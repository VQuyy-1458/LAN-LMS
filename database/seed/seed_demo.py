"""D02: Idempotent local-only LMS demo data. Run from repository root.

First create a teacher user with: python -m server.app.seed
Then: python -m database.seed.seed_demo --teacher-username <username>
"""

import argparse
import getpass

from sqlalchemy import select

from server.app.core.config import Settings
from server.app.core.database import User, database
from server.app.core.security import hasher
from server.app.models import (
    Classes, Courses, CourseClasses, CourseEnrollments, CourseTeachers,
    Students, Teachers,
)


DEMO_STUDENTS = (
    ("demo_sv01", "DEMO-SV001", "Sinh vien Mau 01", "DEMO-CNTT01"),
    ("demo_sv02", "DEMO-SV002", "Sinh vien Mau 02", "DEMO-CNTT01"),
    ("demo_sv03", "DEMO-SV003", "Sinh vien Mau 03", "DEMO-CNTT02"),
)


def existing_or_add(session, model, filters, values):
    obj = session.scalar(select(model).filter_by(**filters))
    if obj is None:
        obj = model(**values)
        session.add(obj)
        session.flush()
        print(f"Created {model.__tablename__}: {filters}")
    else:
        print(f"Exists  {model.__tablename__}: {filters}")
    return obj

def ask_password(username):
    password = getpass.getpass(f"New password for {username} (8-128 chars): ")
    confirm = getpass.getpass("Confirm password: ")
    if not 8 <= len(password) <= 128 or password != confirm:
        raise ValueError(f"Invalid password or mismatch for {username}")
    return password


def seed(session, teacher_username):
    teacher_user = session.scalar(select(User).where(User.username == teacher_username))
    if teacher_user is None or teacher_user.role != "teacher":
        raise ValueError("Teacher account not found or not a teacher. Run python -m server.app.seed first.")

    teacher = existing_or_add(
        session, Teachers, {"user_id": teacher_user.id},
        {"user_id": teacher_user.id, "teacher_code": "DEMO-GV001", "full_name": "Giang vien Mau", "email": None},
    )
    classes = {}
    for code, name in (("DEMO-CNTT01", "Lop demo CNTT 01"), ("DEMO-CNTT02", "Lop demo CNTT 02")):
        classes[code] = existing_or_add(
            session, Classes, {"class_code": code},
            {"class_code": code, "class_name": name, "academic_year": "2026-2027"},
        )

    course = existing_or_add(
        session, Courses,
        {"course_code": "DEMO-LTM", "semester": "1", "academic_year": "2026-2027"},
        {"course_code": "DEMO-LTM", "course_name": "Lap trinh mang - Demo", "semester": "1",
         "academic_year": "2026-2027", "status": "active", "grades_published": False,
         "final_grade_policy": "highest_published_final_exam"},
    )
    existing_or_add(
        session, CourseTeachers, {"course_id": course.id, "teacher_id": teacher.id},
        {"course_id": course.id, "teacher_id": teacher.id, "role": "primary"},
    )
    for cls in classes.values():
        existing_or_add(
            session, CourseClasses, {"course_id": course.id, "class_id": cls.id},
            {"course_id": course.id, "class_id": cls.id},
        )

    for username, code, name, class_code in DEMO_STUDENTS:
        user = session.scalar(select(User).where(User.username == username))
        if user is None:
            password = ask_password(username)
            user = User(username=username, password_hash=hasher.hash(password), role="student",
                        must_change_password=True, active=True)
            session.add(user)
            session.flush()
            print(f"Created user: {username}")
        elif user.role != "student":
            raise ValueError(f"Username {username} already exists with non-student role")
        student = existing_or_add(
            session, Students, {"student_code": code},
            {"user_id": user.id, "class_id": classes[class_code].id,
             "student_code": code, "full_name": name, "date_of_birth": None, "email": None},
        )
        if student.user_id != user.id:
            raise ValueError(f"Student code {code} is already linked to another user")
        existing_or_add(
            session, CourseEnrollments, {"course_id": course.id, "student_id": student.id},
            {"course_id": course.id, "student_id": student.id, "status": "active"},
        )


def main():
    parser = argparse.ArgumentParser(description="Seed local LAN-LMS demo data")
    parser.add_argument("--teacher-username", required=True, help="Existing teacher username created by TV1 seed")
    args = parser.parse_args()
    engine, sessions = database(Settings().database_url)
    try:
        with sessions.begin() as session:
            seed(session, args.teacher_username)
        print("D02 demo seed completed successfully.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()