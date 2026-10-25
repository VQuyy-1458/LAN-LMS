"""Day 25 integration fields and idempotency/profile constraints."""

from alembic import op
import sqlalchemy as sa

revision = "0003_day25"
down_revision = "0002_database_base"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("courses") as batch:
        batch.add_column(
            sa.Column("description", sa.Text(), nullable=False, server_default="")
        )
        batch.add_column(sa.Column("start_date", sa.Text(), nullable=True))
        batch.add_column(sa.Column("end_date", sa.Text(), nullable=True))
    with op.batch_alter_table("course_materials") as batch:
        batch.add_column(
            sa.Column("uploaded_at", sa.Float(), nullable=False, server_default="0")
        )
    with op.batch_alter_table("assignments") as batch:
        batch.add_column(
            sa.Column("description", sa.Text(), nullable=False, server_default="")
        )
    with op.batch_alter_table("assignment_submissions") as batch:
        batch.add_column(
            sa.Column(
                "original_filename",
                sa.Text(),
                nullable=False,
                server_default="submission",
            )
        )
        batch.add_column(
            sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0")
        )
    with op.batch_alter_table("problems") as batch:
        batch.add_column(
            sa.Column(
                "languages_json",
                sa.Text(),
                nullable=False,
                server_default='["c","cpp","java"]',
            )
        )
        batch.add_column(
            sa.Column("io_mode", sa.Text(), nullable=False, server_default="stdio")
        )
        batch.add_column(sa.Column("input_filename", sa.Text(), nullable=True))
        batch.add_column(sa.Column("output_filename", sa.Text(), nullable=True))
    with op.batch_alter_table("judge_results") as batch:
        batch.add_column(
            sa.Column("compile_message", sa.Text(), nullable=False, server_default="")
        )
        batch.add_column(sa.Column("reason_code", sa.Text(), nullable=True))
    # 0002 incorrectly made user_id itself unique; users need many independent keys.
    op.drop_index("ix_idempotency_keys_user_id", table_name="idempotency_keys")
    with op.batch_alter_table("idempotency_keys") as batch:
        batch.add_column(sa.Column("response_json", sa.Text(), nullable=True))
    op.create_index(
        "ix_idempotency_keys_user_id", "idempotency_keys", ["user_id"], unique=False
    )
    op.create_index("uq_students_user_id", "students", ["user_id"], unique=True)
    op.create_index(
        "uq_one_final_per_course",
        "coding_exams",
        ["course_id"],
        unique=True,
        sqlite_where=sa.text("grade_component = 'final'"),
    )
    op.execute("UPDATE courses SET final_grade_policy='single_final_exam'")


def downgrade():
    # Refuse an unsafe downgrade if multiple keys now exist for one user.
    bind = op.get_bind()
    if bind.execute(
        sa.text(
            "SELECT user_id FROM idempotency_keys GROUP BY user_id HAVING count(*)>1"
        )
    ).first():
        raise RuntimeError(
            "Cannot downgrade: multiple idempotency keys exist; archive them explicitly first"
        )
    op.drop_index("uq_one_final_per_course", table_name="coding_exams")
    op.drop_index("uq_students_user_id", table_name="students")
    op.drop_index("ix_idempotency_keys_user_id", table_name="idempotency_keys")
    with op.batch_alter_table("idempotency_keys") as batch:
        batch.drop_column("response_json")
    op.create_index(
        "ix_idempotency_keys_user_id", "idempotency_keys", ["user_id"], unique=True
    )
    for table, columns in [
        ("judge_results", ["compile_message", "reason_code"]),
        (
            "problems",
            ["languages_json", "io_mode", "input_filename", "output_filename"],
        ),
        ("assignment_submissions", ["original_filename", "size_bytes"]),
        ("assignments", ["description"]),
        ("course_materials", ["uploaded_at"]),
        ("courses", ["description", "start_date", "end_date"]),
    ]:
        with op.batch_alter_table(table) as batch:
            for column in columns:
                batch.drop_column(column)
