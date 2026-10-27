"""Homework matrix uses the same score calculation as the course gradebook."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select
from ...core.database import get_db
from ...core.security import learning_user, fail
from ...models import Assignments, AssignmentGrades, Students, CourseEnrollments
from ...services import access, idempotency
from ...services.activity import audit, emit
from ..gradebook.service import assignment_score, scores, round_score

router = APIRouter(tags=["assignments"])

class Cell(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")
    student_id: str
    assignment_id: int
    score: float | None = Field(default=None, ge=0, le=10)

class Changes(BaseModel):
    items: list[Cell] = Field(min_length=1, max_length=2000)

@router.get("/courses/{cid}/assignments/progress")
def progress(cid: int, db=Depends(get_db), user=Depends(learning_user)):
    access.course(db, user, cid)
    assignments = list(db.scalars(select(Assignments).where(Assignments.course_id==cid).order_by(Assignments.id)))
    query = select(Students).join(CourseEnrollments).where(CourseEnrollments.course_id==cid, CourseEnrollments.status=="active")
    if user.role == "student": query = query.where(Students.user_id==user.user_id)
    return {"assignments": [{"id":a.id,"title":a.title} for a in assignments], "items": [
        {"student_id":s.student_code,"full_name":s.full_name,
         "scores":{str(a.id):round_score(assignment_score(db,a,s.id)) for a in assignments},
         "average":round_score(scores(db,cid,s.id)["homework"])}
        for s in db.scalars(query.order_by(Students.student_code))]}

@router.patch("/courses/{cid}/assignments/progress")
def update(cid: int, body: Changes, db=Depends(get_db), user=Depends(learning_user)):
    idempotency.write_lock(db)
    course = access.course(db,user,cid,True)
    teacher = access.teacher(db,user)
    seen = set()
    for item in body.items:
        key = (item.assignment_id,item.student_id)
        if key in seen: fail(422,"DUPLICATE_ENTRY","Trùng ô điểm")
        seen.add(key)
        assignment = db.get(Assignments,item.assignment_id)
        student = db.scalar(select(Students).join(CourseEnrollments).where(
            Students.student_code==item.student_id,CourseEnrollments.course_id==cid,CourseEnrollments.status=="active"))
        if not assignment or assignment.course_id!=cid or not student:
            fail(404,"NOT_FOUND","Bài tập hoặc sinh viên không thuộc khóa học")
        row = db.scalar(select(AssignmentGrades).where(AssignmentGrades.assignment_id==assignment.id,AssignmentGrades.student_id==student.id))
        if item.score is None:
            if row: db.delete(row)
        else:
            if not row:
                row=AssignmentGrades(assignment_id=assignment.id,student_id=student.id,graded_by=teacher.id,score=item.score);db.add(row)
            row.score=item.score;row.graded_by=teacher.id
        audit(db,user.user_id,"homework-grade","assignment",assignment.id,item.model_dump())
    course.grades_published=False
    emit(db,"grade.updated",cid,{"course_id":cid})
    db.commit()
    return {"updated_count":len(body.items)}
