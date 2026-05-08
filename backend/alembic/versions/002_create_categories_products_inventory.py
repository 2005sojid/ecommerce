from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision: str = '002_catalog'
down_revision: Union[str, None] = '001_users'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('categories', sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('name', sa.String(100), nullable=False), sa.Column('slug', sa.String(120), nullable=False), sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.UniqueConstraint('slug', name='uq_categories_slug'))
    op.create_index('ix_categories_slug', 'categories', ['slug'], unique=True)
    op.create_table('products', sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('name', sa.String(255), nullable=False), sa.Column('slug', sa.String(280), nullable=False), sa.Column('description', sa.Text(), nullable=True), sa.Column('price', sa.Numeric(10, 2), nullable=False), sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='RESTRICT'), nullable=False), sa.Column('image_url', sa.String(500), nullable=True), sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True), sa.UniqueConstraint('slug', name='uq_products_slug'))
    op.create_index('ix_products_slug', 'products', ['slug'], unique=True)
    op.create_table('inventory', sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False), sa.Column('quantity', sa.Integer(), nullable=False, server_default='0'), sa.Column('reserved', sa.Integer(), nullable=False, server_default='0'), sa.Column('warehouse_location', sa.String(50), nullable=True), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()), sa.UniqueConstraint('product_id', name='uq_inventory_product_id'))

def downgrade() -> None:
    op.drop_table('inventory')
    op.drop_index('ix_products_slug', table_name='products')
    op.drop_table('products')
    op.drop_index('ix_categories_slug', table_name='categories')
    op.drop_table('categories')
