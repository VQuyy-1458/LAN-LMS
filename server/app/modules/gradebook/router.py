from .schemas import Weights, Entry, Update, Publish
import csv
import io
from fastapi import APIRouter, Depends, Response, UploadFile, File
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Literal
from sqlalchemy import select
from ...core.database import get_db
from ...core.security import learning_user, fail
from ...models import (
    Courses,
    Grades,
    Students,
    CourseEnrollments,
    AttendanceSessions,
    Assignments,
)
from ...services import access, idempotency
from ...services.activity import audit, emit
from . import service as svc

router = APIRouter(prefix="/api", tags=["gradebook"])


@router.get("/courses/{cid}/grade-components")
def weights(cid: int, db=Depends(get_db), user=Depends(learning_user)):
    access.course(db, user, cid, True)
    return svc.weights(db, cid)


@router.patch("/courses/{cid}/grade-components")
def change_weights(
    cid: int, body: Weights, db=Depends(get_db), user=Depends(learning_user)
):
    idempotency.write_lock(db)
    course = access.course(db, user, cid, True)
    before = svc.weights(db, cid)
    cs = svc.components(db, cid)
    for k, v in body.model_dump().items():
        cs[k].weight = v
    course.grades_published = False
    audit(
        db,
        user.user_id,
        "weights",
        "course",
        cid,
        {"before": before, "after": body.model_dump()},
    )
    db.commit()
    return body.model_dump()


@router.get("/courses/{cid}/gradebook")
def gradebook(cid: int, db=Depends(get_db), user=Depends(learning_user)):
    course = access.course(db, user, cid)
    student = access.student(db, user) if user.role == "student" else None
    items = svc.rows(db, cid, student.id if student else None)
    return dict(
        weights=svc.weights(db, cid), published=course.grades_published, items=items
    )


@router.patch("/courses/{cid}/grades")
def override(cid: int, body: Update, db=Depends(get_db), user=Depends(learning_user)):
    idempotency.write_lock(db)
    course = access.course(db, user, cid, True)
    t = access.teacher(db, user)
    cs = svc.components(db, cid)
    seen = set()
    for item in body.items:
        key = (item.student_id, item.component)
        if key in seen:
            fail(422, "DUPLICATE_ENTRY", "Trùng sinh viên/thành phần trong yêu cầu")
        seen.add(key)
        s = db.scalar(
            select(Students)
            .join(CourseEnrollments)
            .where(
                Students.student_code == item.student_id,
                CourseEnrollments.course_id == cid,
                CourseEnrollments.status == "active",
            )
        )
        if not s:
            fail(404, "NOT_FOUND", "Sinh viên không thuộc khóa học")
        r = db.scalar(
            select(Grades).where(
                Grades.component_id == cs[item.component].id, Grades.student_id == s.id
            )
        )
        before = r.score if r else None
        if item.score is None:
            if r:
                db.delete(r)
        else:
            if not r:
                r = Grades(component_id=cs[item.component].id, student_id=s.id)
                db.add(r)
            r.score = item.score
            r.entry_method = "manual"
            r.reason = item.reason
            r.graded_by = t.id
            r.source_exam_id = None
        audit(
            db,
            user.user_id,
            "override",
            "grade",
            cid,
            {
                "student_id": item.student_id,
                "component": item.component,
                "before": before,
                "after": item.score,
                "reason": item.reason,
            },
        )
    course.grades_published = False
    emit(db, "grade.updated", cid, {"course_id": cid})
    db.commit()
    return {"updated_count": len(body.items)}


