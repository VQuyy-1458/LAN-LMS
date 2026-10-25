import json
import time
from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, Response
from pydantic import ValidationError
from sqlalchemy import select, func
from ...core.database import get_db
from ...core.security import learning_user, fail
from ...models import (
    CodingExams,
    Problems,
    TestCases,
    ExamSessions,
    ExamRegistrations,
    Courses,
    Students,
)
from ...schemas.common import Pagination
from ...services import access, idempotency, files
from ...services.activity import iso, audit, emit
from .schemas import ExamInput, ProblemInput
from . import service as svc

router = APIRouter(prefix="/api", tags=["coding-exams"])


@router.get("/courses/{course_id}/coding-exams")
def listing(
    course_id: int,
    db=Depends(get_db),
    user=Depends(learning_user),
    p=Depends(Pagination),
):
    access.course(db, user, course_id)
    q = select(CodingExams).where(CodingExams.course_id == course_id)
    if user.role != "teacher":
        q = q.where(CodingExams.status != "draft")
    return p.response(
        [
            svc.exam_payload(r)
            for r in db.scalars(
                q.order_by(CodingExams.id).offset(p.offset).limit(p.page_size)
            )
        ],
        db.scalar(select(func.count()).select_from(q.subquery())),
    )


@router.post("/courses/{course_id}/coding-exams", status_code=201)
def create(
    course_id: int, body: ExamInput, db=Depends(get_db), user=Depends(learning_user)
):
    idempotency.write_lock(db)
    access.course(db, user, course_id, True)
    t = access.teacher(db, user)
    if body.starts_at.timestamp() <= time.time():
        fail(422, "INVALID_DATES", "Tạo kỳ thi có giờ bắt đầu trong tương lai")
    row = CodingExams(
        course_id=course_id,
        created_by=t.id,
        title=body.title,
        starts_at=body.starts_at.timestamp(),
        ends_at=body.ends_at.timestamp(),
        grade_component=body.grade_component,
        status="draft",
        results_published=False,
        score_ladder_json=json.dumps(body.score_ladder),
    )
    db.add(row)
    db.flush()
    db.get(Courses, course_id).grades_published = False
    audit(db, user.user_id, "create", "exam", row.id)
    db.commit()
    return svc.exam_payload(row)


@router.get("/coding-exams/{eid}")
def detail(eid: int, db=Depends(get_db), user=Depends(learning_user)):
    row = svc.exam(db, user, eid)
    if row.status == "draft" and user.role != "teacher":
        fail(403, "EXAM_NOT_OPEN", "Đề đang soạn")
    return svc.exam_payload(row)


@router.patch("/coding-exams/{eid}")
def update(eid: int, body: dict, db=Depends(get_db), user=Depends(learning_user)):
    idempotency.write_lock(db)
    row = svc.exam(db, user, eid, True)
    if set(body) - {"title", "starts_at", "ends_at", "score_ladder", "status"}:
        fail(422, "VALIDATION_ERROR", "Trường cập nhật không hợp lệ")
    action = body.pop("status", None)
    if action not in (None, "scheduled", "closed"):
        fail(422, "INVALID_STATUS", "Trạng thái không hợp lệ")
    if body:
        svc.editable(db, row)
        try:
            merged = ExamInput.model_validate(
                {
                    "title": row.title,
                    "starts_at": iso(row.starts_at),
                    "ends_at": iso(row.ends_at),
                    "grade_component": row.grade_component,
                    "score_ladder": json.loads(row.score_ladder_json),
                    **body,
                }
            )
        except ValidationError:
            fail(422, "VALIDATION_ERROR", "Thông tin kỳ thi không hợp lệ")
        row.title = merged.title
        row.starts_at = merged.starts_at.timestamp()
        row.ends_at = merged.ends_at.timestamp()
        row.score_ladder_json = json.dumps(merged.score_ladder)
    if action == "scheduled":
        svc.editable(db, row)
        svc.ready(db, row)
        row.status = "scheduled"
    if action == "closed":
        row.status = "closed"
    db.get(Courses, row.course_id).grades_published = False
    audit(db, user.user_id, "update", "exam", eid, {"status": action})
    emit(
        db,
        "exam.updated",
        row.course_id,
        {"exam_id": eid, "status": svc.state(row), "ends_at": iso(row.ends_at)},
    )
    db.commit()
    return svc.exam_payload(row)


