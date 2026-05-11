from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '011_returns'
down_revision: Union[str, None] = '010_coupons'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'returns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('order_id', sa.String(length=20), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('refund_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('admin_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_returns_order_id', 'returns', ['order_id'])
    op.create_index('ix_returns_user_id', 'returns', ['user_id'])
    op.create_index('ix_returns_status', 'returns', ['status'])


def downgrade() -> None:
    op.drop_index('ix_returns_status', table_name='returns')
    op.drop_index('ix_returns_user_id', table_name='returns')
    op.drop_index('ix_returns_order_id', table_name='returns')
    op.drop_table('returns')
