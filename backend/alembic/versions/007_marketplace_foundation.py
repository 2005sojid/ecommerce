from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision: str = '007_marketplace'
down_revision: Union[str, None] = '006_mv_daily_sales'
branch_labels = None
depends_on = None

def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'seller'")
    op.create_table('sellers', sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False), sa.Column('store_name', sa.String(150), nullable=False), sa.Column('slug', sa.String(180), nullable=False), sa.Column('description', sa.Text(), nullable=True), sa.Column('logo_url', sa.String(500), nullable=True), sa.Column('banner_url', sa.String(500), nullable=True), sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True), sa.UniqueConstraint('slug', name='uq_sellers_slug'), sa.UniqueConstraint('user_id', name='uq_sellers_user_id'))
    op.create_index('ix_sellers_slug', 'sellers', ['slug'], unique=True)
    op.create_index('ix_sellers_user_id', 'sellers', ['user_id'])
    op.create_table('addresses', sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False), sa.Column('label', sa.String(50), nullable=True), sa.Column('recipient_name', sa.String(150), nullable=False), sa.Column('line1', sa.String(255), nullable=False), sa.Column('line2', sa.String(255), nullable=True), sa.Column('city', sa.String(100), nullable=False), sa.Column('state', sa.String(100), nullable=True), sa.Column('postal_code', sa.String(20), nullable=False), sa.Column('country', sa.String(2), nullable=False), sa.Column('phone', sa.String(30), nullable=True), sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_addresses_user_id', 'addresses', ['user_id'])
    op.create_table('product_variants', sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False), sa.Column('sku', sa.String(64), nullable=False), sa.Column('variant_name', sa.String(150), nullable=False), sa.Column('attributes', postgresql.JSONB(), nullable=True), sa.Column('price', sa.Numeric(10, 2), nullable=False), sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='0'), sa.Column('reserved_quantity', sa.Integer(), nullable=False, server_default='0'), sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True), sa.UniqueConstraint('sku', name='uq_product_variants_sku'))
    op.create_index('ix_product_variants_sku', 'product_variants', ['sku'], unique=True)
    op.create_index('ix_product_variants_product_id', 'product_variants', ['product_id'])
    op.add_column('products', sa.Column('seller_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sellers.id', ondelete='SET NULL'), nullable=True))
    op.create_index('ix_products_seller_id', 'products', ['seller_id'])
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')
    op.execute("INSERT INTO product_variants (id, product_id, sku, variant_name, attributes, price, stock_quantity, reserved_quantity, is_active, created_at) SELECT gen_random_uuid(), p.id, 'SKU-' || REPLACE(p.id::text, '-', ''), 'Default', NULL, p.price, COALESCE(i.quantity, 0), COALESCE(i.reserved, 0), true, now() FROM products p LEFT JOIN inventory i ON i.product_id = p.id")

def downgrade() -> None:
    op.drop_index('ix_products_seller_id', table_name='products')
    op.drop_column('products', 'seller_id')
    op.drop_index('ix_product_variants_product_id', table_name='product_variants')
    op.drop_index('ix_product_variants_sku', table_name='product_variants')
    op.drop_table('product_variants')
    op.drop_index('ix_addresses_user_id', table_name='addresses')
    op.drop_table('addresses')
    op.drop_index('ix_sellers_user_id', table_name='sellers')
    op.drop_index('ix_sellers_slug', table_name='sellers')
    op.drop_table('sellers')
