"""Completion acceptance: real HTTP permissions, deadlines, queue fencing and AC-based grading."""

import concurrent.futures
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
from sqlalchemy import select, func
from test_day25 import context
from server.app.models import (
    CodingExams,
    CsvImportPreviews,
    ExamSessions,
    JudgeJobs,
    Students,
)
from judge import job_queue
from judge.worker import execute
from judge.runners.container import Result


def prepare_exam(app, c, cid, count=1):
    now = datetime.now(timezone.utc)
    r = c["t"].post(
        f"/api/courses/{cid}/coding-exams",
        json={
            "title": "Final",
            "starts_at": (now + timedelta(minutes=5)).isoformat(),
            "ends_at": (now + timedelta(hours=1)).isoformat(),
            "grade_component": "final",
            "score_ladder": [0, 10] if count == 1 else [0, 5, 7, 8, 9, 10],
        },
    )
    assert r.status_code == 201, r.text
    eid = r.json()["id"]
    pids = []
    for n in range(count):
        r = c["t"].post(
            f"/api/coding-exams/{eid}/problems",
            json={
                "title": f"Sum {n}",
                "statement": "Add two numbers. Sample: 1 2 -> 3",
                "max_score": 100,
            },
        )
        assert r.status_code == 201, r.text
        pid = r.json()["id"]
        pids.append(pid)
        r = c["t"].post(
            f"/api/problems/{pid}/test-cases",
            files={
                "input_file": ("01.in", b"1 2\n"),
                "expected_output_file": ("01.out", b"3\n"),
            },
            data={"points": "100", "is_hidden": "true", "ordinal": "1"},
        )
        assert r.status_code == 201, r.text
    r = c["t"].patch(f"/api/coding-exams/{eid}", json={"status": "scheduled"})
    assert r.status_code == 200, r.text
    with app.state.sessions.begin() as db:
        db.get(CodingExams, eid).starts_at = time.time() - 1
    r = c["s"].post(f"/api/coding-exams/{eid}/sessions/start")
    assert r.status_code == 200, r.text
    return eid, pids, r.json()["id"]


def submit(c, pid, sid, key="one", source="int main(){return 0;}"):
    return c["s"].post(
        f"/api/problems/{pid}/submissions",
        json={"exam_session_id": sid, "language": "cpp", "source_code": source},
        headers={"Idempotency-Key": key},
    )


def test_calendar_rights_and_attendance_atomic(context):
    app, c, cid = context
    body = {
        "title": "Lesson",
        "starts_at": "2026-11-01T08:00:00+07:00",
        "ends_at": "2026-11-01T10:00:00+07:00",
        "description": "Room A",
    }
    assert c["s"].post(f"/api/courses/{cid}/events", json=body).status_code == 403
    assert c["t"].post(f"/api/courses/{cid}/events", json=body).status_code == 201
    assert c["outsider"].get(f"/api/courses/{cid}/events").status_code == 403
    assert c["s"].get(f"/api/courses/{cid}/events").json()["total"] == 1
    r = c["t"].post(f"/api/courses/{cid}/attendance-sessions", json={"title": "Week 1"})
    assert r.status_code == 201, r.text
    session = r.json()
    sid = session["id"]
    path = f"/api/attendance-sessions/{sid}/check-in"
    assert "token" not in c["s"].get(f"/api/attendance-sessions/{sid}").json()
    assert c["s"].post(path, json={"token": "wrong"}).status_code == 403
    assert c["outsider"].post(path, json={"token": session["token"]}).status_code == 403

    def attempt(_):
        return c["s"].post(path, json={"token": session["token"]})

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        rs = list(pool.map(attempt, range(2)))
    assert sorted(x.status_code for x in rs) == [200, 201]
    assert rs[0].json()["id"] == rs[1].json()["id"]
    c["t"].patch(f"/api/attendance-sessions/{sid}", json={"status": "closed"})
    assert c["t"].get(f"/api/attendance-sessions/{sid}/records").json()["total"] == 1
    assert c["s"].get(f"/api/attendance-sessions/{sid}/records").status_code == 403
    assert (
        c["t"]
        .patch(
            f"/api/attendance-sessions/{sid}/records",
            json={
                "student_id": "s",
                "status": "absent",
                "reason": "Corrected by teacher",
            },
        )
        .status_code
        == 409
    )


