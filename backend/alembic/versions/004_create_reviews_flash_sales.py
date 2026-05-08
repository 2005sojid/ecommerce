from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision: str = '004_reviews_flash'
down_revision: Union[str, None] = '003_orders'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('reviews', sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False), sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False), sa.Column('rating', sa.Integer(), nullable=False), sa.Column('comment', sa.Text(), nullable=True), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_reviews_rating_range'), sa.UniqueConstraint('user_id', 'product_id', name='uq_reviews_user_product'))
    op.create_table('flash_sales', sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False), sa.Column('sale_price', sa.Numeric(10, 2), nullable=False), sa.Column('original_price', sa.Numeric(10, 2), nullable=False), sa.Column('start_at', sa.DateTime(timezone=True), nullable=False), sa.Column('end_at', sa.DateTime(timezone=True), nullable=False), sa.Column('initial_stock', sa.Integer(), nullable=False), sa.Column('remaining_stock', sa.Integer(), nullable=False), sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.false()))

def downgrade() -> None:
    op.drop_table('flash_sales')
    op.drop_table('reviews')
