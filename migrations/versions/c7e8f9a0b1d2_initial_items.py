"""initial items table and pgvector extension

Revision ID: c7e8f9a0b1d2
Revises:
Create Date: 2026-04-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "c7e8f9a0b1d2"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("image_url", sa.String(length=1024), nullable=False),
        sa.Column("subcategory", sa.String(length=128), nullable=True),
        sa.Column("style", sa.String(length=64), nullable=True),
        sa.Column("color_hex", sa.String(length=16), nullable=True),
        sa.Column("embedding", Vector(512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_items_user_id"), "items", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_items_user_id"), table_name="items")
    op.drop_table("items")
    op.execute("DROP EXTENSION IF EXISTS vector")
