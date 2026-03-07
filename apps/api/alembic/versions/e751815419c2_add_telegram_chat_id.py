"""add telegram_chat_id

Revision ID: e751815419c2
Revises: a1b2c3d4e5f6
Create Date: 2026-03-07 16:35:49.450782
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers
revision: str = 'e751815419c2'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('telegram_chat_id', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_users_telegram_chat_id'), 'users', ['telegram_chat_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_telegram_chat_id'), table_name='users')
    op.drop_column('users', 'telegram_chat_id')
