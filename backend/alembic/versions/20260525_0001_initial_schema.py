"""initial schema

Revision ID: 20260525_0001
Revises:
Create Date: 2026-05-25 00:00:00.000000
"""

from alembic import op

from app.db.session import Base
import app.models.models  # noqa: F401


revision = "20260525_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    for table in Base.metadata.sorted_tables:
        table.create(bind=bind, checkfirst=True)
    for table in Base.metadata.sorted_tables:
        for index in table.indexes:
            index.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    # Downgrade intencionalmente vazio: a migration inicial não deve remover dados.
    pass
