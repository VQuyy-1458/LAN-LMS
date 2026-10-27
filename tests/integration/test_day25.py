import concurrent.futures
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from server.app.main import create_app
from server.app.core.config import Settings
from server.app.core.database import Base, User
from server.app.core.security import hasher
from server.app.models import (
    Teachers,
    Students,
    Classes,
    CourseEnrollments,
    AssignmentSubmissions,
    IdempotencyKeys,
    Assignments,
    CourseMaterials,
)

ORIGIN = {"Origin": "http://localhost:3000"}


@pytest.fixture
def context(tmp_path):
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}"))
    app.state.storage_root = tmp_path / "storage"
    Base.metadata.create_all(app.state.engine)
    with app.state.sessions.begin() as db:
        for name, role in [
            ("t", "teacher"),
            ("other", "teacher"),
            ("s", "student"),
            ("outsider", "student"),
        ]:
            u = User(
                username=name,
                password_hash=hasher.hash("password-123"),
                role=role,
                must_change_password=False,
            )
            db.add(u)
            db.flush()
            if role == "teacher":
                db.add(Teachers(user_id=u.id, teacher_code=name, full_name=name))
            else:
                db.add(Students(user_id=u.id, student_code=name, full_name=name))
    clients = {}
    for name in ["t", "other", "s", "outsider"]:
        c = TestClient(app)
        assert (
            c.post(
                "/api/auth/login",
                headers=ORIGIN,
                json={"username": name, "password": "password-123"},
            ).status_code
            == 200
        )
        c.headers.update(
            {**ORIGIN, "X-CSRF-Token": c.get("/api/auth/csrf").json()["csrf_token"]}
        )
        clients[name] = c
    course = clients["t"].post(
        "/api/courses", json={"course_code": "C1", "name": "Course"}
    )
    assert course.status_code == 201, course.text
    cid = course.json()["id"]
    with app.state.sessions.begin() as db:
        s = db.scalar(select(Students).join(User).where(User.username == "s"))
        db.add(CourseEnrollments(course_id=cid, student_id=s.id, status="active"))
    yield app, clients, cid
    for c in clients.values():
        c.close()
    app.state.engine.dispose()


def test_course_permissions_and_pagination(context):
    app, c, cid = context
    assert c["s"].get("/api/courses").json()["total"] == 1
    assert c["outsider"].get("/api/courses").json()["total"] == 0
    assert c["other"].get(f"/api/courses/{cid}").status_code == 403
    assert c["outsider"].get(f"/api/courses/{cid}").status_code == 403
    assert c["s"].get(f"/api/courses/{cid}/students").status_code == 403
    assert (
        c["s"]
        .post("/api/courses", json={"course_code": "BAD", "name": "Bad"})
        .status_code
        == 403
    )
    assert c["t"].get("/api/courses?page_size=101").status_code == 422


def test_csv_preview_confirm_retry_and_password(context):
    app, c, cid = context
    data = b"student_id,full_name,date_of_birth,class_name,email\n001,Student One,02112005,C01,\n"
    preview = c["t"].post(
        f"/api/courses/{cid}/students/import-preview",
        files={"file": ("students.csv", data)},
    )
    assert preview.status_code == 200 and preview.json()["can_confirm"], preview.text
    path = f"/api/courses/{cid}/students/import-confirm"
    body = {"preview_id": preview.json()["preview_id"]}
    first = c["t"].post(path, json=body, headers={"Idempotency-Key": "import-1"})
    assert first.status_code == 200, first.text
    assert (
        c["t"].post(path, json=body, headers={"Idempotency-Key": "import-1"}).json()
        == first.json()
    )
    assert (
        c["t"]
        .post(
            path,
            json={"preview_id": "different"},
            headers={"Idempotency-Key": "import-1"},
        )
        .status_code
        == 409
    )
    with app.state.sessions() as db:
        user = db.scalar(select(User).where(User.username == "001"))
        old_hash = user.password_hash
        assert user.must_change_password and hasher.verify(old_hash, "02112005")
    preview = (
        c["t"]
        .post(
            f"/api/courses/{cid}/students/import-preview",
            files={"file": ("students.csv", data)},
        )
        .json()
    )
    assert preview["can_confirm"]
    assert (
        c["t"]
        .post(
            path,
            json={"preview_id": preview["preview_id"]},
            headers={"Idempotency-Key": "import-2"},
        )
        .status_code
        == 200
    )
    with app.state.sessions() as db:
        assert (
            db.scalar(select(User).where(User.username == "001")).password_hash
            == old_hash
        )


