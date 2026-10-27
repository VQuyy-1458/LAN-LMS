from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select, func
from ...core.database import get_db
from ...core.security import learning_user, fail
from ...models import CalendarEvents, AttendanceSessions
from ...schemas.common import Pagination
from ...services import access
from ...services.activity import iso, audit

router = APIRouter(prefix="/api", tags=["calendar"])


class EventInput(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    event_type: Literal["lesson", "exam", "deadline", "announcement"] = "lesson"
    starts_at: datetime
    ends_at: datetime

    @model_validator(mode="after")
    def dates(self):
        if (
            not self.starts_at.tzinfo
            or not self.ends_at.tzinfo
            or self.ends_at < self.starts_at
        ):
            raise ValueError("Thời gian cần múi giờ, kết thúc không trước bắt đầu")
        return self


def payload(row):
    return dict(
        id=row.id,
        course_id=row.course_id,
        title=row.title,
        description=row.description,
        event_type=row.event_type,
        starts_at=iso(row.starts_at),
        ends_at=iso(row.ends_at),
    )


@router.get("/courses/{course_id}/events")
def events(
    course_id: int,
    db=Depends(get_db),
    user=Depends(learning_user),
    p=Depends(Pagination),
):
    access.course(db, user, course_id)
    q = select(CalendarEvents).where(CalendarEvents.course_id == course_id)
    return p.response(
        [
            payload(x)
            for x in db.scalars(
                q.order_by(CalendarEvents.starts_at).offset(p.offset).limit(p.page_size)
            )
        ],
        db.scalar(select(func.count()).select_from(q.subquery())),
    )


@router.post("/courses/{course_id}/events", status_code=201)
def create(
    course_id: int, body: EventInput, db=Depends(get_db), user=Depends(learning_user)
):
    access.course(db, user, course_id, True)
    row = CalendarEvents(
        course_id=course_id,
        created_by=user.user_id,
        title=body.title,
        description=body.description,
        event_type=body.event_type,
        starts_at=body.starts_at.timestamp(),
        ends_at=body.ends_at.timestamp(),
    )
    db.add(row)
    db.flush()
    audit(db, user.user_id, "create", "event", row.id)
    db.commit()
    return payload(row)


@router.put("/events/{event_id}")
def update(
    event_id: int, body: EventInput, db=Depends(get_db), user=Depends(learning_user)
):
    row = db.get(CalendarEvents, event_id)
    if not row:
        fail(404, "NOT_FOUND", "Không tìm thấy sự kiện")
    access.course(db, user, row.course_id, True)
    for k, v in body.model_dump().items():
        setattr(row, k, v.timestamp() if isinstance(v, datetime) else v)
    audit(db, user.user_id, "update", "event", row.id)
    db.commit()
    return payload(row)


@router.delete("/events/{event_id}", status_code=204)
def delete(event_id: int, db=Depends(get_db), user=Depends(learning_user)):
    row = db.get(CalendarEvents, event_id)
    if not row:
        fail(404, "NOT_FOUND", "Không tìm thấy sự kiện")
    access.course(db, user, row.course_id, True)
    if db.scalar(select(AttendanceSessions.id).where(AttendanceSessions.event_id==event_id)):
        fail(409,"LESSON_HAS_ATTENDANCE","Buổi học đã có điểm danh; hãy giữ lịch để bảo toàn kết quả")
    audit(db, user.user_id, "delete", "event", row.id)
    db.delete(row)
    db.commit()
    return Response(status_code=204)
