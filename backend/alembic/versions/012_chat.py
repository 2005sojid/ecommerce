from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '012_chat'
down_revision: Union[str, None] = '011_returns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('buyer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sellers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('buyer_id', 'seller_id', name='uq_conversation_buyer_seller'),
    )
    op.create_index('ix_conversations_buyer_id', 'conversations', ['buyer_id'])
    op.create_index('ix_conversations_seller_id', 'conversations', ['seller_id'])

    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_messages_sender_user_id', 'messages', ['sender_user_id'])
    op.create_index('ix_messages_created_at', 'messages', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_messages_created_at', table_name='messages')
    op.drop_index('ix_messages_sender_user_id', table_name='messages')
    op.drop_index('ix_messages_conversation_id', table_name='messages')
    op.drop_table('messages')
    op.drop_index('ix_conversations_seller_id', table_name='conversations')
    op.drop_index('ix_conversations_buyer_id', table_name='conversations')
    op.drop_table('conversations')
