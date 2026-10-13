import os
from logging.config import fileConfig
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection
from alembic import context

# Importar modelos para que o Alembic os detecte
from app.db.session import Base
import app.models.models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def load_dotenv_if_present() -> None:
    for path in (".env", "../.env"):
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_database_url() -> str:
    load_dotenv_if_present()
    url = (
        os.getenv("DATABASE_URL_SYNC")
        or os.getenv("DATABASE_URL")
        or config.get_main_option("sqlalchemy.url")
    )
    if not url:
        raise RuntimeError("DATABASE_URL ou DATABASE_URL_SYNC deve estar configurada para o Alembic")
    return url.replace("postgresql+asyncpg", "postgresql+psycopg2")


def run_migrations_offline() -> None:
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(get_database_url(), pool_pre_ping=True)
    with engine.connect() as conn:
        do_run_migrations(conn)
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
