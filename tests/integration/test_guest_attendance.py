"""Guest catalogue and teacher/student attendance permissions through real HTTP."""

import time
from fastapi.testclient import TestClient
from sqlalchemy import select
from test_day25 import context
from server.app.models import AttendanceSessions, AuditLogs
from server.app.modules.gradebook.service import scores


def test_guest_only_sees_catalogue(context):
    app, clients, cid = context
    with TestClient(app) as guest:
        r = guest.get("/api/public/courses")
        assert r.status_code == 200
        course = r.json()["items"][0]
        assert course["id"] == cid
        assert set(course) == {
            "id",
            "name",
            "course_code",
            "description",
            "semester",
            "academic_year",
        }
        for path in (
            f"/api/courses/{cid}",
            f"/api/courses/{cid}/events",
            f"/api/courses/{cid}/students",
            f"/api/courses/{cid}/attendance-sessions",
        ):
            assert guest.get(path).status_code == 401


def test_roster_manual_statuses_and_qr_retry_preserve_teacher_correction(context):
    app, c, cid = context
    created = c["t"].post(f"/api/courses/{cid}/attendance-sessions", json={}).json()
    sid = created["id"]
    path = f"/api/attendance-sessions/{sid}"
    roster = c["t"].get(path + "/roster").json()
    assert roster["total"] == 1
    assert roster["items"][0]["status"] == "unmarked"
    assert roster["items"][0]["student_id"] == "s"
    for actor in ("s", "outsider", "other"):
        assert c[actor].get(path + "/roster").status_code == 403
        assert (
            c[actor]
            .patch(
                path + "/records",
                json={
                    "student_id": "s",
                    "status": "late",
                    "reason": "Teacher manual correction",
                },
            )
            .status_code
            == 403
        )
    for status in ("present", "absent", "late"):
        result = c["t"].patch(
            path + "/records",
            json={
                "student_id": "s",
                "status": status,
                "reason": "Manual attendance at lesson",
            },
        )
        assert result.status_code == 200, result.text
        assert result.json()["status"] == status
        # Scanning again must not erase a teacher's explicit correction.
        retry = c["s"].post(path + "/check-in", json={"token": created["token"]})
        assert retry.json()["status"] == status
    assert (
        c["s"]
        .get(f"/api/courses/{cid}/attendance-sessions")
        .json()["items"][0]["my_status"]
        == "late"
    )
    assert (
        c["t"]
        .patch(
            path + "/records",
            json={"student_id": "outsider", "status": "late", "reason": "Not enrolled"},
        )
        .status_code
        == 404
    )
    assert (
        c["t"]
        .patch(
            path + "/records",
            json={"student_id": "s", "status": "unknown", "reason": "Invalid value"},
        )
        .status_code
        == 422
    )
    c["t"].patch(path, json={"status": "closed"})
    with app.state.sessions() as db:
        from server.app.models import Students

        student = db.scalar(select(Students).where(Students.student_code == "s"))
        assert scores(db, cid, student.id)["attendance"] == 10
        assert (
            len(
                list(db.scalars(select(AuditLogs).where(AuditLogs.action == "correct")))
            )
            == 3
        )


def test_qr_from_lesson_validation_and_expiry(context):
    app, c, cid = context
    event = (
        c["t"]
        .post(
            f"/api/courses/{cid}/events",
            json={
                "title": "Buổi học tuần 1",
                "event_type": "lesson",
                "starts_at": "2026-11-01T08:00:00+07:00",
                "ends_at": "2026-11-01T10:00:00+07:00",
            },
        )
        .json()
    )
    path = f"/api/courses/{cid}/attendance-sessions"
    r = c["t"].post(path, json={"event_id": event["id"], "title": "Ignored"})
    assert r.status_code == 201, r.text
    payload = r.json()
    assert payload["title"] == event["title"]
    assert "<svg" in payload["qr_svg"]
    assert f'attendance={payload["id"]}' in payload["check_in_path"]
    other = (
        c["other"]
        .post("/api/courses", json={"course_code": "OTHER", "name": "Other"})
        .json()
    )
    assert (
        c["other"]
        .post(
            f'/api/courses/{other["id"]}/attendance-sessions',
            json={"event_id": event["id"]},
        )
        .status_code
        == 422
    )
    assert c["t"].post(path, json={"event_id": 99999}).status_code == 422
    with app.state.sessions.begin() as db:
        db.get(AttendanceSessions, payload["id"]).expires_at = time.time() - 1
    assert (
        c["s"]
        .post(
            f'/api/attendance-sessions/{payload["id"]}/check-in',
            json={"token": payload["token"]},
        )
        .status_code
        == 409
    )
