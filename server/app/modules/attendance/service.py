import time
from sqlalchemy import select
from ...core.security import fail
from ...models import AttendanceSessions, AttendanceRecords, Students
from ...services import access
from ...services.activity import iso


def session(db, user, sid, manage=False):
    row = db.get(AttendanceSessions, sid)
    if not row:
        fail(404, "NOT_FOUND", "Không tìm thấy phiên điểm danh")
    access.course(db, user, row.course_id, manage)
    return row


def payload(row):
    return dict(
        id=row.id,
        course_id=row.course_id,
        event_id=row.event_id,
        title=row.title,
        status=(
            "closed"
            if row.status == "closed" or row.expires_at <= time.time()
            else "open"
        ),
        created_at=iso(row.starts_at),
        expires_at=iso(row.expires_at),
    )


def record(db, row):
    student = db.get(Students, row.student_id)
    return dict(
        id=row.id,
        session_id=row.session_id,
        student_id=student.student_code,
        full_name=student.full_name,
        status=row.status,
        checked_in_at=iso(row.checked_in_at),
    )
