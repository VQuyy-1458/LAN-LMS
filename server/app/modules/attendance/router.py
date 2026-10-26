from .service import session, payload, record
from .schemas import Create, Close, Check, Correction
import secrets
import time
from typing import Literal
from fastapi import APIRouter, Depends, Response, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from ...core.database import get_db
from ...core.security import learning_user, digest, fail
from ...models import (
    AttendanceSessions,
    AttendanceRecords,
    Students,
    Courses,
    CalendarEvents,
    CourseEnrollments,
)
from ...schemas.common import Pagination
from ...services import access, idempotency
from ...services.activity import iso, audit, emit

router = APIRouter(prefix="/api", tags=["attendance"])


@router.get("/courses/{course_id}/attendance-sessions")
def listing(
    course_id: int,
    db=Depends(get_db),
    user=Depends(learning_user),
    p=Depends(Pagination),
):
    access.course(db, user, course_id)
    q = select(AttendanceSessions).where(AttendanceSessions.course_id == course_id)
    items = []
    for row in db.scalars(
        q.order_by(AttendanceSessions.id.desc()).offset(p.offset).limit(p.page_size)
    ):
        item = payload(row)
        if user.role == "student":
            s = access.student(db, user)
            r = db.scalar(
                select(AttendanceRecords).where(
                    AttendanceRecords.session_id == row.id,
                    AttendanceRecords.student_id == s.id,
                )
            )
            item["my_status"] = r.status if r else None
        items.append(item)
    return p.response(items, db.scalar(select(func.count()).select_from(q.subquery())))


@router.post("/courses/{course_id}/attendance-sessions", status_code=201)
def create(
    course_id: int,
    body: Create,
    request: Request,
    db=Depends(get_db),
    user=Depends(learning_user),
):
    access.course(db, user, course_id, True)
    t = access.teacher(db, user)
    if body.event_id is not None:
        event = db.get(CalendarEvents, body.event_id)
        if not event or event.course_id != course_id or event.event_type != "lesson":
            fail(422, "INVALID_LESSON", "Lịch học không thuộc khóa học này")
        body.title = event.title
    token = secrets.token_urlsafe(24)
    now = time.time()
    row = AttendanceSessions(
        course_id=course_id,
        created_by=t.id,
        title=body.title,
        token_hash=digest(token),
        starts_at=now,
        expires_at=now + body.duration_seconds,
        status="open",
    )
    db.add(row)
    db.flush()
    audit(db, user.user_id, "create", "attendance", row.id)
    db.get(Courses, course_id).grades_published = False
    db.commit()
    import io
    import qrcode
    import qrcode.image.svg

    path = f"/student/courses?attendance={row.id}&token={token}"
    qr = qrcode.make(
        (request.app.state.settings.public_origin or request.headers["origin"]) + path, image_factory=qrcode.image.svg.SvgPathImage
    )
    stream = io.BytesIO()
    qr.save(stream)
    return {
        **payload(row),
        "token": token,
        "check_in_path": path,
        "qr_svg": stream.getvalue().decode("utf-8"),
    }


@router.get("/attendance-sessions/{sid}")
def detail(sid: int, db=Depends(get_db), user=Depends(learning_user)):
    return payload(session(db, user, sid))


@router.patch("/attendance-sessions/{sid}")
def close(sid: int, body: Close, db=Depends(get_db), user=Depends(learning_user)):
    row = session(db, user, sid, True)
    row.status = "closed"
    db.get(Courses, row.course_id).grades_published = False
    audit(db, user.user_id, "close", "attendance", row.id)
    db.commit()
    return payload(row)


