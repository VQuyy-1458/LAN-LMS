"""SQLite durable queue: short transactions, renewable leases and fenced completion."""

import json
import time
import uuid
from dataclasses import dataclass
from sqlalchemy import select, or_, and_
from server.app.models import (
    JudgeJobs,
    CodeSubmissions,
    JudgeResults,
    Problems,
    CodingExams,
    Students,
    Courses,
)
from server.app.services.idempotency import write_lock
from server.app.services.activity import emit


@dataclass(frozen=True)
class Claim:
    job_id: int
    submission_id: int
    token: str


class LostLease(RuntimeError):
    pass


def notify(db, sub):
    p = db.get(Problems, sub.problem_id)
    e = db.get(CodingExams, p.exam_id)
    s = db.get(Students, sub.student_id)
    emit(
        db,
        "submission.updated",
        e.course_id,
        {"submission_id": sub.id, "status": sub.status, "version": sub.version},
        s.user_id,
    )
    db.get(Courses, e.course_id).grades_published = False


def terminal(db, job, sub, verdict, message="", reason=None):
    p = db.get(Problems, sub.problem_id)
    sub.status = verdict
    sub.score = (
        p.max_score
        if verdict == "Accepted"
        else None if verdict == "System Error" else 0
    )
    sub.version += 1
    result = db.scalar(select(JudgeResults).where(JudgeResults.submission_id == sub.id))
    if not result:
        result = JudgeResults(submission_id=sub.id)
        db.add(result)
    result.is_correct = verdict == "Accepted"
    result.verdict = verdict
    result.score = sub.score
    result.compile_message = message[:16384]
    result.reason_code = reason
    result.judged_at = time.time()
    job.status = "done"
    job.lease_until = None
    job.finished_at = time.time()
    notify(db, sub)


def claim(sessions, worker_id, lease_seconds=60, now=None):
    now = time.time() if now is None else now
    with sessions() as db:
        write_lock(db)
        while True:
            job = db.scalar(
                select(JudgeJobs)
                .where(
                    or_(
                        JudgeJobs.status == "pending",
                        and_(
                            JudgeJobs.status == "running", JudgeJobs.lease_until < now
                        ),
                    )
                )
                .order_by(JudgeJobs.id)
                .limit(1)
            )
            if not job:
                db.commit()
                return None
            sub = db.get(CodeSubmissions, job.submission_id)
            if job.attempt_count >= 3:
                terminal(db, job, sub, "System Error", reason="WORKER_RETRY_EXHAUSTED")
                db.flush()
                continue
            job.status = "running"
            job.attempt_id = uuid.uuid4().hex
            job.attempt_count += 1
            job.worker_id = worker_id
            job.lease_until = now + lease_seconds
            job.started_at = now
            sub.status = "Compiling"
            sub.score = None
            sub.version += 1
            notify(db, sub)
            result = Claim(job.id, sub.id, job.attempt_id)
            db.commit()
            return result


def owned(db, c):
    j = db.get(JudgeJobs, c.job_id)
    if (
        not j
        or j.attempt_id != c.token
        or j.status != "running"
        or not j.lease_until
        or j.lease_until <= time.time()
    ):
        raise LostLease("Judge lease no longer owned")
    return j, db.get(CodeSubmissions, c.submission_id)


def renew(sessions, c, lease_seconds=60):
    with sessions() as db:
        write_lock(db)
        j, _ = owned(db, c)
        j.lease_until = time.time() + lease_seconds
        db.commit()


def running(sessions, c, compile_ms):
    with sessions() as db:
        write_lock(db)
        j, sub = owned(db, c)
        j.compile_ms = compile_ms
        sub.status = "Running"
        sub.version += 1
        notify(db, sub)
        db.commit()


def complete(sessions, c, result, compile_ms, run_ms):
    with sessions() as db:
        write_lock(db)
        j, sub = owned(db, c)
        terminal(db, j, sub, result.verdict, result.compile_message)
        j.compile_ms = compile_ms
        j.run_ms = run_ms
        db.commit()


def retry(sessions, c):
    with sessions() as db:
        write_lock(db)
        j, sub = owned(db, c)
        if j.attempt_count >= 3:
            terminal(db, j, sub, "System Error", reason="JUDGE_UNAVAILABLE")
        else:
            j.status = "pending"
            j.lease_until = None
            sub.status = "Pending"
            sub.version += 1
            notify(db, sub)
        db.commit()
