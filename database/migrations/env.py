from alembic import context
from server.app.core.config import Settings
from server.app.core.database import Base, database

engine, _ = database(Settings().database_url)
with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()
engine.dispose()
