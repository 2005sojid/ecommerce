from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision: str = '013_review_depth'
down_revision: Union[str, None] = '012_chat'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('reviews', sa.Column('is_approved', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('reviews', sa.Column('seller_response', sa.Text(), nullable=True))
    op.add_column('reviews', sa.Column('seller_response_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('reviews', sa.Column('helpful_count', sa.Integer(), nullable=False, server_default='0'))
    op.create_table('review_votes', sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('review_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reviews.id', ondelete='CASCADE'), nullable=False), sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False), sa.Column('vote', sa.SmallInteger(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.UniqueConstraint('review_id', 'user_id', name='uq_review_vote_user'))
    op.create_index('ix_review_votes_review_id', 'review_votes', ['review_id'])
    op.create_index('ix_review_votes_user_id', 'review_votes', ['user_id'])

def downgrade() -> None:
    op.drop_index('ix_review_votes_user_id', table_name='review_votes')
    op.drop_index('ix_review_votes_review_id', table_name='review_votes')
    op.drop_table('review_votes')
    op.drop_column('reviews', 'helpful_count')
    op.drop_column('reviews', 'seller_response_at')
    op.drop_column('reviews', 'seller_response')
    op.drop_column('reviews', 'is_approved')
