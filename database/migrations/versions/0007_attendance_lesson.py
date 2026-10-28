"""Bind one attendance roster to each scheduled lesson."""
from alembic import op
import sqlalchemy as sa

revision="0007_attendance_lesson"
down_revision="0006_assignment_files"
branch_labels=None
depends_on=None


def upgrade():
    # Native ADD COLUMN preserves attendance_records referencing this populated table.
    if op.get_bind().dialect.name=="sqlite":
        op.execute("ALTER TABLE attendance_sessions ADD COLUMN event_id INTEGER REFERENCES calendar_events(id)")
    else:
        op.add_column("attendance_sessions",sa.Column("event_id",sa.Integer(),sa.ForeignKey("calendar_events.id"),nullable=True))
    op.create_index("uq_attendance_event","attendance_sessions",["event_id"],unique=True)


def downgrade():
    op.drop_index("uq_attendance_event",table_name="attendance_sessions")
    op.drop_column("attendance_sessions","event_id")
