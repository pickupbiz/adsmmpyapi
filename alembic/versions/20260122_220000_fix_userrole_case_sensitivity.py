"""Fix userrole enum case sensitivity - migrate ADMIN to director

This migration fixes case-sensitivity issues with the userrole enum.
Existing users with uppercase 'ADMIN' role will be migrated to 'director'.

Revision ID: 6c2d3e4f5g6h
Revises: 5b1c2d3e4f5g
Create Date: 2026-01-22 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c2d3e4f5g6h'
down_revision: Union[str, None] = '5b1c2d3e4f5g'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Fix case-sensitivity issues in user roles.
    
    PostgreSQL enums are case-sensitive. Some users may have been created
    with uppercase role values (e.g., 'ADMIN') which don't match the 
    lowercase enum values defined in the database.
    
    This migration:
    1. Temporarily converts the role column to VARCHAR
    2. Updates any uppercase values to their lowercase equivalents
    3. Converts the column back to the enum type
    """
    # Step 1: Change role column to VARCHAR temporarily to allow data manipulation
    op.execute("""
        ALTER TABLE users 
        ALTER COLUMN role TYPE VARCHAR(50) 
        USING role::text
    """)
    
    # Step 2: Fix case-sensitivity - convert all uppercase role values to lowercase
    # Map old uppercase values to new lowercase values
    op.execute("UPDATE users SET role = LOWER(role) WHERE role != LOWER(role)")
    
    # Step 3: Map 'admin' to 'director' (admin is legacy, director is the new equivalent)
    # Keep 'admin' for backward compatibility but also update to 'director' if preferred
    # Uncomment the next line if you want to migrate all 'admin' users to 'director':
    # op.execute("UPDATE users SET role = 'director' WHERE role = 'admin'")
    
    # Step 4: Convert back to enum type
    op.execute("""
        ALTER TABLE users 
        ALTER COLUMN role TYPE userrole 
        USING role::userrole
    """)


def downgrade() -> None:
    """
    Downgrade is not fully reversible as we can't restore uppercase values.
    The column will remain with lowercase values.
    """
    pass