@router.get("/coding-exams/{eid}/problems")
def problems(
    eid: int, db=Depends(get_db), user=Depends(learning_user), p=Depends(Pagination)
):
    row = svc.exam(db, user, eid)
    if user.role != "teacher" and (
        row.status == "draft" or time.time() < row.starts_at
    ):
        fail(403, "EXAM_NOT_OPEN", "Chưa đến giờ xem đề")
    q = select(Problems).where(Problems.exam_id == eid)
    return p.response(
        [
            svc.problem_payload(r)
            for r in db.scalars(
                q.order_by(Problems.id).offset(p.offset).limit(p.page_size)
            )
        ],
        db.scalar(select(func.count()).select_from(q.subquery())),
    )


def assign_problem(row, body):
    for k, v in body.model_dump().items():
        setattr(
            row,
            "languages_json" if k == "languages" else k,
            json.dumps(v) if k == "languages" else v,
        )


@router.post("/coding-exams/{eid}/problems", status_code=201)
def create_problem(
    eid: int, body: ProblemInput, db=Depends(get_db), user=Depends(learning_user)
):
    idempotency.write_lock(db)
    e = svc.exam(db, user, eid, True)
    svc.editable(db, e)
    if db.scalar(select(func.count(Problems.id)).where(Problems.exam_id == eid)) >= 20:
        fail(409, "TOO_MANY_PROBLEMS", "Tối đa 20 bài mỗi đề")
    r = Problems(exam_id=eid)
    assign_problem(r, body)
    db.add(r)
    db.flush()
    audit(db, user.user_id, "create", "problem", r.id)
    db.commit()
    return svc.problem_payload(r)


@router.patch("/problems/{pid}")
def update_problem(
    pid: int, body: dict, db=Depends(get_db), user=Depends(learning_user)
):
    idempotency.write_lock(db)
    r, e = svc.problem(db, user, pid, True)
    svc.editable(db, e)
    original = svc.problem_payload(r)
    original.pop("id")
    original.pop("exam_id")
    try:
        merged = ProblemInput.model_validate({**original, **body})
    except ValidationError:
        fail(422, "VALIDATION_ERROR", "Cấu hình bài không hợp lệ")
    assign_problem(r, merged)
    audit(db, user.user_id, "update", "problem", pid)
    db.commit()
    return svc.problem_payload(r)


def test_payload(r):
    return dict(
        id=r.id,
        problem_id=r.problem_id,
        points=r.weight,
        is_hidden=not r.is_sample,
        ordinal=r.sort_order,
    )


@router.post("/problems/{pid}/test-cases", status_code=201)
async def add_test(
    pid: int,
    request: Request,
    input_file: UploadFile = File(...),
    expected_output_file: UploadFile = File(...),
    points: float = Form(..., ge=0, le=10000),
    is_hidden: bool = Form(True),
    ordinal: int = Form(0, ge=0),
    db=Depends(get_db),
    user=Depends(learning_user),
):
    import math

    if not math.isfinite(points):
        fail(422, "INVALID_POINTS", "Điểm test không hợp lệ")
    _, inp = await files.read_upload(input_file, 1024 * 1024, {".txt", ".in", ".out"})
    _, out = await files.read_upload(
        expected_output_file, 1024 * 1024, {".txt", ".in", ".out"}
    )
    idempotency.write_lock(db)
    r, e = svc.problem(db, user, pid, True)
    svc.editable(db, e)
    if (
        db.scalar(select(func.count(TestCases.id)).where(TestCases.problem_id == pid))
        >= 100
    ):
        fail(409, "TOO_MANY_TESTS", "Tối đa 100 test")
    paths = []
    try:
        paths.append(files.save(request.app.state.storage_root, "test_cases", inp))
        paths.append(files.save(request.app.state.storage_root, "test_cases", out))
        t = TestCases(
            problem_id=pid,
            input_path=paths[0],
            expected_output_path=paths[1],
            weight=points,
            sort_order=ordinal,
            is_sample=not is_hidden,
        )
        db.add(t)
        db.flush()
        audit(db, user.user_id, "create", "test-case", t.id)
        db.commit()
        return test_payload(t)
    except BaseException:
        db.rollback()
        for path in paths:
            (request.app.state.storage_root / path).unlink(missing_ok=True)
        raise


@router.get("/problems/{pid}/test-cases")
def tests(
    pid: int, db=Depends(get_db), user=Depends(learning_user), p=Depends(Pagination)
):
    svc.problem(db, user, pid, True)
    q = select(TestCases).where(TestCases.problem_id == pid)
    return p.response(
        [
            test_payload(t)
            for t in db.scalars(
                q.order_by(TestCases.sort_order, TestCases.id)
                .offset(p.offset)
                .limit(p.page_size)
            )
        ],
        db.scalar(select(func.count()).select_from(q.subquery())),
    )


