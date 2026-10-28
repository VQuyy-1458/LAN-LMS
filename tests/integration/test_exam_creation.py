import concurrent.futures
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from test_day25 import context
from server.app.models import CodingExams


def body(component):
    now = datetime.now(timezone.utc)
    return {"title": "Đề mới " + component, "grade_component": component,
            "starts_at": (now+timedelta(hours=1)).isoformat(),
            "ends_at": (now+timedelta(hours=3)).isoformat()}


def test_multiple_midterms_and_practice_only_one_final(context):
    app,c,cid = context
    path = f"/api/courses/{cid}/coding-exams"
    assert c["s"].post(path,json=body("midterm")).status_code == 403
    assert c["other"].post(path,json=body("midterm")).status_code == 403
    for component in ("midterm", "midterm", "practice", "practice", "final"):
        response = c["t"].post(path,json=body(component))
        assert response.status_code == 201, response.text
    duplicate = c["t"].post(path,json=body("final"))
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "EXAM_COMPONENT_EXISTS"
    assert c["t"].get(path).json()["total"] == 5
    # Teacher can reclassify a draft; a second final is rejected atomically.
    rows = c["t"].get(path).json()["items"]
    assert c["t"].patch(f"/api/coding-exams/{rows[0]['id']}",json={"grade_component":"final"}).status_code == 409
    assert c["t"].patch(f"/api/coding-exams/{rows[-1]['id']}",json={"grade_component":"practice"}).status_code == 200
    assert c["t"].patch(f"/api/coding-exams/{rows[0]['id']}",json={"grade_component":"final"}).status_code == 200


def test_two_teachers_requests_cannot_race_into_generic_database_error(context):
    _,c,cid = context
    def create(_):
        return c["t"].post(f"/api/courses/{cid}/coding-exams",json=body("final"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(create, range(2)))
    assert sorted(r.status_code for r in responses) == [201,409]
    conflict = next(r for r in responses if r.status_code==409)
    assert conflict.json()["code"]=="EXAM_COMPONENT_EXISTS"


def test_more_than_twenty_questions_and_ladder_entries(context):
    _, c, cid = context
    response = c["t"].post(f"/api/courses/{cid}/coding-exams", json={**body("practice"),"score_ladder":[i/3 for i in range(31)]})
    assert response.status_code == 201, response.text
    eid = response.json()["id"]
    for index in range(30):
        result = c["t"].post(f"/api/coding-exams/{eid}/problems",json={"title":str(index),"statement":"sum"})
        assert result.status_code == 201, result.text
    assert c["t"].get(f"/api/coding-exams/{eid}/problems").json()["total"] == 30
