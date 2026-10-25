"""D01 shared LMS/Judge schema; member 1 auth migration remains unchanged."""
from alembic import op
from database.migrations.schema_0002 import Base  # frozen historical schema

revision = "0002_database_base"
down_revision = "0001_auth"
branch_labels = None
depends_on = None

TABLES = ['classes', 'courses', 'course_classes', 'teachers', 'csv_import_previews', 'course_materials', 'calendar_events', 'attendance_sessions', 'assignments', 'coding_exams', 'problems', 'test_cases', 'idempotency_keys', 'grade_components', 'audit_logs', 'students', 'course_teachers', 'course_enrollments', 'attendance_records', 'assignment_submissions', 'exam_registrations', 'exam_sessions', 'code_submissions', 'judge_jobs', 'judge_results', 'grades']


def upgrade():
    bind = op.get_bind()
    for name in TABLES:
        Base.metadata.tables[name].create(bind=bind, checkfirst=False)


def downgrade():
    bind = op.get_bind()
    for name in reversed(TABLES):
        Base.metadata.tables[name].drop(bind=bind, checkfirst=False)
