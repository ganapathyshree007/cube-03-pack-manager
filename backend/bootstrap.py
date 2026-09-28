"""Run as the separate migration job, never as an application replica."""

import os
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from psycopg import sql
from .config import settings


def main():
    password = os.environ["APP_DATABASE_PASSWORD"]
    if len(password) < 20:
        raise ValueError("Application database password must contain at least 20 characters")
    engine = create_engine(settings().migration_database_url, connect_args={"connect_timeout": 5})
    with engine.begin() as conn:
        cursor = conn.connection.driver_connection.cursor()
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname='pack_app'")
        if cursor.fetchone() is None:
            cursor.execute(
                sql.SQL("CREATE ROLE pack_app LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD {}").format(
                    sql.Literal(password)
                )
            )
        cursor.execute("GRANT CONNECT ON DATABASE pack TO pack_app")
        cursor.execute("GRANT USAGE ON SCHEMA public TO pack_app")
    command.upgrade(Config("alembic.ini"), "head")


if __name__ == "__main__":
    main()
