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
    CodeSubmissions,
    ExamSessionEvents,
)
from ...schemas.common import Pagination
from ...services import access, idempotency, files
from ...services.activity import iso, audit, emit
from .schemas import ExamInput, ProblemInput, SessionEventInput
from . import service as svc

from .testcase_files import router as testcase_files_router

router = APIRouter(prefix="/api", tags=["coding-exams"])
router.include_router(testcase_files_router)


@router.get("/my/active-exam")
def active_exam(db=Depends(get_db), user=Depends(learning_user)):
    student=access.student(db,user)
    row=db.execute(select(ExamSessions,CodingExams).join(ExamRegistrations,ExamSessions.registration_id==ExamRegistrations.id)
        .join(CodingExams,ExamRegistrations.exam_id==CodingExams.id).where(
            ExamRegistrations.student_id==student.id,ExamSessions.status=="active",ExamSessions.ends_at>time.time(),
            CodingExams.status!="closed",CodingExams.ends_at>time.time()).order_by(ExamSessions.id).limit(1)).first()
    return {"exam_id":row[1].id,"session_id":row[0].id} if row else None


@router.get("/coding-exams/{eid}/export-csv")
def export_exam(eid: int, db=Depends(get_db), user=Depends(learning_user)):
    import csv,io
    from ...models import CourseEnrollments,Classes
    from ..gradebook.service import single_exam_score,round_score
    from ..gradebook.router import safe_text
    exam=svc.exam(db,user,eid,True)
    output=io.StringIO(newline="")
    writer=csv.writer(output);writer.writerow(["student_id","full_name","class_name","accepted_count","score","status"])
    for student in db.scalars(select(Students).join(CourseEnrollments).where(CourseEnrollments.course_id==exam.course_id,CourseEnrollments.status=="active").order_by(Students.student_code)):
        registration=db.scalar(select(ExamRegistrations).where(ExamRegistrations.exam_id==eid,ExamRegistrations.student_id==student.id))
        session=db.scalar(select(ExamSessions).where(ExamSessions.registration_id==registration.id)) if registration else None
        count=db.scalar(select(func.count(func.distinct(CodeSubmissions.problem_id))).join(Problems,CodeSubmissions.problem_id==Problems.id).where(Problems.exam_id==eid,CodeSubmissions.student_id==student.id,CodeSubmissions.status=="Accepted"))
        cls=db.get(Classes,student.class_id) if student.class_id else None
        score=single_exam_score(db,exam,student.id)
        writer.writerow([safe_text(student.student_code),safe_text(student.full_name),safe_text(cls.class_code if cls else ""),count,round_score(score) if score is not None else "",session.status if session else "not_started"])
    return Response(("\ufeff"+output.getvalue()).encode("utf-8"),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":f'attachment; filename="exam-{eid}.csv"'})


@router.get("/courses/{course_id}/judge-status")
def judge_status(course_id: int, request: Request, db=Depends(get_db), user=Depends(learning_user)):
    access.course(db, user, course_id)
    from judge.health import status
    from ...models import JudgeJobs
    workers = status(request.app.state.storage_root, request.app.state.settings.database_url)
    q = select(func.count(JudgeJobs.id)).join(CodeSubmissions, JudgeJobs.submission_id == CodeSubmissions.id).join(Problems, CodeSubmissions.problem_id == Problems.id).join(CodingExams, Problems.exam_id == CodingExams.id).where(CodingExams.course_id == course_id, JudgeJobs.status.in_(["pending", "running"]))
    return {"ready": workers > 0, "workers": workers, "pending_jobs": db.scalar(q), "server_time": iso(time.time())}


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
            {**svc.exam_payload(r),"can_open":not svc.attempt_closed(db,user,r)}
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
    existing = db.scalar(
        select(CodingExams).where(
            CodingExams.course_id == course_id,
            CodingExams.grade_component == body.grade_component,
        )
    )
    if body.grade_component == "final" and existing:
        label = "giữa kỳ" if body.grade_component == "midterm" else "cuối kỳ"
        fail(409, "EXAM_COMPONENT_EXISTS",
             f'Khóa học đã có đề {label} "{existing.title}". Mỗi khóa chỉ có một đề cuối kỳ; hãy mở đề hiện có hoặc tạo đề giữa kỳ/test.')
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
    return {**svc.exam_payload(row),"can_open":not svc.attempt_closed(db,user,row)}


@router.patch("/coding-exams/{eid}")
def update(eid: int, body: dict, db=Depends(get_db), user=Depends(learning_user)):
    idempotency.write_lock(db)
    row = svc.exam(db, user, eid, True)
    if set(body) - {"title", "starts_at", "ends_at", "score_ladder", "status", "grade_component"}:
        fail(422, "VALIDATION_ERROR", "Trường cập nhật không hợp lệ")
    action = body.pop("status", None)
    if action not in (None, "scheduled", "closed"):
        fail(422, "INVALID_STATUS", "Trạng thái không hợp lệ")
    if body:
        if set(body) - {"grade_component"}:
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
        if merged.grade_component == "final" and db.scalar(select(CodingExams.id).where(
            CodingExams.course_id == row.course_id, CodingExams.grade_component == "final", CodingExams.id != eid)):
            fail(409, "EXAM_COMPONENT_EXISTS", "Khóa học đã có đề cuối kỳ; hãy đổi đề cuối kỳ cũ sang test trước")
        row.grade_component = merged.grade_component
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
    if user.role=="student":svc.ensure_attempt_open(db,user,row)
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
        if old.status!="active" or old.ends_at<=time.time() or e.status=="closed": fail(409,"ATTEMPT_CLOSED","Bạn đã kết thúc bài thi; không thể mở lại")
        return svc.session_payload(db, old, reg, e, s, request.app.state.hub)
    if active_exam(db,user):
        fail(409,"ACTIVE_EXAM","Bạn cần kết thúc phiên thi hiện tại trước khi vào đề khác")
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
        started_ip=request.client.host if request.client else None,
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


@router.delete("/problems/{pid}", status_code=204)
def delete_problem(
    pid: int, request: Request, db=Depends(get_db), user=Depends(learning_user)
):
    idempotency.write_lock(db)
    p, e = svc.problem(db, user, pid, True)
    svc.editable(db, e)
    tests = list(db.scalars(select(TestCases).where(TestCases.problem_id == pid)))
    paths = [path for t in tests for path in (t.input_path, t.expected_output_path)]
    for t in tests:
        db.delete(t)
    db.flush()
    db.delete(p)
    audit(db, user.user_id, "delete", "problem", pid)
    db.commit()
    for path in paths:
        try:
            files.resolve(request.app.state.storage_root, path).unlink(missing_ok=True)
        except OSError:
            pass
    return Response(status_code=204)


@router.post("/exam-sessions/{sid}/events", status_code=201)
def record_event(sid: int, body: SessionEventInput, request: Request, db=Depends(get_db), user=Depends(learning_user)):
    idempotency.write_lock(db)
    row, reg, e, student = svc.session(db, user, sid)
    if user.user_id != student.user_id:
        fail(403, "FORBIDDEN", "Chỉ sinh viên của phiên được gửi sự kiện")
    old = db.scalar(select(ExamSessionEvents).where(ExamSessionEvents.session_id == sid, ExamSessionEvents.event_key == body.event_key))
    if old:
        return {"id": old.id}
    if row.status != "active" or row.ends_at <= time.time() or e.status == "closed":
        fail(409, "SESSION_CLOSED", "Phiên thi đã kết thúc")
    if db.scalar(select(func.count(ExamSessionEvents.id)).where(ExamSessionEvents.session_id == sid)) >= 1000:
        fail(429, "EVENT_LIMIT", "Phiên đã có quá nhiều sự kiện")
    event = ExamSessionEvents(session_id=sid, event_key=body.event_key, event_type=body.event_type,
        ip_address=request.client.host if request.client else None, created_at=time.time())
    db.add(event)
    db.flush()
    db.commit()
    return {"id": event.id}


@router.get("/exam-sessions/{sid}/events")
def list_events(sid: int, db=Depends(get_db), user=Depends(learning_user), p=Depends(Pagination)):
    row, reg, e, student = svc.session(db, user, sid)
    access.course(db, user, e.course_id, True)
    query = select(ExamSessionEvents).where(ExamSessionEvents.session_id == sid)
    return p.response([{"id": x.id, "event_type": x.event_type, "ip_address": x.ip_address,
        "created_at": iso(x.created_at)} for x in db.scalars(query.order_by(ExamSessionEvents.id.desc()).offset(p.offset).limit(p.page_size))],
        db.scalar(select(func.count()).select_from(query.subquery())))


@router.delete("/coding-exams/{eid}",status_code=204)
def delete_exam(eid: int,db=Depends(get_db),user=Depends(learning_user)):
    row=svc.exam(db,user,eid,True)
    row.deleted=True
    for session in db.scalars(select(ExamSessions).join(ExamRegistrations).where(ExamRegistrations.exam_id==eid,ExamSessions.status=="active")):
        session.status="finished";session.submitted_at=time.time()
    audit(db,user.user_id,"delete","exam",eid)
    emit(db,"exam.updated",row.course_id,{"exam_id":eid,"deleted":True})
    db.commit()
    return Response(status_code=204)
