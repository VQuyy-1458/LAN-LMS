from fastapi import APIRouter, Depends
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


def serialize(db, row):
    teacher_id = db.scalar(
        select(Teachers.user_id)
        .join(CourseTeachers, CourseTeachers.teacher_id == Teachers.id)
        .where(CourseTeachers.course_id == row.id)
        .order_by(Teachers.id)
    )
    return dict(
        id=row.id,
        course_code=row.course_code,
        name=row.course_name,
        description=row.description,
        start_date=row.start_date,
        end_date=row.end_date,
        teacher_id=teacher_id,
        semester=row.semester,
        academic_year=row.academic_year,
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
    from pydantic import ValidationError

    try:
        merged = CourseInput.model_validate(
            {**current, **body.model_dump(exclude_unset=True)}
        )
    except ValidationError:
        fail(422, "VALIDATION_ERROR", "Thông tin hoặc ngày khóa học không hợp lệ")
    r.course_code = merged.course_code
    r.course_name = merged.name
    r.description = merged.description
    r.start_date = merged.start_date.isoformat() if merged.start_date else None
    r.end_date = merged.end_date.isoformat() if merged.end_date else None
    r.semester = merged.semester
    r.academic_year = merged.academic_year
    db.commit()
    return serialize(db, r)


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
                class_name=cls.class_code if cls else "",
                email=s.email,
            )
        )
    return p.response(rows, db.scalar(select(func.count()).select_from(q.subquery())))
