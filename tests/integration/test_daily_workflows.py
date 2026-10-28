from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from test_day25 import context
from server.app.models import AttendanceSessions, AttendanceRecords, CourseEnrollments, Students
from server.app.services.notifications import read_events


def test_qr_is_bound_to_lesson_and_teacher_gets_present_update(context):
    app,clients,cid=context
    event=clients["t"].post(f"/api/courses/{cid}/events",json={"title":"Buổi thực hành TCP","starts_at":"2026-10-27T08:00:00+07:00","ends_at":"2026-10-27T10:00:00+07:00"}).json()
    first=clients["t"].post(f"/api/courses/{cid}/attendance-sessions",json={"event_id":event["id"]}).json()
    assert first["event_id"]==event["id"] and first["title"]==event["title"]
    path=f"/api/attendance-sessions/{first['id']}/check-in"
    response=clients["s"].post(path,json={"token":first["token"]})
    assert response.status_code==201 and response.json()["status"]=="present"
    events=read_events(app.state.sessions,0)
    event_row=next(row for row in events if row[1]=="attendance.updated")
    with app.state.sessions() as db:
        from server.app.core.database import User
        teacher=db.scalar(select(User).where(User.username=="t"))
        other=db.scalar(select(User).where(User.username=="other"))
        student=db.scalar(select(User).where(User.username=="s"))
        assert teacher.id in event_row[3] and student.id in event_row[3] and other.id not in event_row[3]
    second=clients["t"].post(f"/api/courses/{cid}/attendance-sessions",json={"event_id":event["id"]}).json()
    assert second["id"]==first["id"] and second["token"]!=first["token"]
    assert clients["s"].post(path,json={"token":first["token"]}).status_code==403
    assert clients["s"].post(path,json={"token":second["token"]}).json()["status"]=="present"
    roster=clients["t"].get(f"/api/attendance-sessions/{first['id']}/roster").json()["items"]
    assert roster[0]["status"]=="present"
    assert clients["t"].delete(f"/api/events/{event['id']}").status_code==409
    with app.state.sessions() as db:
        assert db.scalar(select(func.count(AttendanceSessions.id)).where(AttendanceSessions.event_id==event["id"]))==1
        assert db.scalar(select(func.count(AttendanceRecords.id)).where(AttendanceRecords.session_id==first["id"]))==1


def test_assignment_filters_use_own_submission_and_count_before_paging(context):
    app,clients,cid=context
    now=datetime.now(timezone.utc)
    with app.state.sessions.begin() as db:
        other=db.scalar(select(Students).where(Students.student_code=="outsider"))
        db.add(CourseEnrollments(course_id=cid,student_id=other.id,status="active"))
    ids=[]
    for index in range(4):
        response=clients["t"].post(f"/api/courses/{cid}/assignments",json={"title":f"Bài {index}","due_at":(now+timedelta(days=1) if index!=2 else now-timedelta(days=1)).isoformat()})
        assert response.status_code==201,response.text
        ids.append(response.json()["id"])
    for who,aid in [("s",ids[1]),("outsider",ids[3])]:
        response=clients[who].post(f"/api/assignments/{aid}/submissions",files={"file":("answer.txt",b"answer")},headers={"Idempotency-Key":"answer"})
        assert response.status_code==201,response.text
    path=f"/api/courses/{cid}/assignments"
    result=clients["s"].get(path+"?page_size=1").json()
    assert result["counts"]=={"all":4,"not_submitted":2,"submitted":1,"overdue":1}
    assert result["total"]==4 and len(result["items"])==1
    assert clients["s"].get(path+"?status=submitted").json()["items"][0]["id"]==ids[1]
    assert clients["s"].get(path+"?status=overdue").json()["items"][0]["id"]==ids[2]
    assert clients["t"].get(path).json()["counts"]=={"all":4,"not_submitted":3,"submitted":0,"overdue":1,"within":3}
    assert clients["s"].get(path+"?status=invalid").status_code==422


def test_classroom_identity_refresh_preserves_student_records(context,tmp_path):
    import csv
    from scripts.seed_classroom import seed
    from scripts.refresh_classroom import refresh
    from server.app.core.database import User, AuthSession
    from server.app.core.security import verify
    app,clients,cid=context
    output=tmp_path/"accounts"
    seeded=seed(app.state.sessions,app.state.storage_root,"t",output)
    path=output/"accounts.csv"
    with path.open(encoding="utf-8-sig",newline="") as stream:rows=list(csv.DictReader(stream))
    rows[0]["student_id"]="DEMO-NET-001"
    with path.open("w",encoding="utf-8-sig",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    with app.state.sessions.begin() as db:
        student=db.scalar(select(Students).where(Students.student_code=="B26DCCN001"));sid=student.id
        student.student_code="DEMO-NET-001"
        user=db.get(User,student.user_id);user.username="DEMO-NET-001"
        db.add(AuthSession(token_hash="reset-test",user_id=user.id,csrf_hash="x",expires_at=9999999999))
    result=refresh(app.state.sessions,app.state.storage_root,output,rename_students=True)
    assert result["accounts_updated"]==40
    with app.state.sessions() as db:
        student=db.get(Students,sid)
        assert student.student_code=="B26DCCN001" and student.date_of_birth=="01012006"
        user=db.get(User,student.user_id)
        assert user.username==student.student_code and user.must_change_password
        assert verify(user.password_hash,"01012006")
        assert db.get(AuthSession,"reset-test") is None
        assert db.scalar(select(func.count(CourseEnrollments.id)).where(CourseEnrollments.student_id==sid))==1
    course=seeded["courses"][0]["id"]
    response=clients["t"].get(f"/api/courses/{course}/students")
    assert response.json()["items"][0]["date_of_birth"]=="01012006"
    assert clients["s"].get(f"/api/courses/{course}/students").status_code==403
