from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision: str = '001_users'
down_revision: Union[str, None] = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('users', sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('email', sa.String(255), nullable=False), sa.Column('password_hash', sa.String(255), nullable=False), sa.Column('name', sa.String(100), nullable=False), sa.Column('role', sa.Enum('customer', 'admin', name='user_role'), nullable=False, server_default='customer'), sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True), sa.UniqueConstraint('email', name='uq_users_email'))
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

def downgrade() -> None:
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
    sa.Enum(name='user_role').drop(op.get_bind(), checkfirst=True)