def test_csv_expired_and_concurrent_confirm(context):
    app, c, cid = context
    data = b"student_id,full_name,date_of_birth,class_name\nnew1,One,02112005,C1\n"

    def preview():
        return (
            c["t"]
            .post(
                f"/api/courses/{cid}/students/import-preview",
                files={"file": ("students.csv", data)},
            )
            .json()["preview_id"]
        )

    old = preview()
    with app.state.sessions.begin() as db:
        db.scalar(
            select(CsvImportPreviews).where(CsvImportPreviews.preview_id == old)
        ).expires_at = 0
    path = f"/api/courses/{cid}/students/import-confirm"
    assert (
        c["t"]
        .post(path, json={"preview_id": old}, headers={"Idempotency-Key": "expired"})
        .status_code
        == 409
    )
    fresh = preview()

    def attempt(_):
        return c["t"].post(
            path, json={"preview_id": fresh}, headers={"Idempotency-Key": "same"}
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        rs = list(pool.map(attempt, range(2)))
    assert all(r.status_code == 200 for r in rs), [r.text for r in rs]
    assert rs[0].json() == rs[1].json()
    with app.state.sessions() as db:
        assert (
            db.scalar(
                select(func.count(Students.id)).where(Students.student_code == "new1")
            )
            == 1
        )


def test_exam_validation_locking_and_private_source(context):
    app, c, cid = context
    eid, pids, sid = prepare_exam(app, c, cid)
    assert c["s"].get(f"/api/problems/{pids[0]}/test-cases").status_code == 403
    assert c["other"].get(f"/api/coding-exams/{eid}/sessions").status_code == 403
    assert (
        c["t"]
        .patch(f"/api/problems/{pids[0]}", json={"statement": "Changed"})
        .status_code
        == 409
    )
    first = submit(c, pids[0], sid)
    assert first.status_code == 202, first.text
    assert submit(c, pids[0], sid).json() == first.json()
    assert submit(c, pids[0], sid, source="different").status_code == 409
    subid = first.json()["id"]
    assert c["outsider"].get(f"/api/submissions/{subid}").status_code == 403
    assert (
        c["s"].get(f"/api/submissions/{subid}").json()["source_code"]
        == "int main(){return 0;}"
    )
    assert (
        "source_code"
        not in c["s"].get(f"/api/problems/{pids[0]}/submissions").json()["items"][0]
    )
    c["s"].post(f"/api/exam-sessions/{sid}/finish")
    assert submit(c, pids[0], sid, key="after-finish").status_code == 409
    # Retry a request already committed before finish still returns the accepted resource.
    assert submit(c, pids[0], sid).status_code == 202


def test_expiry_and_session_reuse(context):
    app, c, cid = context
    eid, pids, sid = prepare_exam(app, c, cid)
    assert c["s"].post(f"/api/coding-exams/{eid}/sessions/start").json()["id"] == sid
    with app.state.sessions.begin() as db:
        db.get(ExamSessions, sid).ends_at = time.time() - 1
    assert submit(c, pids[0], sid).status_code == 409
    assert c["s"].get(f"/api/exam-sessions/{sid}").json()["status"] == "expired"


def test_queue_lease_fences_stale_completion_and_retries(context):
    app, c, cid = context
    eid, pids, sid = prepare_exam(app, c, cid)
    submit(c, pids[0], sid)
    first = job_queue.claim(app.state.sessions, "a")
    assert first
    assert job_queue.claim(app.state.sessions, "b") is None
    with app.state.sessions.begin() as db:
        db.get(JudgeJobs, first.job_id).lease_until = time.time() - 1
    second = job_queue.claim(app.state.sessions, "b")
    assert second.token != first.token
    with pytest.raises(job_queue.LostLease):
        job_queue.complete(
            app.state.sessions, first, Result("Accepted", 100, 100), 1, 1
        )
    job_queue.complete(
        app.state.sessions, second, Result("Wrong Answer", 50, 100), 1, 1
    )
    r = c["s"].get(f"/api/exam-sessions/{sid}").json()
    assert r["accepted_count"] == 0 and r["total_score"] == 0
    # Partial test points do not count as a solved problem under the chosen policy.
    r = c["s"].get(f"/api/problems/{pids[0]}/submissions").json()["items"][0]
    assert r["score"] == 0 and r["verdict_code"] == "WA"
    submit(c, pids[0], sid, key="two")
    for _ in range(3):
        claim = job_queue.claim(app.state.sessions, "broken")
        assert claim
        job_queue.retry(app.state.sessions, claim)
    assert job_queue.claim(app.state.sessions, "done") is None
    assert (
        c["s"]
        .get(f"/api/problems/{pids[0]}/submissions")
        .json()["items"][0]["verdict_code"]
        == "SE"
    )


def test_accepted_count_ladder_and_grades_publish(context):
    app, c, cid = context
    eid, pids, sid = prepare_exam(app, c, cid, 5)
    for index, pid in enumerate(pids):
        submit(c, pid, sid, key=f"ac-{index}")
        claim = job_queue.claim(app.state.sessions, "test")
        job_queue.complete(
            app.state.sessions, claim, Result("Accepted", 100, 100), 2, 3
        )
        result = c["s"].get(f"/api/exam-sessions/{sid}").json()
        assert result["total_score"] == [5, 7, 8, 9, 10][index]
    submit(c, pids[0], sid, key="wrong-after-ac")
    claim = job_queue.claim(app.state.sessions, "test")
    job_queue.complete(app.state.sessions, claim, Result("Wrong Answer", 0, 100), 1, 1)
    assert c["s"].get(f"/api/exam-sessions/{sid}").json()["total_score"] == 10
    assert c["s"].get(f"/api/courses/{cid}/gradebook").json()["items"][0]["total_score"] is None
    # A later infrastructure error on an already solved problem cannot erase an AC.
    submit(c, pids[0], sid, key="system-error-after-ac")
    claim = job_queue.claim(app.state.sessions, "infrastructure")
    job_queue.complete(
        app.state.sessions, claim, Result("System Error", None, 100), 1, 1
    )
    weights = {"attendance": 0, "homework": 0, "midterm": 0, "final": 100}
    assert (
        c["t"]
        .patch(f"/api/courses/{cid}/grade-components", json={**weights, "final": 90})
        .status_code
        == 422
    )
    assert (
        c["t"].patch(f"/api/courses/{cid}/grade-components", json=weights).status_code
        == 200
    )
    assert (
        c["t"]
        .post(f"/api/courses/{cid}/gradebook/publish", json={"published": True})
        .status_code
        == 409
    )
    assert (
        c["t"].patch(f"/api/coding-exams/{eid}", json={"status": "closed"}).status_code
        == 200
    )
    assert (
        c["t"]
        .post(f"/api/courses/{cid}/gradebook/publish", json={"published": True})
        .status_code
        == 200
    )
    assert (
        c["s"].get(f"/api/courses/{cid}/gradebook").json()["items"][0]["total_score"]
        == 10
    )
    assert (
        c["t"]
        .get(f"/api/courses/{cid}/gradebook/export-csv")
        .content.startswith(b"\xef\xbb\xbf")
    )
    edit = {
        "items": [
            {
                "student_id": "s",
                "component": "final",
                "score": 8,
                "reason": "Reviewed by teacher",
            }
        ]
    }
    assert c["t"].patch(f"/api/courses/{cid}/grades", json=edit).status_code == 423
    assert c["s"].get(f"/api/courses/{cid}/gradebook").json()["items"][0]["total_score"] == 10
    assert (
        c["t"].get(f"/api/courses/{cid}/gradebook").json()["items"][0]["total_score"]
        == 10
    )


@pytest.mark.skipif(os.getenv("RUN_DOCKER_TESTS") != "1", reason="Real Docker required")
def test_api_worker_actual_docker(context):
    app, c, cid = context
    eid, pids, sid = prepare_exam(app, c, cid)
    source = (
        '#include <iostream>\nint main(){int a,b;std::cin>>a>>b;std::cout<<a+b<<"\\n";}'
    )
    r = submit(c, pids[0], sid, source=source)
    assert r.status_code == 202
    claim = job_queue.claim(app.state.sessions, "real-docker")
    execute(app.state.sessions, app.state.storage_root, claim)
    result = c["s"].get(f"/api/submissions/{r.json()['id']}").json()
    assert result["verdict_code"] == "AC", result
    assert c["s"].get(f"/api/exam-sessions/{sid}").json()["total_score"] == 10


def test_expired_attempt_limit_is_persisted(context):
    app, c, cid = context
    _, pids, sid = prepare_exam(app, c, cid)
    submit(c, pids[0], sid)
    for _ in range(3):
        claim = job_queue.claim(app.state.sessions, "dying")
        with app.state.sessions.begin() as db:
            db.get(JudgeJobs, claim.job_id).lease_until = time.time() - 1
    assert job_queue.claim(app.state.sessions, "recovery") is None
    with app.state.sessions() as db:
        assert db.get(JudgeJobs, claim.job_id).status == "done"
    assert (
        c["s"]
        .get(f"/api/problems/{pids[0]}/submissions")
        .json()["items"][0]["verdict_code"]
        == "SE"
    )


def test_worker_event_reaches_authenticated_websocket(context):
    from fastapi.testclient import TestClient

    app, c, cid = context
    _, pids, sid = prepare_exam(app, c, cid)
    sub = submit(c, pids[0], sid).json()
    claim = job_queue.claim(app.state.sessions, "notification-test")
    app.state.settings.heartbeat_seconds = 0.1
    app.state.settings.heartbeat_timeout = 2
    with TestClient(app) as live:
        live.cookies.update(c["s"].cookies)
        with live.websocket_connect(
            "/ws", headers={"Origin": "http://localhost:3000"}
        ) as ws:
            job_queue.complete(
                app.state.sessions, claim, Result("Accepted", 100, 100), 1, 1
            )
            found = False
            for _ in range(40):
                message = ws.receive_json()
                if message["type"] == "heartbeat":
                    ws.send_json({"type": "heartbeat.ack", "id": message["id"]})
                elif (
                    message["type"] == "submission.updated"
                    and message["data"].get("submission_id") == sub["id"]
                    and message["data"]["status"] == "Accepted"
                ):
                    found = True
                    break
            assert found
    assert c["s"].get(f"/api/submissions/{sub['id']}").json()["verdict_code"] == "AC"


def test_synthetic_content_seed_is_idempotent(context):
    from database.seed.seed_content import seed_content
    from server.app.models import Courses, Problems, TestCases as Cases

    app, c, cid = context
    with app.state.sessions.begin() as db:
        db.get(Courses, cid).course_code = "DEMO-LTM"
        seed_content(db, "t", app.state.storage_root)
    with app.state.sessions.begin() as db:
        seed_content(db, "t", app.state.storage_root)
    with app.state.sessions() as db:
        assert db.scalar(select(func.count(CodingExams.id))) == 2
        assert db.scalar(select(func.count(Problems.id))) == 10
        assert db.scalar(select(func.count(Cases.id))) == 20
