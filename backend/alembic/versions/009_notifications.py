from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision: str = '009_notifications'
down_revision: Union[str, None] = '008_wishlist'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('notifications', sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False), sa.Column('type', sa.String(length=50), nullable=False), sa.Column('title', sa.String(length=255), nullable=False), sa.Column('body', sa.Text(), nullable=True), sa.Column('link', sa.String(length=500), nullable=True), sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    op.create_index('ix_notifications_user_unread', 'notifications', ['user_id', 'is_read'])

def downgrade() -> None:
    op.drop_index('ix_notifications_user_unread', table_name='notifications')
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_table('notifications')
