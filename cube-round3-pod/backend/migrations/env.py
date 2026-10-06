from alembic import context
from sqlalchemy import create_engine

from backend.config import settings
from backend.db import metadata

url = settings().migration_database_url or settings().database_url
with create_engine(url, connect_args={"connect_timeout": 5}).connect() as connection:
    context.configure(connection=connection, target_metadata=metadata)
    with context.begin_transaction():
        context.run_migrations()
