import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import settings
from app.models import Base

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_engine():
    db_url = settings.sync_database_url
    if "sqlite" in db_url:
        return create_engine(db_url)
    try:
        eng = create_engine(db_url, poolclass=pool.NullPool)
        with eng.connect():
            pass
        return eng
    except Exception:
        # Fallback for local testing when Postgres service is not running on host
        return create_engine("sqlite:///./aerocpi_dev.db")

def run_migrations_offline() -> None:
    url = str(get_engine().url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