@router.post("/courses/{cid}/gradebook/publish")
def publish(cid: int, body: Publish, db=Depends(get_db), user=Depends(learning_user)):
    idempotency.write_lock(db)
    course = access.course(db, user, cid, True)
    if body.published:
        try:
            Weights.model_validate(svc.weights(db, cid))
        except ValueError:
            fail(409, "INVALID_WEIGHTS", "Trọng số không hợp lệ")
        import time

        ws = svc.weights(db, cid)
        now = time.time()
        if ws.get("attendance", 0) > 0 and db.scalar(
            select(AttendanceSessions.id)
            .where(
                AttendanceSessions.course_id == cid,
                AttendanceSessions.status == "open",
                AttendanceSessions.expires_at > now,
            )
            .limit(1)
        ):
            fail(409, "INCOMPLETE_GRADES", "Còn phiên điểm danh đang mở")
        if ws.get("homework", 0) > 0 and db.scalar(
            select(Assignments.id)
            .where(Assignments.course_id == cid, Assignments.due_at > now)
            .limit(1)
        ):
            fail(409, "INCOMPLETE_GRADES", "Còn bài tập chưa đến hạn")
        items = svc.rows(db, cid)
        from ...models import CodingExams
        exams=list(db.scalars(select(CodingExams).where(CodingExams.course_id==cid)))
        students=list(db.scalars(select(Students).join(CourseEnrollments).where(CourseEnrollments.course_id==cid,CourseEnrollments.status=="active")))
        if any(ws.get(e.grade_component,0)>0 and svc.single_exam_score(db,e,s.id) is None for e in exams for s in students):
            fail(409,"INCOMPLETE_GRADES","Còn đề thi chưa kết thúc hoặc bài chờ chấm; chưa thể chốt tổng kết")
        if not items or any(r["total_score"] is None for r in items):
            fail(
                409, "INCOMPLETE_GRADES", "Còn thiếu điểm thành phần hoặc bài chờ chấm"
            )
    course.grades_published = body.published
    if body.published: course.status = "finalized"
    audit(db, user.user_id, "publish", "gradebook", cid, {"published": body.published})
    db.commit()
    return {"published": body.published}


def safe_text(value):
    text = str(value)
    return (
        "'" + text
        if text.lstrip().startswith(("=", "+", "-", "@"))
        or text.startswith(("\t", "\r"))
        else text
    )


@router.post("/courses/{cid}/gradebook/import-csv")
async def import_csv(cid: int, file: UploadFile = File(...), db=Depends(get_db), user=Depends(learning_user)):
    from ...services.files import read_upload
    from pydantic import ValidationError
    _, data = await read_upload(file, 2 * 1024 * 1024, {".csv"})
    try:
        reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""))
        columns = reader.fieldnames or []
        valid = {k + "_score": k for k in svc.DEFAULT_WEIGHTS}
        if len(columns) != len(set(columns)) or "student_id" not in columns or not set(columns) & set(valid):
            raise ValueError("Cần student_id và ít nhất một cột attendance_score, homework_score, midterm_score, final_score")
        items = []
        for number, row in enumerate(reader, 2):
            if number > 2001 or None in row:
                raise ValueError("CSV quá 2.000 dòng hoặc sai số cột")
            for column, component in valid.items():
                value = (row.get(column) or "").strip()
                if value:
                    items.append(Entry(student_id=row["student_id"].strip(), component=component, score=float(value)))
        if not items:
            raise ValueError("Không có điểm để nhập; ô trống giữ nguyên điểm hiện có")
        body = Update(items=items)
    except (UnicodeError, ValueError, ValidationError, csv.Error) as error:
        fail(422, "INVALID_GRADE_CSV", str(error))
    return override(cid, body, db, user)


@router.get("/courses/{cid}/gradebook/export-csv")
def export(cid: int, db=Depends(get_db), user=Depends(learning_user)):
    access.course(db, user, cid, True)
    items = svc.rows(db, cid)
    keys = [
        "student_id",
        "full_name",
        "class_name",
        "attendance_score",
        "homework_score",
        "midterm_score",
        "final_score",
        "total_score",
    ]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=keys)
    writer.writeheader()
    for row in items:
        writer.writerow(
            {
                k: (safe_text(v) if isinstance(v, str) else "" if v is None else v)
                for k, v in row.items()
            }
        )
    return Response(
        content=("\ufeff" + stream.getvalue()).encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="grades-{cid}.csv"'},
    )