@router.post("/attendance-sessions/{sid}/check-in")
def check_in(
    sid: int,
    body: Check,
    response: Response,
    db=Depends(get_db),
    user=Depends(learning_user),
):
    idempotency.write_lock(db)
    row = session(db, user, sid)
    s = access.student(db, user)
    if not secrets.compare_digest(row.token_hash, digest(body.token)):
        fail(403, "INVALID_TOKEN", "Mã điểm danh không hợp lệ")
    old = db.scalar(
        select(AttendanceRecords).where(
            AttendanceRecords.session_id == sid, AttendanceRecords.student_id == s.id
        )
    )
    if old:
        return record(db, old)
    if row.status != "open" or row.expires_at <= time.time():
        fail(409, "ATTENDANCE_CLOSED", "Phiên điểm danh đã đóng hoặc hết hạn")
    r = AttendanceRecords(
        session_id=sid, student_id=s.id, checked_in_at=time.time(), status="present"
    )
    db.add(r)
    db.get(Courses, row.course_id).grades_published = False
    db.flush()
    response.status_code = 201
    emit(db, "attendance.updated", row.course_id, {"session_id": sid, "student_id": s.student_code, "status": "present"}, s.user_id)
    db.commit()
    return record(db, r)


@router.get("/attendance-sessions/{sid}/records")
def records(
    sid: int, db=Depends(get_db), user=Depends(learning_user), p=Depends(Pagination)
):
    session(db, user, sid, True)
    q = select(AttendanceRecords).where(AttendanceRecords.session_id == sid)
    return p.response(
        [
            record(db, r)
            for r in db.scalars(
                q.order_by(AttendanceRecords.id).offset(p.offset).limit(p.page_size)
            )
        ],
        db.scalar(select(func.count()).select_from(q.subquery())),
    )


@router.get("/attendance-sessions/{sid}/roster")
def roster(
    sid: int, db=Depends(get_db), user=Depends(learning_user), p=Depends(Pagination)
):
    row = session(db, user, sid, True)
    q = (
        select(Students, AttendanceRecords)
        .join(CourseEnrollments, CourseEnrollments.student_id == Students.id)
        .outerjoin(
            AttendanceRecords,
            (AttendanceRecords.student_id == Students.id)
            & (AttendanceRecords.session_id == sid),
        )
        .where(
            CourseEnrollments.course_id == row.course_id,
            CourseEnrollments.status == "active",
        )
    )
    items = []
    for student, entry in db.execute(
        q.order_by(Students.student_code).offset(p.offset).limit(p.page_size)
    ):
        items.append(
            dict(
                id=entry.id if entry else None,
                student_id=student.student_code,
                full_name=student.full_name,
                status=entry.status if entry else "unmarked",
                checked_in_at=iso(entry.checked_in_at) if entry else None,
            )
        )
    return p.response(items, db.scalar(select(func.count()).select_from(q.subquery())))


@router.patch("/attendance-sessions/{sid}/records")
def correct(
    sid: int, body: Correction, db=Depends(get_db), user=Depends(learning_user)
):
    idempotency.write_lock(db)
    row = session(db, user, sid, True)
    from ...models import CourseEnrollments, Courses

    s = db.scalar(
        select(Students)
        .join(CourseEnrollments)
        .where(
            Students.student_code == body.student_id,
            CourseEnrollments.course_id == row.course_id,
            CourseEnrollments.status == "active",
        )
    )
    if not s:
        fail(404, "NOT_FOUND", "Sinh viên không thuộc khóa học")
    r = db.scalar(
        select(AttendanceRecords).where(
            AttendanceRecords.session_id == sid, AttendanceRecords.student_id == s.id
        )
    )
    before = r.status if r else None
    if not r:
        r = AttendanceRecords(
            session_id=sid,
            student_id=s.id,
            checked_in_at=time.time(),
            status=body.status,
        )
        db.add(r)
    r.status = body.status
    emit(db, "attendance.updated", row.course_id, {"session_id": sid, "student_id": s.student_code, "status": body.status}, s.user_id)
    db.get(Courses, row.course_id).grades_published = False
    audit(
        db,
        user.user_id,
        "correct",
        "attendance",
        sid,
        {
            "student_id": body.student_id,
            "before": before,
            "after": body.status,
            "reason": body.reason,
        },
    )
    db.flush()
    db.commit()
    return record(db, r)
