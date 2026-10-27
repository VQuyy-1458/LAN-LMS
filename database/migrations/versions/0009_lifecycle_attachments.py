"""Lifecycle visibility and multiple assignment handouts."""
from alembic import op
import sqlalchemy as sa
revision="0009_lifecycle_attachments"
down_revision="0008_assignment_grades"
branch_labels=None
depends_on=None

def upgrade():
    for name in ("assignments","coding_exams"):
        op.add_column(name,sa.Column("deleted",sa.Boolean(),nullable=False,server_default=sa.false()))
    op.drop_index("uq_one_final_per_course",table_name="coding_exams")
    op.create_index("uq_one_final_per_course","coding_exams",["course_id"],unique=True,sqlite_where=sa.text("grade_component = 'final' AND deleted = 0"))
    op.create_table("assignment_attachments",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("assignment_id",sa.Integer(),sa.ForeignKey("assignments.id"),nullable=False),
        sa.Column("original_filename",sa.Text(),nullable=False),
        sa.Column("storage_path",sa.Text(),nullable=False),
        sa.Column("size_bytes",sa.Integer(),nullable=False))
    op.execute("INSERT INTO assignment_attachments (assignment_id,original_filename,storage_path,size_bytes) SELECT id,attachment_filename,attachment_path,0 FROM assignments WHERE attachment_path IS NOT NULL")

def downgrade():
    op.drop_table("assignment_attachments")
    op.drop_index("uq_one_final_per_course",table_name="coding_exams")
    for name in ("assignments","coding_exams"):op.drop_column(name,"deleted")
    op.create_index("uq_one_final_per_course","coding_exams",["course_id"],unique=True,sqlite_where=sa.text("grade_component = 'final'"))
