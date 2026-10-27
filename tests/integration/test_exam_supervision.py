from sqlalchemy import select
from test_day25 import context
from test_completion import prepare_exam, submit
from judge import job_queue
from judge.runners.container import Result
from server.app.models import CodingExams, Students
from server.app.modules.gradebook.service import exam_score


def test_early_finish_updates_grade_and_focus_events_are_scoped(context):
    app, clients, cid = context
    eid, pids, sid = prepare_exam(app, clients, cid)
    event = {"event_key":"tab-1","event_type":"tab_hidden"}
    path = f"/api/exam-sessions/{sid}/events"
    first = clients["s"].post(path,json=event)
    assert first.status_code == 201, first.text
    assert clients["s"].post(path,json=event).json() == first.json()
    assert clients["outsider"].post(path,json=event).status_code == 403
    assert clients["t"].post(path,json={**event,"event_key":"fake"}).status_code == 403
    assert clients["s"].get(path).status_code == 403
    events = clients["t"].get(path).json()
    assert events["total"] == 1 and events["items"][0]["event_type"] == "tab_hidden"
    assert clients["t"].get(f"/api/exam-sessions/{sid}").json()["started_ip"]
    assert submit(clients,pids[0],sid).status_code == 202
    assert clients["s"].post(f"/api/exam-sessions/{sid}/finish").status_code == 200
    before = clients["s"].get(f"/api/courses/{cid}/gradebook").json()["items"][0]
    assert before["final_score"] is None
    claim = job_queue.claim(app.state.sessions,"test")
    job_queue.complete(app.state.sessions,claim,Result("Accepted",100,100),1,1)
    after = clients["s"].get(f"/api/courses/{cid}/gradebook").json()["items"][0]
    assert after["final_score"] == 10
    assert after["total_score"] is None
    assert submit(clients,pids[0],sid,key="late").status_code == 409
    assert clients["s"].post(path,json={**event,"event_key":"late"}).status_code == 409
    assert clients["s"].post(f"/api/exam-sessions/{sid}/finish").json()["status"] == "finished"


def test_selected_midterms_average_and_practice_excluded(context):
    app, clients, cid = context
    # Reclassify each completed final fixture to create the next exam independently.
    for component, accepted in [("midterm",True),("midterm",False),("practice",True)]:
        eid,pids,sid = prepare_exam(app,clients,cid)
        assert submit(clients,pids[0],sid,key=str(eid)).status_code == 202
        claim=job_queue.claim(app.state.sessions,"test")
        job_queue.complete(app.state.sessions,claim,Result("Accepted" if accepted else "Wrong Answer",100 if accepted else 0,100),1,1)
        clients["s"].post(f"/api/exam-sessions/{sid}/finish")
        with app.state.sessions.begin() as db:
            db.get(CodingExams,eid).grade_component=component
    with app.state.sessions() as db:
        student=db.scalar(select(Students).where(Students.student_code=="s"))
        assert exam_score(db,cid,student.id,"midterm") == 5
        assert exam_score(db,cid,student.id,"final") is None
