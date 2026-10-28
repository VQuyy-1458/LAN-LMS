"""Replace the authored networking classroom; preserve accounts and other courses.

Stop API/workers and take a database/storage backup before invoking this command.
The removed course is soft-deleted so its history remains recoverable privately.
"""
import argparse
import json
from pathlib import Path

from sqlalchemy import select, delete

from demo.classroom_content import COURSES
from scripts.seed_classroom import seed
from server.app.core.database import database, User
from server.app.models import Courses, CourseEnrollments, CourseTeachers, Teachers, CalendarEvents


def switch(sessions, storage, teacher_username, output):
    with sessions() as db:
        teacher = db.scalar(select(Teachers).join(User).where(User.username == teacher_username))
        if teacher is None:
            raise ValueError("Teacher does not exist")
        old = db.scalar(select(Courses).where(Courses.course_code == "LTM-D24-01").execution_options(include_deleted=True))
        if old is None:
            raise ValueError("Expected authored course LTM-D24-01 was not found; no course changed")
        if not db.scalar(select(CourseTeachers.id).where(CourseTeachers.course_id == old.id, CourseTeachers.teacher_id == teacher.id)):
            raise ValueError("Networking course belongs to a different teacher")
        old_id = old.id
        ids = list(db.scalars(select(CourseEnrollments.student_id).where(CourseEnrollments.course_id == old.id, CourseEnrollments.status == "active")))
        if len(ids) != 20:
            raise ValueError("Expected 20 enrolled students; review roster before continuing")
    content = dict(COURSES[0], code="LT-D24-01")
    result = seed(sessions, storage, teacher_username, output, contents=[content], student_ids=ids)
    with sessions.begin() as db:
        old = db.scalar(select(Courses).where(Courses.id == old_id).execution_options(include_deleted=True))
        old.status = "deleted"
        new_id = result["courses"][0]["id"]
        # Exams/deadlines come from their source objects in the calendar feed.
        db.execute(delete(CalendarEvents).where(CalendarEvents.course_id == new_id, CalendarEvents.event_type.in_(["exam", "deadline"])))
    result.update(removed_course_id=old_id, preserved_student_accounts=len(ids))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--storage", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--teacher", default="GV001")
    args = parser.parse_args()
    if not args.database.is_file():
        parser.error("Database must already exist")
    engine, sessions = database("sqlite:///" + args.database.resolve().as_posix())
    try:
        print(json.dumps(switch(sessions, args.storage, args.teacher, args.output), ensure_ascii=False, indent=2))
    finally:
        engine.dispose()
