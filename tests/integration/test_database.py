"""D03: SQLite constraints and concurrent writes (isolated temporary database)."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from server.app.core.database import Base, User
from server.app.models import Classes, Courses, CourseEnrollments, Students
from server.app.models import (
    AttendanceSessions,
    AttendanceRecords,
    CodingExams,
    ExamRegistrations,
    Teachers,
)

@pytest.fixture
def engine(tmp_path):
    path = tmp_path / "d03.sqlite3"
    engine = create_engine(
        f"sqlite:///{path}", connect_args={"timeout": 5}, poolclass=NullPool
    )

    @event.listens_for(engine, "connect")
    def pragmas(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")
        dbapi_conn.execute("PRAGMA busy_timeout=5000")
        dbapi_conn.execute("PRAGMA journal_mode=WAL")

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def course(code="D03-LTM"):
    return Courses(course_code=code, course_name="Lap trinh mang", semester="1",
                   academic_year="2026-2027", status="active",
                   grades_published=False, final_grade_policy="highest_published_final_exam")

def student(db, username="d03_sv", student_code="D03-SV001"):
    user = User(username=username, password_hash="test-only-not-a-real-password", role="student")
    db.add(user)
    db.flush()
    row = Students(user_id=user.id, student_code=student_code, full_name="Sinh vien demo")
    db.add(row)
    db.flush()
    return row


def test_unique_class_code(engine):
    with Session(engine) as db:
        db.add(Classes(class_code="D03-C01", class_name="Lop A"))
        db.commit()
    with Session(engine) as db:
        db.add(Classes(class_code="D03-C01", class_name="Lop B"))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_unique_course_composite(engine):
    with Session(engine) as db:
        db.add(course())
        db.commit()
    with Session(engine) as db:
        db.add(course())
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

def test_enrollment_unique_and_foreign_key(engine):
    with Session(engine) as db:
        c = course()
        db.add(c)
        db.flush()
        s = student(db)
        course_id, student_id = c.id, s.id
        db.add(CourseEnrollments(course_id=course_id, student_id=student_id, status="active"))
        db.commit()
    with Session(engine) as db:
        db.add(CourseEnrollments(course_id=course_id, student_id=student_id, status="active"))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        db.add(CourseEnrollments(course_id=999999, student_id=student_id, status="active"))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_transaction_rolls_back_entire_unit(engine):
    with Session(engine) as db:
        db.add(Classes(class_code="D03-DUP", class_name="Existing"))
        db.commit()
    with Session(engine) as db:
        db.add(Classes(class_code="D03-NEW", class_name="Should rollback"))
        db.add(Classes(class_code="D03-DUP", class_name="Duplicate"))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Classes)) == 1
        assert db.scalar(select(Classes).where(Classes.class_code == "D03-NEW")) is None

def test_concurrent_insert_same_unique_code(engine):
    """Two separate connections race; exactly one insert may succeed."""
    barrier = Barrier(2)

    def insert_one(n):
        barrier.wait(timeout=10)
        try:
            with Session(engine) as db:
                db.add(Classes(class_code="D03-RACE", class_name=f"Lop {n}"))
                db.commit()
            return "ok"
        except IntegrityError:
            return "duplicate"
        except OperationalError as exc:
            # A busy/locked DB is a controlled error, never a silent success.
            if "locked" in str(exc).lower() or "busy" in str(exc).lower():
                return "busy"
            raise

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(insert_one, range(2)))
    assert results.count("ok") == 1, results
    assert results.count("duplicate") + results.count("busy") == 1, results
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Classes).where(
            Classes.class_code == "D03-RACE")) == 1
# Additional D03 cases. All tests use the isolated SQLite database above.
from threading import Event, Thread

from server.app.models import (
    Teachers, CourseTeachers, CourseClasses,
)


def test_unique_teacher_and_student_codes(engine):
    with Session(engine) as db:
        teacher_user = User(username="d03_teacher_1", password_hash="test-only", role="teacher")
        db.add(teacher_user)
        db.flush()
        db.add(Teachers(user_id=teacher_user.id, teacher_code="D03-GV01", full_name="GV 1"))
        student(db, "d03_student_1", "D03-SV01")
        db.commit()

    with Session(engine) as db:
        second_teacher = User(username="d03_teacher_2", password_hash="test-only", role="teacher")
        db.add(second_teacher)
        db.flush()
        db.add(Teachers(user_id=second_teacher.id, teacher_code="D03-GV01", full_name="GV 2"))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    with Session(engine) as db:
        with pytest.raises(IntegrityError):
            student(db, "d03_student_2", "D03-SV01")
            db.commit()
        db.rollback()

def test_unique_course_teacher_and_class_links(engine):
    with Session(engine) as db:
        teacher_user = User(username="d03_teacher", password_hash="test-only", role="teacher")
        db.add(teacher_user)
        db.flush()
        teacher = Teachers(user_id=teacher_user.id, teacher_code="D03-GV", full_name="GV")
        c = course()
        cls = Classes(class_code="D03-CLASS", class_name="Lop D03")
        db.add_all([teacher, c, cls])
        db.flush()
        course_id, teacher_id, class_id = c.id, teacher.id, cls.id
        db.add_all([
            CourseTeachers(course_id=course_id, teacher_id=teacher_id, role="primary"),
            CourseClasses(course_id=course_id, class_id=class_id),
        ])
        db.commit()

    with Session(engine) as db:
        db.add(CourseTeachers(course_id=course_id, teacher_id=teacher_id, role="primary"))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        db.add(CourseClasses(course_id=course_id, class_id=class_id))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

def test_sqlite_busy_timeout_is_controlled(engine):
    """A second writer times out while another connection holds a write lock."""
    first_has_lock = Event()
    release_first = Event()
    failures = []

    def hold_write_lock():
        try:
            with engine.connect() as conn:
                conn.exec_driver_sql("BEGIN IMMEDIATE")
                conn.exec_driver_sql(
                    "INSERT INTO classes (class_code, class_name) VALUES (?, ?)",
                    ("D03-LOCK-1", "Lock holder"),
                )
                first_has_lock.set()
                if not release_first.wait(timeout=10):
                    raise TimeoutError("Test failed to release writer lock")
                conn.commit()
        except BaseException as exc:
            failures.append(exc)
            first_has_lock.set()

    worker = Thread(target=hold_write_lock, daemon=True)
    worker.start()
    try:
        assert first_has_lock.wait(timeout=10)
        assert not failures, failures
        # Override the test fixture's 5-second timeout only for this connection.
        with engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA busy_timeout=100")
            with pytest.raises(OperationalError, match="locked"):
                conn.exec_driver_sql(
                    "INSERT INTO classes (class_code, class_name) VALUES (?, ?)",
                    ("D03-LOCK-2", "Contending writer"),
                )
            conn.rollback()
    finally:
        release_first.set()
        worker.join(timeout=10)
    assert not worker.is_alive()
    assert not failures, failures
    with Session(engine) as db:
        assert db.scalar(select(Classes).where(Classes.class_code == "D03-LOCK-1")) is not None
        assert db.scalar(select(Classes).where(Classes.class_code == "D03-LOCK-2")) is None

def test_unique_attendance_record(engine):
    with Session(engine) as db:
        user = User(
            username="d03_attendance_teacher",
            password_hash="test-only",
            role="teacher",
        )
        db.add(user)
        db.flush()

        teacher = Teachers(
            user_id=user.id,
            teacher_code="D03-GV-ATT",
            full_name="Giang vien kiem thu",
        )
        db.add(teacher)

        c = course("D03-ATT")
        db.add(c)
        s = student(db, "d03_attendance_student", "D03-SV-ATT")
        db.flush()

        attendance = AttendanceSessions(
            course_id=c.id,
            created_by=teacher.id,
            token_hash="d03-attendance-token",
            starts_at=1000.0,
            expires_at=2000.0,
            status="active",
        )
        db.add(attendance)
        db.flush()

        db.add(
            AttendanceRecords(
                session_id=attendance.id,
                student_id=s.id,
                checked_in_at=1100.0,
                status="present",
            )
        )
        db.commit()
        session_id, student_id = attendance.id, s.id

    with Session(engine) as db:
        db.add(
            AttendanceRecords(
                session_id=session_id,
                student_id=student_id,
                checked_in_at=1200.0,
                status="present",
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_unique_exam_registration(engine):
    with Session(engine) as db:
        user = User(
            username="d03_exam_teacher",
            password_hash="test-only",
            role="teacher",
        )
        db.add(user)
        db.flush()

        teacher = Teachers(
            user_id=user.id,
            teacher_code="D03-GV-EXAM",
            full_name="Giang vien kiem thu",
        )
        db.add(teacher)

        c = course("D03-EXAM")
        db.add(c)
        s = student(db, "d03_exam_student", "D03-SV-EXAM")
        db.flush()

        exam = CodingExams(
            course_id=c.id,
            created_by=teacher.id,
            title="Bai thi kiem thu D03",
            grade_component="FINAL",
            starts_at=1000.0,
            ends_at=2000.0,
            status="published",
            results_published=False,
        )
        db.add(exam)
        db.flush()

        db.add(
            ExamRegistrations(
                exam_id=exam.id,
                student_id=s.id,
                registered_at=900.0,
                status="registered",
            )
        )
        db.commit()
        exam_id, student_id = exam.id, s.id

    with Session(engine) as db:
        db.add(
            ExamRegistrations(
                exam_id=exam_id,
                student_id=student_id,
                registered_at=950.0,
                status="registered",
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()