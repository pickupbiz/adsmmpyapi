"""Add new userrole enum values

Revision ID: 5b1c2d3e4f5g
Revises: 4aeaf6096159
Create Date: 2026-01-22 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b1c2d3e4f5g'
down_revision: Union[str, None] = 'e78c7c8b52c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new values to userrole enum
    # PostgreSQL requires ALTER TYPE to add new enum values
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'admin'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'director'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'head_of_operations'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'store'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'purchase'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'qa'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values easily
    # Would need to recreate the enum type
    pass
