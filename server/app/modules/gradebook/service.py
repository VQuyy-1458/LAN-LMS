import json
import time
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select, func
from ...models import *

DEFAULT_WEIGHTS = {"attendance": 10, "homework": 20, "midterm": 30, "final": 40}


def weights(db, cid):
    rows = list(
        db.scalars(select(GradeComponents).where(GradeComponents.course_id == cid))
    )
    return {r.component_code: r.weight for r in rows} if rows else dict(DEFAULT_WEIGHTS)


def components(db, cid):
    rows = {
        r.component_code: r
        for r in db.scalars(
            select(GradeComponents).where(GradeComponents.course_id == cid)
        )
    }
    for code, weight in DEFAULT_WEIGHTS.items():
        if code not in rows:
            rows[code] = GradeComponents(
                course_id=cid, component_code=code, weight=weight, max_score=10
            )
            db.add(rows[code])
    db.flush()
    return rows


def exam_score(db, cid, sid, kind):
    e = db.scalar(
        select(CodingExams).where(
            CodingExams.course_id == cid, CodingExams.grade_component == kind
        )
    )
    if (
        not e
        or e.status == "draft"
        or (e.status != "closed" and e.ends_at > time.time())
    ):
        return None
    accepted = set(
        db.scalars(
            select(CodeSubmissions.problem_id)
            .join(Problems, CodeSubmissions.problem_id == Problems.id)
            .where(
                Problems.exam_id == e.id,
                CodeSubmissions.student_id == sid,
                CodeSubmissions.status == "Accepted",
            )
        )
    )
    pending = db.scalar(
        select(func.count(CodeSubmissions.id))
        .join(Problems, CodeSubmissions.problem_id == Problems.id)
        .where(
            Problems.exam_id == e.id,
            CodeSubmissions.student_id == sid,
            CodeSubmissions.problem_id.not_in(accepted),
            CodeSubmissions.status.in_(
                ["Pending", "Compiling", "Running", "System Error"]
            ),
        )
    )
    if pending:
        return None
    ladder = json.loads(e.score_ladder_json)
    return ladder[min(len(accepted), len(ladder) - 1)]


def scores(db, cid, sid):
    now = time.time()
    result = {}
    closed = list(
        db.scalars(
            select(AttendanceSessions.id).where(
                AttendanceSessions.course_id == cid,
                (AttendanceSessions.status == "closed")
                | (AttendanceSessions.expires_at <= now),
            )
        )
    )
    present = (
        db.scalar(
            select(func.count(AttendanceRecords.id)).where(
                AttendanceRecords.session_id.in_(closed),
                AttendanceRecords.student_id == sid,
                AttendanceRecords.status.in_(["present", "late"]),
            )
        )
        if closed
        else 0
    )
    result["attendance"] = 10 * present / len(closed) if closed else None
    assignments = list(
        db.scalars(
            select(Assignments).where(
                Assignments.course_id == cid, Assignments.due_at <= now
            )
        )
    )
    homework = []
    for a in assignments:
        sub = db.scalar(
            select(AssignmentSubmissions)
            .where(
                AssignmentSubmissions.assignment_id == a.id,
                AssignmentSubmissions.student_id == sid,
            )
            .order_by(AssignmentSubmissions.attempt_no.desc())
            .limit(1)
        )
        homework.append(sub.score if sub else 0)
    result["homework"] = (
        (sum(homework) / len(homework))
        if homework and all(x is not None for x in homework)
        else None
    )
    for kind in ("midterm", "final"):
        result[kind] = exam_score(db, cid, sid, kind)
    for grade, component in db.execute(
        select(Grades, GradeComponents)
        .join(GradeComponents)
        .where(
            GradeComponents.course_id == cid,
            Grades.student_id == sid,
            Grades.entry_method == "manual",
        )
    ):
        result[component.component_code] = grade.score
    return result


def round_score(value):
    return (
        float(Decimal(str(value)).quantize(Decimal(".01"), rounding=ROUND_HALF_UP))
        if value is not None
        else None
    )


def rows(db, cid, student_id=None):
    q = (
        select(Students)
        .join(CourseEnrollments)
        .where(CourseEnrollments.course_id == cid, CourseEnrollments.status == "active")
    )
    if student_id is not None:
        q = q.where(Students.id == student_id)
    ws = weights(db, cid)
    result = []
    for s in db.scalars(q.order_by(Students.student_code)):
        values = scores(db, cid, s.id)
        total = (
            None
            if any(ws.get(k, 0) > 0 and values.get(k) is None for k in DEFAULT_WEIGHTS)
            else sum((values.get(k) or 0) * ws.get(k, 0) / 100 for k in DEFAULT_WEIGHTS)
        )
        cls = db.get(Classes, s.class_id) if s.class_id else None
        result.append(
            dict(
                student_id=s.student_code,
                full_name=s.full_name,
                class_name=cls.class_code if cls else "",
                **{k + "_score": round_score(v) for k, v in values.items()},
                total_score=round_score(total)
            )
        )
    return result
