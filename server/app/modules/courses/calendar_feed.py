"""Derived exam/deadline events cannot drift from their source records."""
import time
from sqlalchemy import select
from ...models import CalendarEvents,AttendanceSessions,CodingExams,Assignments
from ...services.activity import iso

def feed(db,cid,user):
    result=[]
    attendance={s.event_id:s for s in db.scalars(select(AttendanceSessions).where(AttendanceSessions.course_id==cid)) if s.event_id}
    for row in db.scalars(select(CalendarEvents).where(CalendarEvents.course_id==cid,CalendarEvents.event_type.in_(["lesson","announcement"]))):
        session=attendance.get(row.id)
        result.append(dict(id=row.id,course_id=cid,title=row.title,description=row.description,event_type=row.event_type,
            starts_at=iso(row.starts_at),ends_at=iso(row.ends_at),editable=True,source_id=row.id,
            attendance_state=("closed" if session.status=="closed" or session.expires_at<=time.time() else "open") if session else None))
    for row in db.scalars(select(CodingExams).where(CodingExams.course_id==cid)):
        if user.role=="student" and row.status=="draft":continue
        result.append(dict(id=-row.id*2,course_id=cid,title=row.title,description="Lịch thi tự đồng bộ từ đề lập trình.",event_type="exam",
            starts_at=iso(row.starts_at),ends_at=iso(row.ends_at),editable=False,source_id=row.id))
    for row in db.scalars(select(Assignments).where(Assignments.course_id==cid)):
        result.append(dict(id=-row.id*2-1,course_id=cid,title=row.title,description="Hạn nộp tự đồng bộ từ bài tập.",event_type="deadline",
            starts_at=iso(row.due_at),ends_at=iso(row.due_at),editable=False,source_id=row.id))
    return sorted(result,key=lambda e:(e["starts_at"],e["id"]))
