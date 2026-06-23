"""add consent audit action

Revision ID: e3d89e75cb1c
Revises: 9fc8fec44ae1
Create Date: 2026-06-22 19:34:57.472455

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3d89e75cb1c'
down_revision: Union[str, Sequence[str], None] = '9fc8fec44ae1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add 'consent' value to the audit_action enum."""
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE audit_action ADD VALUE 'consent'")


def downgrade() -> None:
    """PostgreSQL does not support removing enum values; no-op."""
    pass
