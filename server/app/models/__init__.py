"""D01 shared ORM models. Auth models are owned by member 1."""
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint, Index, text
from sqlalchemy.orm import Mapped, mapped_column
from server.app.core.database import Base, User, AuthSession, LoginAttempt

class Classes(Base):
    __tablename__ = "classes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    class_code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    class_name: Mapped[str] = mapped_column(Text, nullable=False)
    academic_year: Mapped[str | None] = mapped_column(Text, nullable=True)

class Courses(Base):
    __tablename__ = "courses"
    __table_args__ = (UniqueConstraint('course_code', 'semester', 'academic_year', name="uq_courses_course_code_semester_academic_year"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_code: Mapped[str] = mapped_column(Text, nullable=False)
    course_name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    start_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    end_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    semester: Mapped[str] = mapped_column(Text, nullable=False)
    academic_year: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    grades_published: Mapped[bool] = mapped_column(Boolean, nullable=False)
    final_grade_policy: Mapped[str] = mapped_column(Text, nullable=False)

class CourseClasses(Base):
    __tablename__ = "course_classes"
    __table_args__ = (UniqueConstraint('course_id', 'class_id', name="uq_course_classes_course_id_class_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id", ondelete="RESTRICT"), nullable=False, index=True)

class Teachers(Base):
    __tablename__ = "teachers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, unique=True, index=True)
    teacher_code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)

class CsvImportPreviews(Base):
    __tablename__ = "csv_import_previews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    preview_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False, index=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    can_confirm: Mapped[bool] = mapped_column(Boolean, nullable=False)
    expires_at: Mapped[float] = mapped_column(Float, nullable=False)
    confirmed_at: Mapped[float | None] = mapped_column(Float, nullable=True)

class CourseMaterials(Base):
    __tablename__ = "course_materials"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_at: Mapped[float] = mapped_column(Float, default=0, server_default="0")

class CalendarEvents(Base):
    __tablename__ = "calendar_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    event_type: Mapped[str] = mapped_column(Text, default="lesson", server_default="lesson")
    starts_at: Mapped[float] = mapped_column(Float, nullable=False)
    ends_at: Mapped[float] = mapped_column(Float, nullable=False)

class AttendanceSessions(Base):
    __tablename__ = "attendance_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, default="Điểm danh", server_default="Điểm danh")
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    starts_at: Mapped[float] = mapped_column(Float, nullable=False)
    expires_at: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)

class Assignments(Base):
    __tablename__ = "assignments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    due_at: Mapped[float] = mapped_column(Float, nullable=False)
    allow_resubmit: Mapped[bool] = mapped_column(Boolean, nullable=False)

