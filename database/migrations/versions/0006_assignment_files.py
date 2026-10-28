"""Teacher assignment handout files."""
from alembic import op
import sqlalchemy as sa

revision = "0006_assignment_files"
down_revision = "0005_flexible_exams"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("assignments") as batch:
        batch.add_column(sa.Column("attachment_path", sa.Text(), nullable=True))
        batch.add_column(sa.Column("attachment_filename", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("assignments") as batch:
        batch.drop_column("attachment_filename")
        batch.drop_column("attachment_path")