@router.delete("/test-cases/{tid}", status_code=204)
def remove_test(
    tid: int, request: Request, db=Depends(get_db), user=Depends(learning_user)
):
    idempotency.write_lock(db)
    r = db.get(TestCases, tid)
    if not r:
        fail(404, "NOT_FOUND", "Không tìm thấy test")
    _, e = svc.problem(db, user, r.problem_id, True)
    svc.editable(db, e)
    paths = [r.input_path, r.expected_output_path]
    db.delete(r)
    audit(db, user.user_id, "delete", "test-case", tid)
    db.commit()
    for path in paths:
        try:
            files.resolve(request.app.state.storage_root, path).unlink(missing_ok=True)
        except Exception:
            pass
    return Response(status_code=204)


@router.post("/coding-exams/{eid}/sessions/start")
def start(eid: int, request: Request, db=Depends(get_db), user=Depends(learning_user)):
    idempotency.write_lock(db)
    e = svc.exam(db, user, eid)
    s = access.student(db, user)
    reg = db.scalar(
        select(ExamRegistrations).where(
            ExamRegistrations.exam_id == eid, ExamRegistrations.student_id == s.id
        )
    )
    old = (
        db.scalar(select(ExamSessions).where(ExamSessions.registration_id == reg.id))
        if reg
        else None
    )
    if old:
        return svc.session_payload(db, old, reg, e, s, request.app.state.hub)
    if svc.state(e) != "open":
        fail(409, "EXAM_NOT_OPEN", "Kỳ thi chưa mở hoặc đã kết thúc")
    svc.ready(db, e)
    now = time.time()
    if not reg:
        reg = ExamRegistrations(
            exam_id=eid, student_id=s.id, registered_at=now, status="active"
        )
        db.add(reg)
        db.flush()
    if reg.status != "active":
        fail(403, "FORBIDDEN", "Đăng ký thi không hoạt động")
    row = ExamSessions(
        registration_id=reg.id,
        started_at=now,
        ends_at=e.ends_at,
        last_seen_at=now,
        status="active",
    )
    db.add(row)
    db.flush()
    emit(
        db,
        "session.updated",
        e.course_id,
        {"exam_session_id": row.id, "status": "active"},
        s.user_id,
    )
    db.commit()
    return svc.session_payload(db, row, reg, e, s, request.app.state.hub)


@router.get("/exam-sessions/{sid}")
def get_session(
    sid: int, request: Request, db=Depends(get_db), user=Depends(learning_user)
):
    row, reg, e, s = svc.session(db, user, sid)
    return svc.session_payload(db, row, reg, e, s, request.app.state.hub)


@router.post("/exam-sessions/{sid}/finish")
def finish(sid: int, request: Request, db=Depends(get_db), user=Depends(learning_user)):
    idempotency.write_lock(db)
    row, reg, e, s = svc.session(db, user, sid)
    if user.user_id != s.user_id:
        fail(403, "FORBIDDEN", "Chỉ chủ phiên được nộp bài")
    if row.status == "active":
        row.status = "expired" if row.ends_at <= time.time() else "finished"
        row.submitted_at = time.time()
        emit(
            db,
            "session.updated",
            e.course_id,
            {"exam_session_id": sid, "status": row.status},
            s.user_id,
        )
        audit(db, user.user_id, "finish", "exam-session", sid)
        db.commit()
    return svc.session_payload(db, row, reg, e, s, request.app.state.hub)


@router.get("/coding-exams/{eid}/sessions")
def sessions(
    eid: int,
    request: Request,
    db=Depends(get_db),
    user=Depends(learning_user),
    p=Depends(Pagination),
):
    e = svc.exam(db, user, eid, True)
    q = (
        select(ExamSessions, ExamRegistrations, Students)
        .join(ExamRegistrations, ExamSessions.registration_id == ExamRegistrations.id)
        .join(Students, ExamRegistrations.student_id == Students.id)
        .where(ExamRegistrations.exam_id == eid)
    )
    return p.response(
        [
            svc.session_payload(db, r, reg, e, s, request.app.state.hub)
            for r, reg, s in db.execute(
                q.order_by(ExamSessions.id).offset(p.offset).limit(p.page_size)
            )
        ],
        db.scalar(select(func.count()).select_from(q.subquery())),
    )


@router.get("/coding-exams/{eid}/my-session")
def my_session(
    eid: int, request: Request, db=Depends(get_db), user=Depends(learning_user)
):
    e = svc.exam(db, user, eid)
    s = access.student(db, user)
    reg = db.scalar(
        select(ExamRegistrations).where(
            ExamRegistrations.exam_id == eid, ExamRegistrations.student_id == s.id
        )
    )
    row = (
        db.scalar(select(ExamSessions).where(ExamSessions.registration_id == reg.id))
        if reg
        else None
    )
    return (
        svc.session_payload(db, row, reg, e, s, request.app.state.hub) if row else None
    )
