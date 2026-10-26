import json
import os
import time
import pytest
from sqlalchemy import select, func
from test_day25 import context
from scripts.seed_network_lab import seed_lab
from server.app.models import CodingExams, Problems, TestCases as CaseModel, RealtimeEvents
from demo.network_exam import problems
from judge.health import write, status
from judge import job_queue
from judge.worker import execute


def test_seed_is_complete_private_and_idempotent(context):
    app,c,old_cid = context
    root = app.state.storage_root
    seeded = seed_lab(app.state.sessions, root, "t", ["s"])
    cid = seeded["course_id"]
    assert seeded["created"] and seeded["test_cases"] == 62
    again = seed_lab(app.state.sessions, root, "t", ["s"])
    assert not again["created"] and again["course_id"] == cid
    assert c["outsider"].get(f"/api/courses/{cid}").status_code == 403
    assert c["s"].get(f"/api/courses/{old_cid}").status_code == 200
    exams = c["s"].get(f"/api/courses/{cid}/coding-exams").json()["items"]
    assert len(exams) == 2 and all(e["problem_count"] == 5 and e["status"] == "open" for e in exams)
    for exam in exams:
        rows = c["s"].get(f'/api/coding-exams/{exam["id"]}/problems').json()["items"]
        assert len(rows) == 5
        assert all("INPUT" in r["statement"] and "OUTPUT" in r["statement"] for r in rows)
        assert all("solution" not in r for r in rows)
        assert c["s"].get(f'/api/problems/{rows[0]["id"]}/test-cases').status_code == 403
    assert c["t"].get(f"/api/courses/{cid}/students").json()["total"] == 1
    with app.state.sessions() as db:
        assert db.scalar(select(func.count(CaseModel.id))) == 62


def test_judge_presence_is_fresh_and_scoped_to_database(context):
    app,c,cid = context
    path = f"/api/courses/{cid}/judge-status"
    assert c["s"].get(path).json()["ready"] is False
    write(app.state.storage_root,"test-worker",app.state.settings.database_url,True,"test-image")
    assert c["s"].get(path).json()["workers"] == 1
    assert c["outsider"].get(path).status_code == 403
    assert status(app.state.storage_root,"sqlite:///another.db") == 0
    file = next((app.state.storage_root/".worker-health").glob("*.json"))
    data = json.loads(file.read_text()); data["updated_at"]=time.time()-31
    file.write_text(json.dumps(data))
    assert c["s"].get(path).json()["ready"] is False


@pytest.mark.skipif(os.getenv("RUN_DOCKER_TESTS") != "1", reason="Real Docker required")
def test_network_final_http_queue_docker_and_score_ladder(context):
    app,c,_ = context
    seeded = seed_lab(app.state.sessions, app.state.storage_root, "t", ["s"])
    final = next(e for e in seeded["exams"] if e["component"] == "final")
    eid = final["id"]
    session = c["s"].post(f"/api/coding-exams/{eid}/sessions/start").json()
    with app.state.sessions() as db:
        rows = list(db.scalars(select(Problems).where(Problems.exam_id==eid).order_by(Problems.id)))
        ids = [p.id for p in rows]
    specs = problems()["final"]
    for index,(pid,spec) in enumerate(zip(ids,specs)):
        r = c["s"].post(f"/api/problems/{pid}/submissions", json={"exam_session_id":session["id"],"language":"cpp","source_code":spec.solution}, headers={"Idempotency-Key":f"network-{index}"})
        assert r.status_code == 202, r.text
        claim = job_queue.claim(app.state.sessions,"network-acceptance")
        assert claim is not None
        execute(app.state.sessions,app.state.storage_root,claim)
        result = c["s"].get(f'/api/submissions/{r.json()["id"]}').json()
        assert result["verdict_code"] == "AC", result
        assert result["score"] == 100
        snapshot = c["s"].get(f'/api/exam-sessions/{session["id"]}').json()
        assert snapshot["accepted_count"] == index+1
        assert snapshot["total_score"] == [5,7,8,9,10][index]
    with app.state.sessions() as db:
        assert db.scalar(select(func.count(RealtimeEvents.id)).where(RealtimeEvents.event_type=="submission.updated")) >= 15
