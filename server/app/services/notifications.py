"""Bridge durable worker events to one API process; clients recover snapshots using REST."""

import asyncio
import json
import logging
import time
from sqlalchemy import select, func, delete
from ..models import (
    RealtimeEvents,
    CourseTeachers,
    Teachers,
    CourseEnrollments,
    Students,
    ExamSessions,
    ExamRegistrations,
    CodingExams,
    Courses,
)
from .activity import emit

logger = logging.getLogger("lan_lms.notifications")


def read_events(sessions, cursor):
    with sessions() as db:
        rows = list(
            db.scalars(
                select(RealtimeEvents)
                .where(RealtimeEvents.id > cursor)
                .order_by(RealtimeEvents.id)
                .limit(200)
            )
        )
        result = []
        for r in rows:
            recipients = set(
                db.scalars(
                    select(Teachers.user_id)
                    .join(CourseTeachers)
                    .where(CourseTeachers.course_id == r.course_id)
                )
            )
            members = set(
                db.scalars(
                    select(Students.user_id)
                    .join(CourseEnrollments)
                    .where(
                        CourseEnrollments.course_id == r.course_id,
                        CourseEnrollments.status == "active",
                    )
                )
            )
            recipients.update(members if r.owner_id is None else {r.owner_id} & members)
            result.append((r.id, r.event_type, json.loads(r.data_json), recipients))
        return result


def maintain(sessions):
    with sessions() as db:
        now = time.time()
        for row, reg, e, s in db.execute(
            select(ExamSessions, ExamRegistrations, CodingExams, Students)
            .join(
                ExamRegistrations, ExamSessions.registration_id == ExamRegistrations.id
            )
            .join(CodingExams, ExamRegistrations.exam_id == CodingExams.id)
            .join(Students, ExamRegistrations.student_id == Students.id)
            .where(
                ExamSessions.status == "active",
                (ExamSessions.ends_at <= now) | (CodingExams.status == "closed"),
            )
        ):
            row.status = "expired"
            row.submitted_at = min(now, row.ends_at)
            db.get(Courses, e.course_id).grades_published = False
            emit(
                db,
                "session.updated",
                e.course_id,
                {"exam_session_id": row.id, "status": "expired"},
                s.user_id,
            )
        db.execute(
            delete(RealtimeEvents).where(RealtimeEvents.created_at < now - 86400)
        )
        db.commit()


async def dispatch(app):
    cursor = 0
    last_maintenance = 0
    while True:
        try:
            if time.monotonic() - last_maintenance > 5:
                await asyncio.to_thread(maintain, app.state.sessions)
                last_maintenance = time.monotonic()
            rows = await asyncio.to_thread(read_events, app.state.sessions, cursor)
            for eid, kind, data, recipients in rows:
                await app.state.hub.publish(kind, data, recipients)
                cursor = eid
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.warning(
                "Notification bridge unavailable; REST snapshots remain authoritative"
            )
        await asyncio.sleep(0.5)


def touch(app, user_id):
    with app.state.sessions() as db:
        rows = list(
            db.scalars(
                select(ExamSessions)
                .join(ExamRegistrations)
                .join(Students, ExamRegistrations.student_id == Students.id)
                .where(Students.user_id == user_id, ExamSessions.status == "active")
            )
        )
        for r in rows:
            r.last_seen_at = time.time()
        if rows:
            db.commit()
