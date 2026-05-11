from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '016_settlements'
down_revision: Union[str, None] = '015_tracking_variant'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'settlements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sellers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('settlement_date', sa.Date(), nullable=False),
        sa.Column('gross_revenue', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('fees', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('net_payout', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('order_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('seller_id', 'settlement_date', name='uq_settlement_seller_date'),
    )
    op.create_index('ix_settlements_seller_id', 'settlements', ['seller_id'])
    op.create_index('ix_settlements_settlement_date', 'settlements', ['settlement_date'])


def downgrade() -> None:
    op.drop_index('ix_settlements_settlement_date', table_name='settlements')
    op.drop_index('ix_settlements_seller_id', table_name='settlements')
    op.drop_table('settlements')
