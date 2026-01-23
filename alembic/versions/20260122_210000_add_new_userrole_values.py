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
    # IMPORTANT: Enum values must be committed before they can be used
    # We use a raw psycopg2 connection with autocommit enabled
    import psycopg2
    from urllib.parse import urlparse
    from app.core.config import settings
    
    # Parse database URL to get connection parameters
    parsed = urlparse(settings.DATABASE_URL)
    
    # Connect directly using psycopg2 with autocommit
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path[1:] if parsed.path else None,
        user=parsed.username,
        password=parsed.password
    )
    conn.autocommit = True
    
    statements = [
        "ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'admin'",
        "ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'director'",
        "ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'head_of_operations'",
        "ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'store'",
        "ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'purchase'",
        "ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'qa'",
    ]
    
    try:
        cursor = conn.cursor()
        for stmt in statements:
            cursor.execute(stmt)
        cursor.close()
    finally:
        conn.close()


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values easily
    # Would need to recreate the enum type
    pass
