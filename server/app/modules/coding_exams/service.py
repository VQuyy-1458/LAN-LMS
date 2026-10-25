import json
import math
import time
from sqlalchemy import select, func
from ...core.security import fail
from ...models import (
    CodingExams,
    Problems,
    TestCases,
    ExamSessions,
    ExamRegistrations,
    CodeSubmissions,
    Students,
)
from ...services import access
from ...services.activity import iso

CODES = {
    "Pending": "PENDING",
    "Compiling": "COMPILING",
    "Running": "RUNNING",
    "Accepted": "AC",
    "Wrong Answer": "WA",
    "Compile Error": "CE",
    "Time Limit Exceeded": "TLE",
    "Memory Limit Exceeded": "MLE",
    "Runtime Error": "RTE",
    "System Error": "SE",
}


def exam(db, user, eid, manage=False):
    row = db.get(CodingExams, eid)
    if not row:
        fail(404, "NOT_FOUND", "Không tìm thấy kỳ thi")
    access.course(db, user, row.course_id, manage)
    return row


def state(row):
    if row.status in ("draft", "closed"):
        return row.status
    now = time.time()
    return (
        "upcoming" if now < row.starts_at else "ended" if now >= row.ends_at else "open"
    )


def exam_payload(row):
    ladder = json.loads(row.score_ladder_json)
    return dict(
        id=row.id,
        course_id=row.course_id,
        title=row.title,
        grade_component=row.grade_component,
        starts_at=iso(row.starts_at),
        ends_at=iso(row.ends_at),
        status=state(row),
        score_ladder=ladder,
        problem_count=len(ladder) - 1,
        server_time=iso(time.time()),
    )


def editable(db, row):
    if (
        row.status == "closed"
        or time.time() >= row.starts_at
        or db.scalar(
            select(ExamSessions.id)
            .join(ExamRegistrations)
            .where(ExamRegistrations.exam_id == row.id)
            .limit(1)
        )
    ):
        fail(409, "EXAM_LOCKED", "Không sửa đề sau khi kỳ thi bắt đầu")


def ready(db, row):
    problems = list(db.scalars(select(Problems).where(Problems.exam_id == row.id)))
    if len(problems) != len(json.loads(row.score_ladder_json)) - 1:
        fail(409, "INVALID_EXAM", "Số bài cần khớp bảng quy đổi điểm")
    for p in problems:
        tests = list(db.scalars(select(TestCases).where(TestCases.problem_id == p.id)))
        if not tests or not math.isclose(
            sum(t.weight for t in tests), p.max_score, abs_tol=1e-6
        ):
            fail(
                409,
                "INVALID_TESTS",
                "Mỗi bài cần test có tổng trọng số bằng điểm tối đa",
            )
    return problems


def problem(db, user, pid, manage=False):
    row = db.get(Problems, pid)
    if not row:
        fail(404, "NOT_FOUND", "Không tìm thấy bài")
    e = exam(db, user, row.exam_id, manage)
    if user.role == "student" and (e.status == "draft" or time.time() < e.starts_at):
        fail(403, "EXAM_NOT_OPEN", "Chưa đến giờ xem đề")
    return row, e


def problem_payload(row):
    return dict(
        id=row.id,
        exam_id=row.exam_id,
        title=row.title,
        statement=row.statement,
        languages=json.loads(row.languages_json),
        io_mode=row.io_mode,
        input_filename=row.input_filename,
        output_filename=row.output_filename,
        time_limit_ms=row.time_limit_ms,
        memory_limit_mib=row.memory_limit_mib,
        max_score=row.max_score,
        comparator=row.comparator,
    )


def session(db, user, sid):
    row = db.get(ExamSessions, sid)
    if not row:
        fail(404, "NOT_FOUND", "Không tìm thấy phiên thi")
    reg = db.get(ExamRegistrations, row.registration_id)
    e = exam(db, user, reg.exam_id)
    s = db.get(Students, reg.student_id)
    if user.role != "teacher" and s.user_id != user.user_id:
        fail(403, "FORBIDDEN", "Không có quyền xem phiên thi")
    return row, reg, e, s


def session_payload(db, row, reg, e, s, hub=None):
    status = (
        "expired"
        if row.status == "active"
        and (row.ends_at <= time.time() or e.status == "closed")
        else row.status
    )
    accepted = set(
        db.scalars(
            select(CodeSubmissions.problem_id).where(
                CodeSubmissions.exam_session_id == row.id,
                CodeSubmissions.status == "Accepted",
            )
        )
    )
    ladder = json.loads(e.score_ladder_json)
    connected = hub and any(uid == s.user_id for uid, _ in hub.connections.values())
    pending = db.scalar(
        select(func.count(CodeSubmissions.id)).where(
            CodeSubmissions.exam_session_id == row.id,
            CodeSubmissions.status.in_(["Pending", "Compiling", "Running"]),
        )
    )
    return dict(
        id=row.id,
        exam_id=e.id,
        student_id=s.student_code,
        full_name=s.full_name,
        started_at=iso(row.started_at),
        ends_at=iso(row.ends_at),
        submitted_at=iso(row.submitted_at),
        status=status,
        last_seen_at=iso(row.last_seen_at),
        connection_status="connected" if connected else "disconnected",
        accepted_count=len(accepted),
        accepted_problem_ids=sorted(accepted),
        problem_count=len(ladder) - 1,
        total_score=ladder[min(len(accepted), len(ladder) - 1)],
        pending_count=pending,
        server_time=iso(time.time()),
    )
