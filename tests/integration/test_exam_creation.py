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


def test_create_missing_exam_and_report_duplicate_without_changing_existing(context):
    app,c,cid = context
    path = f"/api/courses/{cid}/coding-exams"
    assert c["s"].post(path,json=body("midterm")).status_code == 403
    assert c["other"].post(path,json=body("midterm")).status_code == 403
    created = []
    for component in ("midterm","final"):
        response = c["t"].post(path,json=body(component))
        assert response.status_code == 201, response.text
        created.append(response.json())
        duplicate = c["t"].post(path,json={**body(component),"title":"Không được thay thế đề cũ"})
        assert duplicate.status_code == 409
        assert duplicate.json()["code"] == "EXAM_COMPONENT_EXISTS"
        assert response.json()["title"] in duplicate.json()["detail"]
    rows = c["t"].get(path).json()["items"]
    assert [(r["id"],r["title"]) for r in rows] == [(r["id"],r["title"]) for r in created]
    with app.state.sessions() as db:
        assert db.scalar(select(func.count(CodingExams.id)).where(CodingExams.course_id==cid)) == 2


def test_two_teachers_requests_cannot_race_into_generic_database_error(context):
    _,c,cid = context
    def create(_):
        return c["t"].post(f"/api/courses/{cid}/coding-exams",json=body("final"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(create, range(2)))
    assert sorted(r.status_code for r in responses) == [201,409]
    conflict = next(r for r in responses if r.status_code==409)
    assert conflict.json()["code"]=="EXAM_COMPONENT_EXISTS"
