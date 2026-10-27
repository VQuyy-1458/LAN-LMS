from datetime import datetime, timezone
from ...models import Students


def assignment_view(r):
    return dict(
        id=r.id,
        course_id=r.course_id,
        title=r.title,
        description=r.description,
        due_at=datetime.fromtimestamp(r.due_at, timezone.utc).isoformat(),
        allow_resubmit=r.allow_resubmit,
        attachment_filename=r.attachment_filename,
    )


def submission_view(db, r, user, course):
    s = db.get(Students, r.student_id)
    visible = user.role == "teacher" or course.grades_published
    return dict(
        id=r.id,
        assignment_id=r.assignment_id,
        student_id=s.student_code,
        original_filename=r.original_filename,
        size_bytes=r.size_bytes,
        received_at=datetime.fromtimestamp(r.received_at, timezone.utc).isoformat(),
        score=r.score if visible else None,
        feedback=r.feedback if visible else None,
    )
