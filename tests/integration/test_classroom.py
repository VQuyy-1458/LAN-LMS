import csv
import io
import json
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from sqlalchemy import select, func
from test_day25 import context
from scripts.seed_classroom import seed
from server.app.core.database import User
from server.app.core.security import verify
from server.app.models import CodingExams, CourseEnrollments, Students, Problems, TestCases as Case, Assignments


def test_two_classrooms_are_complete_idempotent_and_preserve_old_users(context,tmp_path):
    app,clients,old_course=context
    with app.state.sessions() as db:
        old_hash=db.scalar(select(User).where(User.username=="s")).password_hash
    output=tmp_path/"classroom"
    first=seed(app.state.sessions,app.state.storage_root,"t",output)
    assert first["new_students"]==40 and len(first["courses"])==2
    credentials=(output/"accounts.csv").read_bytes()
    second=seed(app.state.sessions,app.state.storage_root,"t",output)
    assert second["new_students"]==0
    assert (output/"accounts.csv").read_bytes()==credentials
    with app.state.sessions() as db:
        assert db.scalar(select(User).where(User.username=="s")).password_hash==old_hash
        for course in first["courses"]:
            cid=course["id"]
            assert db.scalar(select(func.count(CourseEnrollments.id)).where(CourseEnrollments.course_id==cid))==20
            exams=list(db.scalars(select(CodingExams).where(CodingExams.course_id==cid)))
            assert sorted(x.grade_component for x in exams)==["final","midterm","midterm","practice"]
            assert clients["t"].get(f"/api/courses/{cid}/materials").json()["total"]==3
            overview=clients["t"].get(f"/api/courses/{cid}/overview").json()
            assert overview["students"]==20 and overview["materials"]==3 and overview["exams"]==4
            assert overview["awaiting_grades"]==7
            assert clients["outsider"].get(f"/api/courses/{cid}/overview").status_code==403
            assert clients["t"].get(f"/api/courses/{cid}/events").json()["total"]==26
            assert clients["outsider"].get(f"/api/courses/{cid}").status_code==403
            assignments=list(db.scalars(select(Assignments).where(Assignments.course_id==cid)))
            assert len(assignments)==6 and all(x.attachment_path for x in assignments)
        rows=list(csv.DictReader(io.StringIO(credentials.decode("utf-8-sig"))))
        assert len(rows)==40
        for row in rows:
            user=db.scalar(select(User).where(User.username==row["student_id"]))
            assert user.must_change_password and verify(user.password_hash,row["temporary_password"])
    assert clients["s"].get(f"/api/courses/{old_course}").status_code==200
    with zipfile.ZipFile(output/"teacher-question-bank.zip") as archive:
        assert len([x for x in archive.namelist() if x.endswith("reference.cpp")])==20


def draft_problem(clients,cid):
    now=datetime.now(timezone.utc)
    exam=clients["t"].post(f"/api/courses/{cid}/coding-exams",json={"title":"Test ZIP","starts_at":(now+timedelta(hours=1)).isoformat(),
        "ends_at":(now+timedelta(hours=2)).isoformat(),"grade_component":"practice","score_ladder":[0,10]}).json()
    return clients["t"].post(f"/api/coding-exams/{exam['id']}/problems",json={"title":"Sum","statement":"Sum two numbers"}).json(),exam


def test_bulk_tests_sample_visibility_and_private_downloads(context):
    app,clients,cid=context
    problem,exam=draft_problem(clients,cid);pid=problem["id"]
    output=io.BytesIO()
    with zipfile.ZipFile(output,"w") as z:
        for name,content in [("sample_01.in","1 2\n"),("sample_01.out","3\n"),("02.in","40 2\n"),("02.out","42\n")]: z.writestr(name,content)
    path=f"/api/problems/{pid}/test-cases/import-zip"
    def upload(who,key="zip"):
        return clients[who].post(path,files={"file":("tests.zip",output.getvalue())},headers={"Idempotency-Key":key})
    assert upload("s").status_code==403
    response=upload("t");assert response.status_code==201,response.text
    assert response.json()=={"count":2,"total_weight":100}
    assert upload("t").json()==response.json()
    assert upload("t","new-key").status_code==409
    rows=clients["t"].get(f"/api/problems/{pid}/test-cases").json()["items"]
    assert len(rows)==2 and sum(r["points"] for r in rows)==100
    assert clients["s"].get(f"/api/problems/{pid}/examples").status_code==403
    with app.state.sessions.begin() as db:
        row=db.get(CodingExams,exam["id"]);row.status="scheduled";row.starts_at=0
    examples=clients["s"].get(f"/api/problems/{pid}/examples").json()["items"]
    assert examples==[{"input":"1 2\n","output":"3\n","truncated":False}]
    hidden=next(r for r in rows if r["is_hidden"])
    assert clients["s"].get(f"/api/test-cases/{hidden['id']}/file?kind=output").status_code==403
    assert clients["t"].get(f"/api/test-cases/{hidden['id']}/file?kind=output").content==b"42\n"
    bad=io.BytesIO()
    with zipfile.ZipFile(bad,"w") as z:z.writestr("../escape.in","x")
    assert clients["t"].post(path,files={"file":("bad.zip",bad.getvalue())},headers={"Idempotency-Key":"bad"}).status_code==422


def test_teacher_assignment_file_and_course_transfer(context):
    app,clients,cid=context
    response=clients["t"].post(f"/api/courses/{cid}/assignments",json={"title":"Report","due_at":"2030-01-01T10:00:00+07:00"})
    aid=response.json()["id"]
    path=f"/api/assignments/{aid}/attachment"
    assert clients["s"].post(path,files={"file":("report.txt",b"handout")}).status_code==403
    assert clients["t"].post(path,files={"file":("report.txt",b"handout")}).status_code==200
    assert clients["s"].get(path).content==b"handout"
    assert clients["outsider"].get(path).status_code==403
    package=clients["t"].get(f"/api/courses/{cid}/export-package").content
    result=clients["t"].post("/api/courses/import-package",files={"file":("course.zip",package)},data={"course_code":"COPY-HANDOUT"},headers={"Idempotency-Key":"handout-copy"})
    assert result.status_code==201,result.text
    copied=clients["t"].get(f"/api/courses/{result.json()['id']}/assignments").json()["items"][0]
    assert clients["s"].get(f"/api/assignments/{copied['id']}/attachment").content==b"handout"
