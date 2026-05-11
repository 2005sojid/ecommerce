from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision: str = '008_wishlist'
down_revision: Union[str, None] = '007_marketplace'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('wishlists', sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False), sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.UniqueConstraint('user_id', 'product_id', name='uq_wishlist_user_product'))
    op.create_index('ix_wishlists_user_id', 'wishlists', ['user_id'])
    op.create_index('ix_wishlists_product_id', 'wishlists', ['product_id'])

def downgrade() -> None:
    op.drop_index('ix_wishlists_product_id', table_name='wishlists')
    op.drop_index('ix_wishlists_user_id', table_name='wishlists')
    op.drop_table('wishlists')