def test_csv_invalid_all_or_nothing(context):
    app, c, cid = context
    data = b"student_id,full_name,date_of_birth,class_name\n001,Good,02112005,C01\n001,Duplicate,31022005,C01\n"
    preview = (
        c["t"]
        .post(
            f"/api/courses/{cid}/students/import-preview",
            files={"file": ("students.csv", data)},
        )
        .json()
    )
    assert not preview["can_confirm"]
    assert (
        c["t"]
        .post(
            f"/api/courses/{cid}/students/import-confirm",
            json={"preview_id": preview["preview_id"]},
            headers={"Idempotency-Key": "bad"},
        )
        .status_code
        == 409
    )
    with app.state.sessions() as db:
        assert db.scalar(select(User).where(User.username == "001")) is None


def test_materials_upload_download_and_security(context):
    app, c, cid = context
    response = c["t"].post(
        f"/api/courses/{cid}/materials",
        data={"title": "Doc"},
        files={"file": ("../../private.txt", b"hello")},
    )
    assert response.status_code == 201, response.text
    mid = response.json()["id"]
    assert response.json()["original_filename"] == "private.txt"
    assert c["s"].get(f"/api/materials/{mid}/download").content == b"hello"
    assert c["outsider"].get(f"/api/materials/{mid}/download").status_code == 403
    assert (
        c["s"]
        .post(
            f"/api/courses/{cid}/materials",
            data={"title": "bad"},
            files={"file": ("bad.txt", b"bad")},
        )
        .status_code
        == 403
    )
    assert (
        c["t"]
        .post(
            f"/api/courses/{cid}/materials",
            data={"title": "bad"},
            files={"file": ("bad.exe", b"bad")},
        )
        .status_code
        == 400
    )


def assignment(c, cid, due=None, resubmit=True):
    result = c.post(
        f"/api/courses/{cid}/assignments",
        json={
            "title": "Homework",
            "description": "Do it",
            "due_at": (
                due or datetime.now(timezone.utc) + timedelta(hours=1)
            ).isoformat(),
            "allow_resubmit": resubmit,
        },
    )
    assert result.status_code == 201, result.text
    return result.json()["id"]


def test_assignment_history_grade_visibility_and_retry(context):
    app, c, cid = context
    aid = assignment(c["t"], cid)
    path = f"/api/assignments/{aid}/submissions"
    r = c["s"].post(
        path,
        files={"file": ("answer.txt", b"hello")},
        headers={"Idempotency-Key": "one"},
    )
    assert r.status_code == 201, r.text
    sid = r.json()["id"]
    assert (
        c["s"]
        .post(
            path,
            files={"file": ("answer.txt", b"hello")},
            headers={"Idempotency-Key": "one"},
        )
        .json()
        == r.json()
    )
    assert (
        c["s"]
        .post(
            path,
            files={"file": ("answer.txt", b"changed")},
            headers={"Idempotency-Key": "one"},
        )
        .status_code
        == 409
    )
    r2 = c["s"].post(
        path, files={"file": ("answer.txt", b"new")}, headers={"Idempotency-Key": "two"}
    )
    assert r2.status_code == 201
    assert r2.json()["id"] != sid
    assert (
        c["t"]
        .patch(
            f"/api/assignment-submissions/{sid}/grade",
            json={"score": 8, "feedback": "Nice"},
        )
        .status_code
        == 200
    )
    assert c["s"].get(path).json()["items"][-1]["score"] == 8
    assert (
        c["outsider"].get(f"/api/assignment-submissions/{sid}/download").status_code
        == 403
    )
    assert c["t"].get(f"/api/assignment-submissions/{sid}/download").content == b"hello"
    assert c["s"].get(path).json()["total"] == 2


