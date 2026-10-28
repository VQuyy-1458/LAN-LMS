import time
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from ...core.database import get_db
from ...core.security import learning_user
from ...models import (CourseEnrollments, CourseMaterials, Assignments, AssignmentSubmissions, CodingExams, CalendarEvents)
from ...services import access
from ...services.activity import iso

router=APIRouter(prefix="/api",tags=["courses"])


@router.get("/courses/{cid}/overview")
def overview(cid: int,db=Depends(get_db),user=Depends(learning_user)):
    access.course(db,user,cid)
    def count(model, *conditions):
        return db.scalar(select(func.count(model.id)).where(*conditions))
    student=access.student(db,user) if user.role=="student" else None
    exam_filter=[CodingExams.course_id==cid]
    if student: exam_filter.append(CodingExams.status!="draft")
    assignment_query=select(AssignmentSubmissions).join(Assignments).where(Assignments.course_id==cid)
    if student: assignment_query=assignment_query.where(AssignmentSubmissions.student_id==student.id)
    submitted=len(set(row.assignment_id for row in db.scalars(assignment_query))) if student else None
    pending=count(AssignmentSubmissions,AssignmentSubmissions.assignment_id.in_(select(Assignments.id).where(Assignments.course_id==cid)),AssignmentSubmissions.score==None) if not student else None
    return {
        "students":count(CourseEnrollments,CourseEnrollments.course_id==cid,CourseEnrollments.status=="active"),
        "materials":count(CourseMaterials,CourseMaterials.course_id==cid),
        "assignments":count(Assignments,Assignments.course_id==cid),
        "exams":count(CodingExams,*exam_filter),"submitted_assignments":submitted,"awaiting_grades":pending,
        "upcoming":[{"id":row.id,"title":row.title,"starts_at":iso(row.starts_at),"event_type":row.event_type}
            for row in db.scalars(select(CalendarEvents).where(CalendarEvents.course_id==cid,CalendarEvents.ends_at>=time.time(),CalendarEvents.event_type!="announcement").order_by(CalendarEvents.starts_at).limit(4))],
    }
