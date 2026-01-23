"""Fix material column defaults for existing records

This migration:
- Sets default values for min_stock_level, quantity, and other required fields
- Ensures all existing materials have valid values

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-01-23 06:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Set default values for existing records that have NULL
    # min_stock_level - set to 0 if NULL
    op.execute("""
        UPDATE materials 
        SET min_stock_level = 0 
        WHERE min_stock_level IS NULL
    """)
    
    # quantity - set to 0 if NULL
    op.execute("""
        UPDATE materials 
        SET quantity = 0 
        WHERE quantity IS NULL
    """)
    
    # unit_of_measure - set to 'units' if NULL or empty
    op.execute("""
        UPDATE materials 
        SET unit_of_measure = 'units' 
        WHERE unit_of_measure IS NULL OR unit_of_measure = ''
    """)
    
    # item_number - ensure it's not NULL (should already have value from rename)
    op.execute("""
        UPDATE materials 
        SET item_number = COALESCE(item_number, 'MAT-' || id::text)
        WHERE item_number IS NULL OR item_number = ''
    """)
    
    # title - ensure it's not NULL (should already have value from rename)
    op.execute("""
        UPDATE materials 
        SET title = COALESCE(title, 'Material ' || id::text)
        WHERE title IS NULL OR title = ''
    """)
    
    # Ensure NOT NULL constraints are met with server defaults
    # Check if columns exist and update them
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='materials' AND column_name='min_stock_level'
    """))
    if result.fetchone():
        op.alter_column('materials', 'min_stock_level', 
                       nullable=False, 
                       server_default='0',
                       existing_type=sa.Numeric(14, 4))
    
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='materials' AND column_name='quantity'
    """))
    if result.fetchone():
        op.alter_column('materials', 'quantity', 
                       nullable=False, 
                       server_default='0',
                       existing_type=sa.Numeric(14, 4))
    
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='materials' AND column_name='unit_of_measure'
    """))
    if result.fetchone():
        op.alter_column('materials', 'unit_of_measure', 
                       nullable=False, 
                       server_default='units',
                       existing_type=sa.String(20))


def downgrade() -> None:
    # Remove server defaults (but keep NOT NULL)
    op.alter_column('materials', 'min_stock_level', server_default=None)
    op.alter_column('materials', 'quantity', server_default=None)
    op.alter_column('materials', 'unit_of_measure', server_default=None)
