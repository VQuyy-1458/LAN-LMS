"""Independent editable homework grades, including students without submissions."""
from alembic import op
import sqlalchemy as sa
revision = "0008_assignment_grades"
down_revision = "0007_attendance_lesson"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("assignment_grades",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assignment_id", sa.Integer(), sa.ForeignKey("assignments.id"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("graded_by", sa.Integer(), sa.ForeignKey("teachers.id"), nullable=False),
        sa.UniqueConstraint("assignment_id", "student_id", name="uq_assignment_grade"))

def downgrade():
    op.drop_table("assignment_grades")
