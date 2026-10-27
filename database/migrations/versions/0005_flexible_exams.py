"""Multiple midterms/practice exams and session supervision metadata."""
from alembic import op
import sqlalchemy as sa

revision = "0005_flexible_exams"
down_revision = "0004_completion"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index("uq_one_midterm_per_course", table_name="coding_exams")
    with op.batch_alter_table("exam_sessions") as batch:
        batch.add_column(sa.Column("started_ip", sa.Text(), nullable=True))
    op.create_table(
        "exam_session_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("exam_sessions.id"), nullable=False),
        sa.Column("event_key", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("ip_address", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.UniqueConstraint("session_id", "event_key", name="uq_session_event_key"),
    )


def downgrade():
    # Never silently delete extra midterms during rollback.
    connection = op.get_bind()
    if connection.execute(sa.text("SELECT 1 FROM coding_exams WHERE grade_component='midterm' GROUP BY course_id HAVING count(*)>1")).first():
        raise RuntimeError("Reclassify extra midterms before downgrade")
    op.drop_table("exam_session_events")
    with op.batch_alter_table("exam_sessions") as batch:
        batch.drop_column("started_ip")
    op.create_index("uq_one_midterm_per_course", "coding_exams", ["course_id"], unique=True,
                    sqlite_where=sa.text("grade_component = 'midterm'"))
