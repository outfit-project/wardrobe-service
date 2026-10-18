"""Persist the photo-processing lifecycle and allow image-only uploads."""
from alembic import op
import sqlalchemy as sa

revision = '7f91c2d3e4a5'
down_revision = '3d1e2a4b5c6d'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('items','category',existing_type=sa.String(64),nullable=True)
    op.add_column('items',sa.Column('processing_status',sa.String(16),nullable=False,server_default='pending'))
    op.add_column('items',sa.Column('processing_error',sa.String(500),nullable=True))
    op.execute("UPDATE items SET processing_status = CASE WHEN embedding IS NOT NULL AND category IS NOT NULL THEN 'ready' ELSE 'failed' END")
    op.execute("UPDATE items SET processing_error = 'Existing photo needs processing. Please retry.' WHERE processing_status = 'failed'")
    op.create_check_constraint('ck_items_processing_status','items',"processing_status IN ('pending','processing','ready','failed')")


def downgrade():
    op.drop_constraint('ck_items_processing_status','items',type_='check')
    op.drop_column('items','processing_error')
    op.drop_column('items','processing_status')
    op.execute("UPDATE items SET category = 'accessory' WHERE category IS NULL")
    op.alter_column('items','category',existing_type=sa.String(64),nullable=False)
