from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '014_product_images'
down_revision: Union[str, None] = '013_review_depth'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'product_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('alt', sa.String(255), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_product_images_product_id', 'product_images', ['product_id'])


def downgrade() -> None:
    op.drop_index('ix_product_images_product_id', table_name='product_images')
    op.drop_table('product_images')
