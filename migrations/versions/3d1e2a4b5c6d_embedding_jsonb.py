from typing import Sequence, Union

from alembic import op

revision: str = "3d1e2a4b5c6d"
down_revision: Union[str, Sequence[str], None] = "c7e8f9a0b1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE items ALTER COLUMN embedding TYPE jsonb "
        "USING (CASE WHEN embedding IS NULL THEN NULL "
        "ELSE (embedding::text)::jsonb END)"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE items ALTER COLUMN embedding TYPE vector(512) "
        "USING (CASE WHEN embedding IS NULL THEN NULL "
        "ELSE (embedding::text)::vector(512) END)"
    )
