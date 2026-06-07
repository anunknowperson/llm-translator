"""create translations table

Revision ID: 0001
Revises:
Create Date: 2026-06-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Версионирование данных: первая миграция создаёт таблицу переводов
def upgrade() -> None:
    op.create_table(
        "translations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("translated_text", sa.Text(), nullable=False),
        sa.Column("source_lang", sa.String(length=8), nullable=False),
        sa.Column("target_lang", sa.String(length=8), nullable=False),
        sa.Column("creativity", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_translations_created_at", "translations", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_translations_created_at", table_name="translations")
    op.drop_table("translations")