def test_deadline_resubmit_and_limits(context):
    app, c, cid = context
    aid = assignment(c["t"], cid, datetime.now(timezone.utc) - timedelta(seconds=1))
    assert (
        c["s"]
        .post(
            f"/api/assignments/{aid}/submissions",
            files={"file": ("a.txt", b"a")},
            headers={"Idempotency-Key": "late"},
        )
        .json()["code"]
        == "DEADLINE_PASSED"
    )
    aid = assignment(c["t"], cid, resubmit=False)
    path = f"/api/assignments/{aid}/submissions"
    assert (
        c["s"]
        .post(path, files={"file": ("a.txt", b"a")}, headers={"Idempotency-Key": "ok"})
        .status_code
        == 201
    )
    assert (
        c["s"]
        .post(
            path, files={"file": ("a.txt", b"a")}, headers={"Idempotency-Key": "again"}
        )
        .json()["code"]
        == "RESUBMIT_DISABLED"
    )
    assert (
        c["s"]
        .post(
            path, files={"file": ("a.exe", b"a")}, headers={"Idempotency-Key": "type"}
        )
        .status_code
        == 400
    )
    assert (
        c["s"]
        .post(
            path,
            files={"file": ("a.txt", b"a" * (20 * 1024 * 1024 + 1))},
            headers={"Idempotency-Key": "huge"},
        )
        .status_code
        == 413
    )


def test_concurrent_same_key_exactly_once(context):
    app, c, cid = context
    aid = assignment(c["t"], cid)
    path = f"/api/assignments/{aid}/submissions"

    def submit(_):
        with TestClient(app) as client:
            client.cookies.update(c["s"].cookies)
            return client.post(
                path,
                headers={**c["s"].headers, "Idempotency-Key": "race"},
                files={"file": ("a.txt", b"answer")},
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(submit, range(2)))
    assert all(r.status_code == 201 for r in responses), [r.text for r in responses]
    assert responses[0].json()["id"] == responses[1].json()["id"]
    with app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(AssignmentSubmissions)) == 1


def test_upgrade_existing_database_preserves_data(tmp_path):
    import os,subprocess,sys
    from sqlalchemy import create_engine,text
    url=f'sqlite:///{tmp_path / "legacy.db"}'
    env=dict(os.environ,DATABASE_URL=url)
    def migrate(revision):
        p=subprocess.run([sys.executable,'-m','alembic','-c','server/alembic.ini','upgrade',revision],env=env,capture_output=True,text=True)
        assert p.returncode==0,p.stderr
    migrate('0002_database_base')
    engine=create_engine(url)
    with engine.begin() as db:
        db.execute(text("INSERT INTO users(id,username,password_hash,role,must_change_password,active) VALUES(1,'legacy','existing-hash','teacher',0,1)"))
        db.execute(text("INSERT INTO courses(id,course_code,course_name,semester,academic_year,status,grades_published,final_grade_policy) VALUES(1,'OLD','Old course','1','2026','active',0,'highest_published_final_exam')"))
        db.execute(text("INSERT INTO idempotency_keys(user_id,method,path,key,request_hash,status,expires_at) VALUES(1,'POST','/old','one','hash','completed',9999999999)"))
    engine.dispose();migrate('head')
    engine=create_engine(url)
    with engine.begin() as db:
        assert db.scalar(text('SELECT password_hash FROM users WHERE id=1'))=='existing-hash'
        assert db.scalar(text('SELECT final_grade_policy FROM courses WHERE id=1'))=='single_final_exam'
        db.execute(text("INSERT INTO idempotency_keys(user_id,method,path,key,request_hash,status,expires_at) VALUES(1,'POST','/old','two','hash','completed',9999999999)"))
        assert db.scalar(text('SELECT count(*) FROM idempotency_keys'))==2
        assert not db.execute(text('PRAGMA foreign_key_check')).fetchall()
    engine.dispose()
