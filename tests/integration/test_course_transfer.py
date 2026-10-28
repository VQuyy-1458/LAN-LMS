import io
import json
import time
import zipfile
from sqlalchemy import select
from test_day25 import context
from test_completion import prepare_exam, submit
from server.app.models import Courses, Students, User, ExamSessions, JudgeJobs, Problems, CourseEnrollments


def upload(client, data, code="COPY", key="copy"):
    return client.post("/api/courses/import-package", files={"file":("course.zip",data)},
                       data={"course_code":code},headers={"Idempotency-Key":key})


def test_course_roundtrip_scope_files_scores_pending_and_accounts(context):
    app, clients, cid = context
    teacher, student = clients["t"], clients["s"]
    material = teacher.post(f"/api/courses/{cid}/materials", data={"title":"Slide"},files={"file":("slides.ppt",b"example slides")})
    assert material.status_code == 201
    eid, pids, sid = prepare_exam(app, clients, cid)
    assert submit(clients, pids[0], sid).status_code == 202
    assert student.post(f"/api/exam-sessions/{sid}/events",json={"event_key":"blur-1","event_type":"tab_hidden"}).status_code == 201
    package = teacher.get(f"/api/courses/{cid}/export-package")
    assert package.status_code == 200, package.text[:200] if package.status_code != 200 else ""
    assert student.get(f"/api/courses/{cid}/export-package").status_code == 403
    assert clients["other"].get(f"/api/courses/{cid}/export-package").status_code == 403
    with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
        tables = json.loads(archive.read("manifest.json"))["tables"]
        assert len(tables["users"]) == 1 and tables["users"][0]["username"] == "s"
        assert "auth_sessions" not in tables
    preview = teacher.post("/api/courses/import-package/preview",files={"file":("course.zip",package.content)})
    assert preview.status_code == 200, preview.text
    assert preview.json()["counts"]["code_submissions"] == 1
    assert upload(student,package.content).status_code == 403
    with app.state.sessions() as db:
        old_hash = db.scalar(select(User).where(User.username == "s")).password_hash
    result = upload(teacher,package.content)
    assert result.status_code == 201, result.text
    copied = result.json()["id"]
    assert copied != cid
    assert upload(teacher,package.content).json() == result.json()
    assert upload(teacher,package.content,key="different").status_code == 409
    assert clients["other"].get(f"/api/courses/{copied}").status_code == 403
    copied_material = student.get(f"/api/courses/{copied}/materials").json()["items"][0]
    assert student.get(f"/api/materials/{copied_material['id']}/download").content == b"example slides"
    new_exam = teacher.get(f"/api/courses/{copied}/coding-exams").json()["items"][0]
    sessions = teacher.get(f"/api/coding-exams/{new_exam['id']}/sessions").json()["items"]
    assert sessions[0]["focus_event_count"] == 1
    with app.state.sessions() as db:
        assert db.scalar(select(User).where(User.username == "s")).password_hash == old_hash
        new_session = db.get(ExamSessions,sessions[0]["id"])
        assert new_session.id != sid
        assert db.scalar(select(JudgeJobs).order_by(JudgeJobs.id.desc())).status == "pending"
        assert len(list(db.scalars(select(CourseEnrollments).where(CourseEnrollments.course_id == copied)))) == 1


def test_import_failure_rolls_back_and_rejects_tampered_zip(context):
    app, clients, cid = context
    teacher = clients["t"]
    material = teacher.post(f"/api/courses/{cid}/materials",data={"title":"Doc"},files={"file":("a.doc",b"original")})
    assert material.status_code == 201
    package = teacher.get(f"/api/courses/{cid}/export-package").content
    def rewrite(mutate):
        out = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(package)) as source, zipfile.ZipFile(out,"w") as target:
            for name in source.namelist(): target.writestr(name,mutate(name,source.read(name)))
        return out.getvalue()
    bad = rewrite(lambda name,data: b"modified" if name.startswith("blobs/") else data)
    assert upload(teacher,bad).status_code == 422
    assert teacher.get("/api/courses").json()["total"] == 1
    with app.state.sessions.begin() as db:
        db.scalar(select(Students).where(Students.student_code == "s")).full_name = "Changed locally"
    assert upload(teacher,package).status_code == 409
    assert teacher.get("/api/courses").json()["total"] == 1
    assert not list((app.state.storage_root / "course_imports").glob("*"))
