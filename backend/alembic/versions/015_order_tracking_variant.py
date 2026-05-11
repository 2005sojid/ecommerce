from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '015_tracking_variant'
down_revision: Union[str, None] = '014_product_images'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'orders',
        sa.Column('tracking_number', sa.String(length=100), nullable=True),
    )
    op.add_column(
        'order_items',
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_order_items_variant_id',
        'order_items',
        'product_variants',
        ['variant_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index(
        'ix_order_items_variant_id',
        'order_items',
        ['variant_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_order_items_variant_id', table_name='order_items')
    op.drop_constraint('fk_order_items_variant_id', 'order_items', type_='foreignkey')
    op.drop_column('order_items', 'variant_id')
    op.drop_column('orders', 'tracking_number')
