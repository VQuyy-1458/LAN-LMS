from .service import payload
from .schemas import SubmissionInput
import json
import time
from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, func
from ...core.database import get_db
from ...core.security import learning_user, fail
from ...models import (
    CodeSubmissions,
    JudgeResults,
    JudgeJobs,
    Problems,
    Students,
    Courses,
)
from ...schemas.common import Pagination
from ...services import access, idempotency, files
from ...services.activity import iso, emit
from ..coding_exams import service as exams

router = APIRouter(prefix="/api", tags=["submissions"])


@router.post("/problems/{pid}/submissions", status_code=202)
def submit(
    pid: int,
    body: SubmissionInput,
    request: Request,
    key: str | None = Header(None, alias="Idempotency-Key"),
    db=Depends(get_db),
    user=Depends(learning_user),
):
    content = body.source_code.encode("utf-8")
    if len(content) > 256 * 1024 or "\x00" in body.source_code:
        fail(413, "INVALID_SOURCE", "Source tối đa 256 KiB UTF-8, không chứa NUL")
    paths = []

    def authorize():
        p, e = exams.problem(db, user, pid)
        s = access.student(db, user)
        row, reg, exam, owner = exams.session(db, user, body.exam_session_id)
        if reg.exam_id != p.exam_id or owner.id != s.id:
            fail(403, "FORBIDDEN", "Phiên không thuộc bài thi")

    def operation():
        p, e = exams.problem(db, user, pid)
        s = access.student(db, user)
        row, reg, exam, owner = exams.session(db, user, body.exam_session_id)
        if (
            row.status != "active"
            or time.time() >= row.ends_at
            or exams.state(e) != "open"
        ):
            fail(409, "EXAM_CLOSED", "Phiên thi đã kết thúc")
        if body.language not in json.loads(p.languages_json):
            fail(422, "INVALID_LANGUAGE", "Ngôn ngữ không được phép")
        active = ["Pending", "Compiling", "Running"]
        if (
            db.scalar(
                select(func.count(CodeSubmissions.id)).where(
                    CodeSubmissions.student_id == s.id,
                    CodeSubmissions.status.in_(active),
                )
            )
            >= 10
        ):
            fail(429, "QUEUE_LIMIT", "Bạn đang có nhiều bài chờ chấm, vui lòng đợi")
        if (
            db.scalar(
                select(func.count(JudgeJobs.id)).where(
                    JudgeJobs.status.in_(["pending", "running"])
                )
            )
            >= 200
        ):
            fail(503, "QUEUE_FULL", "Hàng đợi đang đầy, hãy gửi lại với cùng key")
        path = files.save(request.app.state.storage_root, "code_submissions", content)
        paths.append(path)
        attempt = (
            db.scalar(
                select(func.max(CodeSubmissions.attempt_no)).where(
                    CodeSubmissions.exam_session_id == row.id,
                    CodeSubmissions.problem_id == pid,
                )
            )
            or 0
        ) + 1
        sub = CodeSubmissions(
            exam_session_id=row.id,
            problem_id=pid,
            student_id=s.id,
            attempt_no=attempt,
            language=body.language,
            source_path=path,
            received_at=time.time(),
            status="Pending",
            version=1,
        )
        db.add(sub)
        db.flush()
        db.add(
            JudgeJobs(
                submission_id=sub.id,
                status="pending",
                attempt_count=0,
                created_at=sub.received_at,
            )
        )
        db.get(Courses, e.course_id).grades_published = False
        emit(
            db,
            "submission.updated",
            e.course_id,
            {"submission_id": sub.id, "status": sub.status, "version": 1},
            s.user_id,
        )
        return payload(db, sub)

    try:
        result, status = idempotency.run(
            db,
            user,
            "POST",
            request.url.path,
            key,
            idempotency.request_hash(body.model_dump()),
            operation,
            202,
            authorize,
        )
        return JSONResponse(result, status_code=status)
    except BaseException:
        db.rollback()
        for path in paths:
            (request.app.state.storage_root / path).unlink(missing_ok=True)
        raise


@router.get("/submissions/{sid}")
def detail(sid: int, request: Request, db=Depends(get_db), user=Depends(learning_user)):
    row = db.get(CodeSubmissions, sid)
    if not row:
        fail(404, "NOT_FOUND", "Không tìm thấy bài nộp")
    p, e = exams.problem(db, user, row.problem_id)
    if user.role != "teacher" and access.student(db, user).id != row.student_id:
        fail(403, "FORBIDDEN", "Không có quyền xem bài nộp")
    return payload(db, row, request.app.state.storage_root, True)


@router.get("/problems/{pid}/submissions")
def listing(
    pid: int, db=Depends(get_db), user=Depends(learning_user), p=Depends(Pagination)
):
    exams.problem(db, user, pid)
    q = select(CodeSubmissions).where(CodeSubmissions.problem_id == pid)
    if user.role != "teacher":
        q = q.where(CodeSubmissions.student_id == access.student(db, user).id)
    return p.response(
        [
            payload(db, r)
            for r in db.scalars(
                q.order_by(
                    CodeSubmissions.received_at.desc(), CodeSubmissions.id.desc()
                )
                .offset(p.offset)
                .limit(p.page_size)
            )
        ],
        db.scalar(select(func.count()).select_from(q.subquery())),
    )
