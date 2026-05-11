from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision: str = '010_coupons'
down_revision: Union[str, None] = '009_notifications'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'coupons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('discount_type', sa.String(length=20), nullable=False),
        sa.Column('discount_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('scope', sa.String(length=20), nullable=False, server_default='platform'),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sellers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('min_order_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('used_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_coupons_code', 'coupons', ['code'], unique=True)
    op.create_index('ix_coupons_seller_id', 'coupons', ['seller_id'])

    op.create_table(
        'coupon_usages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('coupon_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('coupons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_id', sa.String(length=20), sa.ForeignKey('orders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('coupon_id', 'user_id', 'order_id', name='uq_coupon_usage'),
    )
    op.create_index('ix_coupon_usages_coupon_id', 'coupon_usages', ['coupon_id'])
    op.create_index('ix_coupon_usages_user_id', 'coupon_usages', ['user_id'])
    op.create_index('ix_coupon_usages_order_id', 'coupon_usages', ['order_id'])


def downgrade() -> None:
    op.drop_index('ix_coupon_usages_order_id', table_name='coupon_usages')
    op.drop_index('ix_coupon_usages_user_id', table_name='coupon_usages')
    op.drop_index('ix_coupon_usages_coupon_id', table_name='coupon_usages')
    op.drop_table('coupon_usages')
    op.drop_index('ix_coupons_seller_id', table_name='coupons')
    op.drop_index('ix_coupons_code', table_name='coupons')
    op.drop_table('coupons')
