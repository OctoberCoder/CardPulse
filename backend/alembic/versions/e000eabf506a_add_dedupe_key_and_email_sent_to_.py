"""add dedupe_key and email_sent to notifications

Revision ID: e000eabf506a
Revises: 001_initial
Create Date: 2026-06-08 03:46:44.373915

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e000eabf506a'
down_revision: Union[str, Sequence[str], None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('notifications', sa.Column('dedupe_key', sa.String(255), nullable=True))
    op.create_index('ix_notifications_dedupe_key', 'notifications', ['dedupe_key'])
    op.add_column('notifications', sa.Column('email_sent', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    op.drop_column('notifications', 'email_sent')
    op.drop_index('ix_notifications_dedupe_key', table_name='notifications')
    op.drop_column('notifications', 'dedupe_key')
