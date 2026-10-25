"""Calendar, attendance presentation and durable worker-to-API notifications."""

from alembic import op
import sqlalchemy as sa

revision = "0004_completion"
down_revision = "0003_day25"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("calendar_events") as b:
        b.add_column(
            sa.Column("description", sa.Text(), nullable=False, server_default="")
        )
        b.add_column(
            sa.Column("event_type", sa.Text(), nullable=False, server_default="lesson")
        )
    with op.batch_alter_table("attendance_sessions") as b:
        b.add_column(
            sa.Column("title", sa.Text(), nullable=False, server_default="Điểm danh")
        )
    with op.batch_alter_table("coding_exams") as b:
        b.add_column(
            sa.Column(
                "score_ladder_json",
                sa.Text(),
                nullable=False,
                server_default="[0,5,7,8,9,10]",
            )
        )
    op.create_index(
        "uq_one_midterm_per_course",
        "coding_exams",
        ["course_id"],
        unique=True,
        sqlite_where=sa.text("grade_component = 'midterm'"),
    )
    with op.batch_alter_table("judge_jobs") as b:
        for name in ("started_at", "finished_at", "compile_ms", "run_ms"):
            b.add_column(sa.Column(name, sa.Float(), nullable=True))
    op.create_table(
        "realtime_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column(
            "course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False
        ),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("data_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Float(), nullable=False),
    )
    op.create_index("ix_realtime_events_course_id", "realtime_events", ["course_id"])


def downgrade():
    op.drop_table("realtime_events")
    with op.batch_alter_table("judge_jobs") as b:
        for name in ("started_at", "finished_at", "compile_ms", "run_ms"):
            b.drop_column(name)
    with op.batch_alter_table("coding_exams") as b:
        b.drop_column("score_ladder_json")
    op.drop_index("uq_one_midterm_per_course", table_name="coding_exams")
    with op.batch_alter_table("attendance_sessions") as b:
        b.drop_column("title")
    with op.batch_alter_table("calendar_events") as b:
        b.drop_column("description")
        b.drop_column("event_type")
