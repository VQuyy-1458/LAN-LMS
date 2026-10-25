"""DB-derived resource permissions. User IDs and student/teacher profile IDs are distinct."""
from sqlalchemy import select
from ..core.security import fail
from ..models import Courses, Teachers, Students, CourseTeachers, CourseEnrollments


def teacher(db, user):
    if user.role != 'teacher':
        fail(403, 'FORBIDDEN', 'Chỉ giảng viên được thực hiện')
    row=db.scalar(select(Teachers).where(Teachers.user_id==user.user_id))
    if not row:
        fail(403,'TEACHER_PROFILE_REQUIRED','Chưa có hồ sơ giảng viên')
    return row


def student(db, user):
    if user.role != 'student':
        fail(403,'FORBIDDEN','Chỉ sinh viên được thực hiện')
    row=db.scalar(select(Students).where(Students.user_id==user.user_id))
    if not row:
        fail(403,'STUDENT_PROFILE_REQUIRED','Chưa có hồ sơ sinh viên')
    return row


def course(db, user, course_id, manage=False):
    row=db.get(Courses,course_id)
    if not row: fail(404,'NOT_FOUND','Không tìm thấy khóa học')
    if user.role=='teacher':
        profile=teacher(db,user)
        allowed=db.scalar(select(CourseTeachers.id).where(CourseTeachers.course_id==course_id,CourseTeachers.teacher_id==profile.id))
    elif not manage:
        profile=student(db,user)
        allowed=db.scalar(select(CourseEnrollments.id).where(CourseEnrollments.course_id==course_id,CourseEnrollments.student_id==profile.id,CourseEnrollments.status=='active'))
    else:
        allowed=None
    if not allowed: fail(403,'FORBIDDEN','Không có quyền với khóa học này')
    return row
