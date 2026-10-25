from sqlalchemy import select
from ...models import Teachers, CourseTeachers


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