class CodingExams(Base):
    __tablename__ = "coding_exams"
    __table_args__ = (Index("uq_one_final_per_course", "course_id", unique=True, sqlite_where=text("grade_component = 'final'")),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    grade_component: Mapped[str] = mapped_column(Text, nullable=False)
    starts_at: Mapped[float] = mapped_column(Float, nullable=False)
    ends_at: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    results_published: Mapped[bool] = mapped_column(Boolean, nullable=False)
    score_ladder_json: Mapped[str] = mapped_column(Text, default="[0,5,7,8,9,10]", server_default="[0,5,7,8,9,10]")

class Problems(Base):
    __tablename__ = "problems"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("coding_exams.id", ondelete="RESTRICT"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    languages_json: Mapped[str] = mapped_column(Text, default='["c","cpp","java"]',server_default='["c","cpp","java"]')
    io_mode: Mapped[str] = mapped_column(Text,default='stdio',server_default='stdio')
    input_filename: Mapped[str | None] = mapped_column(Text,nullable=True)
    output_filename: Mapped[str | None] = mapped_column(Text,nullable=True)
    max_score: Mapped[float] = mapped_column(Float, nullable=False)
    time_limit_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    memory_limit_mib: Mapped[int] = mapped_column(Integer, nullable=False)
    comparator: Mapped[str] = mapped_column(Text, nullable=False)

class TestCases(Base):
    __tablename__ = "test_cases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="RESTRICT"), nullable=False, index=True)
    input_path: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output_path: Mapped[str] = mapped_column(Text, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_sample: Mapped[bool] = mapped_column(Boolean, nullable=False)

class IdempotencyKeys(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (UniqueConstraint('user_id', 'method', 'path', 'key', name="uq_idempotency_keys_user_id_method_path_key"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    method: Mapped[str] = mapped_column(Text, nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    key: Mapped[str] = mapped_column(Text, nullable=False)
    request_hash: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expires_at: Mapped[float] = mapped_column(Float, nullable=False)

class GradeComponents(Base):
    __tablename__ = "grade_components"
    __table_args__ = (UniqueConstraint('course_id', 'component_code', name="uq_grade_components_course_id_component_code"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True)
    component_code: Mapped[str] = mapped_column(Text, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, nullable=False)

class AuditLogs(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[float] = mapped_column(Float, nullable=False)

class Students(Base):
    __tablename__ = "students"
    __table_args__ = (Index("uq_students_user_id", "user_id", unique=True),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    class_id: Mapped[int | None] = mapped_column(ForeignKey("classes.id", ondelete="RESTRICT"), nullable=True, index=True)
    student_code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    date_of_birth: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)

class CourseTeachers(Base):
    __tablename__ = "course_teachers"
    __table_args__ = (UniqueConstraint('course_id', 'teacher_id', name="uq_course_teachers_course_id_teacher_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(Text, nullable=False)

class CourseEnrollments(Base):
    __tablename__ = "course_enrollments"
    __table_args__ = (UniqueConstraint('course_id', 'student_id', name="uq_course_enrollments_course_id_student_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)

class AttendanceRecords(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint('session_id', 'student_id', name="uq_attendance_records_session_id_student_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("attendance_sessions.id", ondelete="RESTRICT"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True)
    checked_in_at: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)

class AssignmentSubmissions(Base):
    __tablename__ = "assignment_submissions"
    __table_args__ = (UniqueConstraint('assignment_id', 'student_id', 'attempt_no', name="uq_assignment_submissions_assignment_id_student_id_attempt_no"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True)
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, default="submission", server_default="submission")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[float] = mapped_column(Float, nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

class ExamRegistrations(Base):
    __tablename__ = "exam_registrations"
    __table_args__ = (UniqueConstraint('exam_id', 'student_id', name="uq_exam_registrations_exam_id_student_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("coding_exams.id", ondelete="RESTRICT"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True)
    registered_at: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)

class ExamSessions(Base):
    __tablename__ = "exam_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    registration_id: Mapped[int] = mapped_column(ForeignKey("exam_registrations.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    started_at: Mapped[float] = mapped_column(Float, nullable=False)
    ends_at: Mapped[float] = mapped_column(Float, nullable=False)
    submitted_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_seen_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_ip: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)

class CodeSubmissions(Base):
    __tablename__ = "code_submissions"
    __table_args__ = (UniqueConstraint('exam_session_id', 'problem_id', 'attempt_no', name="uq_code_submissions_exam_session_id_problem_id_attempt_no"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_session_id: Mapped[int] = mapped_column(ForeignKey("exam_sessions.id", ondelete="RESTRICT"), nullable=False, index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="RESTRICT"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True)
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    language: Mapped[str] = mapped_column(Text, nullable=False)
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)

class JudgeJobs(Base):
    __tablename__ = "judge_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("code_submissions.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    attempt_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    lease_until: Mapped[float | None] = mapped_column(Float, nullable=True)
    worker_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    finished_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    compile_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    run_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[float] = mapped_column(Float, nullable=False)

class JudgeResults(Base):
    __tablename__ = "judge_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("code_submissions.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    verdict: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    compile_message: Mapped[str] = mapped_column(Text,default="",server_default="")
    reason_code: Mapped[str | None] = mapped_column(Text,nullable=True)
    judged_at: Mapped[float] = mapped_column(Float, nullable=False)

class Grades(Base):
    __tablename__ = "grades"
    __table_args__ = (UniqueConstraint('component_id', 'student_id', name="uq_grades_component_id_student_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    component_id: Mapped[int] = mapped_column(ForeignKey("grade_components.id", ondelete="RESTRICT"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    entry_method: Mapped[str] = mapped_column(Text, nullable=False)
    source_exam_id: Mapped[int | None] = mapped_column(ForeignKey("coding_exams.id", ondelete="RESTRICT"), nullable=True, index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    graded_by: Mapped[int | None] = mapped_column(ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=True, index=True)

__all__ = ['Base', 'User', 'AuthSession', 'LoginAttempt', 'Classes', 'Courses', 'CourseClasses', 'Teachers', 'CsvImportPreviews', 'CourseMaterials', 'CalendarEvents', 'AttendanceSessions', 'Assignments', 'CodingExams', 'Problems', 'TestCases', 'IdempotencyKeys', 'GradeComponents', 'AuditLogs', 'Students', 'CourseTeachers', 'CourseEnrollments', 'AttendanceRecords', 'AssignmentSubmissions', 'ExamRegistrations', 'ExamSessions', 'CodeSubmissions', 'JudgeJobs', 'JudgeResults', 'Grades']


class RealtimeEvents(Base):
    """Durable notification handoff; REST remains authoritative after reconnect."""
    __tablename__ = "realtime_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    data_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[float] = mapped_column(Float, nullable=False)


class ExamSessionEvents(Base):
    __tablename__ = "exam_session_events"
    __table_args__ = (UniqueConstraint("session_id", "event_key", name="uq_session_event_key"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("exam_sessions.id"), nullable=False)
    event_key: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[float] = mapped_column(Float, nullable=False)

__all__.append("ExamSessionEvents")
