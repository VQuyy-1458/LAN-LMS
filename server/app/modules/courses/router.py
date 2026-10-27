from .service import serialize
from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from pathlib import Path
import hashlib
from sqlalchemy import select, func
from ...core.database import get_db
from ...core.security import learning_user, fail
from ...schemas.common import Pagination
from ...services import access
from ...models import (
    Courses,
    CourseTeachers,
    CourseEnrollments,
    Students,
    Teachers,
    Classes,
)
from .schemas import CourseInput, CoursePatch

router = APIRouter(prefix="/api", tags=["courses"])


@router.get("/public/connection")
def public_connection(request: Request):
    settings = request.app.state.settings
    ca = Path(settings.lan_ca_certificate) if settings.lan_ca_certificate else None
    fingerprint = hashlib.sha256(ca.read_bytes()).hexdigest().upper() if ca and ca.is_file() else None
    return {"origin": settings.https_origin or settings.public_origin,
            "certificate_available": fingerprint is not None,
            "fingerprint": ":".join(fingerprint[i:i+2] for i in range(0, len(fingerprint), 2)) if fingerprint else None}


@router.get("/public/lan-certificate")
def public_certificate(request: Request):
    value = request.app.state.settings.lan_ca_certificate
    if not value or not Path(value).is_file():
        fail(404, "HTTPS_NOT_CONFIGURED", "Chưa tạo chứng chỉ LAN")
    return FileResponse(value, media_type="application/x-x509-ca-cert", filename="LAN-LMS-CA.cer")


@router.get("/public/courses")
def public_courses(db=Depends(get_db), p=Depends(Pagination)):
    """Only catalogue metadata is public; course content keeps its access policy."""
    q = select(Courses).where(Courses.status == "active")
    return p.response(
        [
            dict(
                id=r.id,
                course_code=r.course_code,
                name=r.course_name,
                description=r.description,
                semester=r.semester,
                academic_year=r.academic_year,
            )
            for r in db.scalars(
                q.order_by(Courses.id.desc()).offset(p.offset).limit(p.page_size)
            )
        ],
        db.scalar(select(func.count()).select_from(q.subquery())),
    )


@router.get("/courses")
def courses(db=Depends(get_db), user=Depends(learning_user), p=Depends(Pagination)):
    if user.role == "teacher":
        t = access.teacher(db, user)
        query = (
            select(Courses)
            .join(CourseTeachers)
            .where(CourseTeachers.teacher_id == t.id)
        )
    else:
        s = access.student(db, user)
        query = (
            select(Courses)
            .join(CourseEnrollments)
            .where(
                CourseEnrollments.student_id == s.id,
                CourseEnrollments.status == "active",
            )
        )
    count = db.scalar(select(func.count()).select_from(query.subquery()))
    return p.response(
        [
            serialize(db, r)
            for r in db.scalars(
                query.order_by(Courses.id).offset(p.offset).limit(p.page_size)
            )
        ],
        count,
    )


@router.post("/courses", status_code=201)
def create(body: CourseInput, db=Depends(get_db), user=Depends(learning_user)):
    t = access.teacher(db, user)
    if db.scalar(select(Courses.id).where(Courses.course_code==body.course_code,Courses.semester==body.semester,Courses.academic_year==body.academic_year).execution_options(include_deleted=True)):
        fail(409,"COURSE_EXISTS","Mã khóa học đã tồn tại trong học kỳ và năm học này; chọn mã khác")
    r = Courses(
        course_code=body.course_code,
        course_name=body.name,
        description=body.description,
        start_date=body.start_date.isoformat() if body.start_date else None,
        end_date=body.end_date.isoformat() if body.end_date else None,
        semester=body.semester,
        academic_year=body.academic_year,
        status="active",
        grades_published=False,
        final_grade_policy="single_final_exam",
    )
    db.add(r)
    db.flush()
    db.add(CourseTeachers(course_id=r.id, teacher_id=t.id, role="primary"))
    db.commit()
    return serialize(db, r)


@router.get("/courses/{course_id}")
def detail(course_id: int, db=Depends(get_db), user=Depends(learning_user)):
    return serialize(db, access.course(db, user, course_id))


@router.patch("/courses/{course_id}")
def patch(
    course_id: int, body: CoursePatch, db=Depends(get_db), user=Depends(learning_user)
):
    r = access.course(db, user, course_id, True)
    current = serialize(db, r)
    current.pop("id")
    current.pop("teacher_id")
    current.pop("status")
    from pydantic import ValidationError

    try:
        merged = CourseInput.model_validate(
            {**current, **body.model_dump(exclude_unset=True)}
        )
    except ValidationError:
        fail(422, "VALIDATION_ERROR", "Thông tin hoặc ngày khóa học không hợp lệ")
    if db.scalar(select(Courses.id).where(Courses.id!=r.id,Courses.course_code==merged.course_code,Courses.semester==merged.semester,Courses.academic_year==merged.academic_year).execution_options(include_deleted=True)):
        fail(409,"COURSE_EXISTS","Mã khóa học đã tồn tại trong học kỳ và năm học này")
    r.course_code = merged.course_code
    r.course_name = merged.name
    r.description = merged.description
    r.start_date = merged.start_date.isoformat() if merged.start_date else None
    r.end_date = merged.end_date.isoformat() if merged.end_date else None
    r.semester = merged.semester
    r.academic_year = merged.academic_year
    db.commit()
    return serialize(db, r)


@router.delete("/courses/{course_id}", status_code=204)
def delete_course(course_id: int, db=Depends(get_db), user=Depends(learning_user)):
    from ...services.activity import audit
    from fastapi import Response
    row=access.course(db,user,course_id,True)
    row.status="deleted"
    audit(db,user.user_id,"delete","course",course_id)
    db.commit()
    return Response(status_code=204)


@router.get("/courses/{course_id}/students")
def students(
    course_id: int,
    db=Depends(get_db),
    user=Depends(learning_user),
    p=Depends(Pagination),
):
    access.course(db, user, course_id, True)
    q = (
        select(Students)
        .join(CourseEnrollments)
        .where(
            CourseEnrollments.course_id == course_id,
            CourseEnrollments.status == "active",
        )
    )
    rows = []
    for s in db.scalars(q.order_by(Students.id).offset(p.offset).limit(p.page_size)):
        cls = db.get(Classes, s.class_id) if s.class_id else None
        rows.append(
            dict(
                student_id=s.student_code,
                full_name=s.full_name,
                date_of_birth=s.date_of_birth,
                class_name=cls.class_code if cls else "",
                email=s.email,
            )
        )
    return p.response(rows, db.scalar(select(func.count()).select_from(q.subquery())))
