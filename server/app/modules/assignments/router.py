from .service import assignment_view, submission_view
import time
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, Request, UploadFile, File, Header
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select, func
from ...core.database import get_db
from ...core.security import learning_user, fail
from ...models import Assignments, AssignmentSubmissions, Students, AuditLogs
from ...services import access, idempotency
from ...services.files import read_upload, save, resolve
from ...schemas.common import Pagination
from .schemas import AssignmentInput, AssignmentPatch, GradeInput

router = APIRouter(prefix="/api", tags=["assignments"])


@router.get("/courses/{course_id}/assignments")
def listing(
    course_id: int,
    db=Depends(get_db),
    user=Depends(learning_user),
    p=Depends(Pagination),
):
    access.course(db, user, course_id)
    q = select(Assignments).where(Assignments.course_id == course_id)
    return p.response(
        [
            assignment_view(r)
            for r in db.scalars(
                q.order_by(Assignments.id).offset(p.offset).limit(p.page_size)
            )
        ],
        db.scalar(select(func.count()).select_from(q.subquery())),
    )


@router.post("/courses/{course_id}/assignments", status_code=201)
def create(
    course_id: int,
    body: AssignmentInput,
    db=Depends(get_db),
    user=Depends(learning_user),
):
    access.course(db, user, course_id, True)
    t = access.teacher(db, user)
    r = Assignments(
        course_id=course_id,
        created_by=t.id,
        title=body.title,
        description=body.description,
        due_at=body.due_at.timestamp(),
        allow_resubmit=body.allow_resubmit,
    )
    db.add(r)
    access.course(db, user, course_id, True).grades_published = False
    db.commit()
    return assignment_view(r)


@router.get("/assignments/{assignment_id}")
def detail(assignment_id: int, db=Depends(get_db), user=Depends(learning_user)):
    r = db.get(Assignments, assignment_id)
    if not r:
        fail(404, "NOT_FOUND", "Không tìm thấy bài tập")
    access.course(db, user, r.course_id)
    return assignment_view(r)


@router.patch("/assignments/{assignment_id}")
def patch(
    assignment_id: int,
    body: AssignmentPatch,
    db=Depends(get_db),
    user=Depends(learning_user),
):
    r = db.get(Assignments, assignment_id)
    if not r:
        fail(404, "NOT_FOUND", "Không tìm thấy bài tập")
    access.course(db, user, r.course_id, True)
    from pydantic import ValidationError

    try:
        merged = AssignmentInput.model_validate(
            {**assignment_view(r), **body.model_dump(exclude_unset=True)}
        )
    except ValidationError:
        fail(422, "VALIDATION_ERROR", "Thông tin bài tập không hợp lệ")
    r.title = merged.title
    r.description = merged.description
    r.due_at = merged.due_at.timestamp()
    r.allow_resubmit = merged.allow_resubmit
    access.course(db, user, r.course_id, True).grades_published = False
    db.commit()
    return assignment_view(r)


@router.post("/assignments/{assignment_id}/submissions")
async def submit(
    assignment_id: int,
    request: Request,
    file: UploadFile = File(...),
    key: str | None = Header(None, alias="Idempotency-Key"),
    db=Depends(get_db),
    user=Depends(learning_user),
):
    name, data = await read_upload(
        file, 20 * 1024 * 1024, {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".txt", ".zip", ".c", ".cpp", ".java"}
    )
    paths = []
    context = {}

    def authorize():
        r = db.get(Assignments, assignment_id)
        if not r:
            fail(404, "NOT_FOUND", "Không tìm thấy bài tập")
        c = access.course(db, user, r.course_id)
        s = access.student(db, user)
        context.update(assignment=r, course=c, student=s)

    def operation():
        r = context["assignment"]
        s = context["student"]
        c = context["course"]
        accepted_at = time.time()
        if accepted_at >= r.due_at:
            fail(409, "DEADLINE_PASSED", "Đã hết hạn nộp")
        last = (
            db.scalar(
                select(func.max(AssignmentSubmissions.attempt_no)).where(
                    AssignmentSubmissions.assignment_id == r.id,
                    AssignmentSubmissions.student_id == s.id,
                )
            )
            or 0
        )
        if last and not r.allow_resubmit:
            fail(409, "RESUBMIT_DISABLED", "Không cho nộp lại")
        path = save(request.app.state.storage_root, "submissions", data)
        paths.append(path)
        row = AssignmentSubmissions(
            assignment_id=r.id,
            student_id=s.id,
            attempt_no=last + 1,
            storage_path=path,
            original_filename=name,
            size_bytes=len(data),
            received_at=accepted_at,
        )
        db.add(row)
        db.flush()
        c.grades_published = False
        return submission_view(db, row, user, c)

    try:
        result, status = idempotency.run(
            db,
            user,
            "POST",
            request.url.path,
            key,
            idempotency.request_hash({"filename": name}, data),
            operation,
            status=201,
            authorize=authorize,
        )
        return JSONResponse(result, status_code=status)
    except BaseException:
        for path in paths:
            (Path(request.app.state.storage_root) / path).unlink(missing_ok=True)
        raise


