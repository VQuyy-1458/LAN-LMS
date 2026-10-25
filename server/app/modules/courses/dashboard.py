import time
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from ...core.database import get_db
from ...core.security import learning_user
from ...models import *
from ...services import access
from ...services.activity import iso
from .router import serialize
from ..coding_exams.service import exam_payload

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
def dashboard(db=Depends(get_db), user=Depends(learning_user)):
    now = time.time()
    if user.role == "teacher":
        profile = access.teacher(db, user)
        query = (
            select(Courses)
            .join(CourseTeachers)
            .where(CourseTeachers.teacher_id == profile.id)
        )
    else:
        profile = access.student(db, user)
        query = (
            select(Courses)
            .join(CourseEnrollments)
            .where(
                CourseEnrollments.student_id == profile.id,
                CourseEnrollments.status == "active",
            )
        )
    courses = list(db.scalars(query.order_by(Courses.id)))
    ids = [r.id for r in courses]
    events = [
        dict(
            id=r.id,
            course_id=r.course_id,
            title=r.title,
            description=r.description,
            event_type=r.event_type,
            starts_at=iso(r.starts_at),
            ends_at=iso(r.ends_at),
        )
        for r in db.scalars(
            select(CalendarEvents)
            .where(
                CalendarEvents.course_id.in_(ids),
                CalendarEvents.ends_at >= now - 31 * 86400,
            )
            .order_by(CalendarEvents.starts_at)
            .limit(500)
        )
    ]
    exams = [
        exam_payload(r)
        for r in db.scalars(
            select(CodingExams)
            .where(CodingExams.course_id.in_(ids), CodingExams.status != "draft")
            .order_by(CodingExams.starts_at)
            .limit(100)
        )
    ]
    assignments = [
        dict(id=r.id, course_id=r.course_id, title=r.title, due_at=iso(r.due_at))
        for r in db.scalars(
            select(Assignments)
            .where(Assignments.course_id.in_(ids))
            .order_by(Assignments.due_at)
            .limit(500)
        )
    ]
    if user.role == "student":
        submitted = set(
            db.scalars(
                select(AssignmentSubmissions.assignment_id)
                .join(Assignments)
                .where(
                    Assignments.course_id.in_(ids),
                    AssignmentSubmissions.student_id == profile.id,
                )
            )
        )
        for a in assignments:
            a["submitted"] = a["id"] in submitted
        stats = {
            "courses": len(courses),
            "submitted": len(submitted),
            "upcoming_exams": sum(e["status"] in ("upcoming", "open") for e in exams),
        }
    else:
        stats = {
            "courses": len(courses),
            "students": db.scalar(
                select(func.count(func.distinct(CourseEnrollments.student_id))).where(
                    CourseEnrollments.course_id.in_(ids),
                    CourseEnrollments.status == "active",
                )
            ),
            "awaiting_grades": db.scalar(
                select(func.count(AssignmentSubmissions.id))
                .join(Assignments)
                .where(
                    Assignments.course_id.in_(ids),
                    AssignmentSubmissions.score.is_(None),
                )
            ),
        }
    return dict(
        full_name=profile.full_name,
        courses=[serialize(db, r) for r in courses],
        stats=stats,
        events=events,
        exams=exams,
        assignments=assignments,
        server_time=iso(now),
    )
