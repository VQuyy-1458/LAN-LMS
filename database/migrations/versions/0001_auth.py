"""Member 1 auth foundation. Course/enrollment migrations belong to member 3."""
from alembic import op
import sqlalchemy as sa

revision = '0001_auth'
down_revision = None


def upgrade():
    op.create_table('users', sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String(128), nullable=False, unique=True),
        sa.Column('password_hash', sa.String, nullable=False),
        sa.Column('role', sa.String(16), nullable=False),
        sa.Column('must_change_password', sa.Boolean, nullable=False),
        sa.Column('active', sa.Boolean, nullable=False),
        sa.CheckConstraint("role IN ('teacher','student')", name='valid_user_role'))
    op.create_table('auth_sessions', sa.Column('token_hash', sa.String(64), primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('csrf_hash', sa.String, nullable=True), sa.Column('expires_at', sa.Float, nullable=False))
    op.create_index('ix_auth_sessions_user_id', 'auth_sessions', ['user_id'])
    op.create_table('login_attempts', sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('ip', sa.String, nullable=False), sa.Column('created_at', sa.Float, nullable=False))
    op.create_index('ix_login_attempts_ip', 'login_attempts', ['ip'])


def downgrade():
    op.drop_table('login_attempts')
    op.drop_table('auth_sessions')
    op.drop_table('users')