@router.get("/assignments/{assignment_id}/submissions")
def submissions(
    assignment_id: int,
    db=Depends(get_db),
    user=Depends(learning_user),
    p=Depends(Pagination),
):
    r = db.get(Assignments, assignment_id)
    if not r:
        fail(404, "NOT_FOUND", "Không tìm thấy bài tập")
    c = access.course(db, user, r.course_id)
    q = select(AssignmentSubmissions).where(AssignmentSubmissions.assignment_id == r.id)
    if user.role == "student":
        q = q.where(AssignmentSubmissions.student_id == access.student(db, user).id)
    return p.response(
        [
            submission_view(db, s, user, c)
            for s in db.scalars(
                q.order_by(AssignmentSubmissions.received_at.desc())
                .offset(p.offset)
                .limit(p.page_size)
            )
        ],
        db.scalar(select(func.count()).select_from(q.subquery())),
    )


@router.get("/assignment-submissions/{submission_id}/download")
def download(
    submission_id: int,
    request: Request,
    db=Depends(get_db),
    user=Depends(learning_user),
):
    r = db.get(AssignmentSubmissions, submission_id)
    if not r:
        fail(404, "NOT_FOUND", "Không tìm thấy bài nộp")
    a = db.get(Assignments, r.assignment_id)
    access.course(db, user, a.course_id)
    if user.role == "student" and access.student(db, user).id != r.student_id:
        fail(403, "FORBIDDEN", "Không được đọc bài người khác")
    return FileResponse(
        resolve(request.app.state.storage_root, r.storage_path),
        filename=r.original_filename,
        media_type="application/octet-stream",
    )


@router.patch("/assignment-submissions/{submission_id}/grade")
def grade(
    submission_id: int,
    body: GradeInput,
    db=Depends(get_db),
    user=Depends(learning_user),
):
    r = db.get(AssignmentSubmissions, submission_id)
    if not r:
        fail(404, "NOT_FOUND", "Không tìm thấy bài nộp")
    a = db.get(Assignments, r.assignment_id)
    c = access.course(db, user, a.course_id, True)
    r.score = body.score
    r.feedback = body.feedback
    c.grades_published = False
    db.add(
        AuditLogs(
            user_id=user.user_id,
            action="grade_assignment",
            entity_type="assignment_submission",
            entity_id=r.id,
            created_at=time.time(),
        )
    )
    db.commit()
    return submission_view(db, r, user, c)


@router.post("/assignments/{aid}/attachment")
async def upload_attachment(aid: int, request: Request, file: UploadFile = File(...), db=Depends(get_db), user=Depends(learning_user)):
    name, data = await read_upload(file, 20 * 1024 * 1024, {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".txt", ".zip"})
    idempotency.write_lock(db)
    assignment = db.get(Assignments, aid)
    if not assignment: fail(404, "NOT_FOUND", "Không tìm thấy bài tập")
    access.course(db, user, assignment.course_id, True)
    old_path = assignment.attachment_path
    path = save(request.app.state.storage_root, "assignment_handouts", data)
    try:
        assignment.attachment_path = path
        assignment.attachment_filename = name
        db.commit()
    except BaseException:
        (Path(request.app.state.storage_root) / path).unlink(missing_ok=True)
        raise
    if old_path:
        try: resolve(request.app.state.storage_root, old_path).unlink(missing_ok=True)
        except OSError: pass
    return assignment_view(assignment)


@router.get("/assignments/{aid}/attachment")
def download_attachment(aid: int, request: Request, db=Depends(get_db), user=Depends(learning_user)):
    assignment = db.get(Assignments, aid)
    if not assignment or not assignment.attachment_path: fail(404, "NOT_FOUND", "Chưa có file đề bài")
    access.course(db, user, assignment.course_id)
    return FileResponse(resolve(request.app.state.storage_root, assignment.attachment_path), filename=assignment.attachment_filename, media_type="application/octet-stream")
