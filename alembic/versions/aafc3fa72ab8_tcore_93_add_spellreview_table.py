"""tcore_93_add_spellreview_table

Revision ID: aafc3fa72ab8
Revises: b3f2a91d7c4e
Create Date: 2026-09-25 00:25:46.380419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'aafc3fa72ab8'
down_revision: Union[str, Sequence[str], None] = 'b3f2a91d7c4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('spellreview',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('spell_id', sa.UUID(), nullable=False),
    sa.Column('submitted_by', sa.UUID(), nullable=True),
    sa.Column('reviewed_by', sa.UUID(), nullable=True),
    sa.Column('status', sa.String(), server_default='pending', nullable=False),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['reviewed_by'], ['accounts.users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['spell_id'], ['spellcast.spell.id'], ),
    sa.ForeignKeyConstraint(['submitted_by'], ['accounts.users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    schema='spellcast'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('spellreview', schema='spellcast')
