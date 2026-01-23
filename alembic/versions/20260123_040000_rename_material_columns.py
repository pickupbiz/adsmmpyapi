"""Rename material columns: part_number to item_number, name to title

This migration:
- Renames part_number column to item_number in materials table
- Renames name column to title in materials table
- Updates indexes accordingly
- Adds new columns for PO integration if they don't exist

Revision ID: a0b1c2d3e4f5
Revises: 9f5g6h7i8j9k
Create Date: 2026-01-23 04:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a0b1c2d3e4f5'
down_revision: Union[str, None] = '0a6b7c8d9e0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if columns exist before renaming
    conn = op.get_bind()
    
    # Check if part_number exists (old column name)
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='materials' AND column_name='part_number'
    """))
    has_part_number = result.fetchone() is not None
    
    # Check if item_number exists (new column name)
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='materials' AND column_name='item_number'
    """))
    has_item_number = result.fetchone() is not None
    
    # Check if name exists (old column name)
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='materials' AND column_name='name'
    """))
    has_name = result.fetchone() is not None
    
    # Check if title exists (new column name)
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='materials' AND column_name='title'
    """))
    has_title = result.fetchone() is not None
    
    # Rename part_number to item_number if needed
    if has_part_number and not has_item_number:
        # Drop old index if exists
        op.drop_index('ix_materials_part_number', table_name='materials', if_exists=True)
        # Rename column
        op.alter_column('materials', 'part_number',
                       new_column_name='item_number',
                       existing_type=sa.String(length=100),
                       existing_nullable=False)
        # Create new index
        op.create_index('ix_materials_item_number', 'materials', ['item_number'], unique=True)
    elif not has_item_number:
        # Column doesn't exist, create it
        op.add_column('materials', sa.Column('item_number', sa.String(length=100), nullable=False, server_default=''))
        op.create_index('ix_materials_item_number', 'materials', ['item_number'], unique=True)
    
    # Rename name to title if needed
    if has_name and not has_title:
        # Drop old index if exists
        op.drop_index('ix_materials_name', table_name='materials', if_exists=True)
        # Rename column
        op.alter_column('materials', 'name',
                       new_column_name='title',
                       existing_type=sa.String(length=200),
                       existing_nullable=False)
        # Create new index
        op.create_index('ix_materials_title', 'materials', ['title'], unique=False)
    elif not has_title:
        # Column doesn't exist, create it
        op.add_column('materials', sa.Column('title', sa.String(length=200), nullable=False, server_default=''))
        op.create_index('ix_materials_title', 'materials', ['title'], unique=False)
    
    # Add new columns for PO integration if they don't exist
    new_columns = [
        ('heat_number', sa.String(length=100), True),
        ('batch_number', sa.String(length=100), True),
        ('quantity', sa.Numeric(precision=14, scale=4), False),
        ('min_stock_level', sa.Numeric(precision=14, scale=4), True),
        ('max_stock_level', sa.Numeric(precision=14, scale=4), True),
        ('po_id', sa.Integer(), True),
        ('po_line_item_id', sa.Integer(), True),
        ('supplier_id', sa.Integer(), True),
        ('supplier_batch_number', sa.String(length=100), True),
        ('project_id', sa.Integer(), True),
        ('location', sa.String(length=200), True),
        ('storage_bin', sa.String(length=100), True),
        ('received_date', sa.DateTime(), True),
        ('inspection_date', sa.DateTime(), True),
        ('issued_date', sa.DateTime(), True),
        ('production_start_date', sa.DateTime(), True),
        ('completion_date', sa.DateTime(), True),
        ('qa_status', sa.String(length=50), True),
        ('qa_inspected_by', sa.Integer(), True),
        ('certificate_number', sa.String(length=100), True),
        ('barcode_id', sa.Integer(), True),
    ]
    
    for col_name, col_type, nullable in new_columns:
        result = conn.execute(sa.text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='materials' AND column_name='{col_name}'
        """))
        if result.fetchone() is None:
            if nullable:
                op.add_column('materials', sa.Column(col_name, col_type, nullable=True))
            else:
                # For non-nullable columns, add with default value
                if isinstance(col_type, sa.Numeric):
                    op.add_column('materials', sa.Column(col_name, col_type, nullable=False, server_default='0'))
                else:
                    op.add_column('materials', sa.Column(col_name, col_type, nullable=False, server_default=''))
    
    # Update material_type enum if needed (RAW, WIP, FINISHED)
    # PostgreSQL doesn't support IF NOT EXISTS for ALTER TYPE ADD VALUE
    # So we check first and only add if missing
    try:
        result = conn.execute(sa.text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'materialtype')
            ORDER BY enumsortorder
        """))
        existing_values = [row[0] for row in result.fetchall()]
        
        # Add new enum values if they don't exist
        if 'RAW' not in existing_values:
            op.execute("ALTER TYPE materialtype ADD VALUE 'RAW'")
        if 'WIP' not in existing_values:
            op.execute("ALTER TYPE materialtype ADD VALUE 'WIP'")
        if 'FINISHED' not in existing_values:
            op.execute("ALTER TYPE materialtype ADD VALUE 'FINISHED'")
    except Exception:
        # Enum might not exist or already have values, continue
        pass
    
    # Update materialstatus enum if needed
    try:
        result = conn.execute(sa.text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'materialstatus')
            ORDER BY enumsortorder
        """))
        existing_status_values = [row[0] for row in result.fetchall()]
        
        # Add new status values if they don't exist
        new_statuses = ['ORDERED', 'RECEIVED', 'IN_INSPECTION', 'IN_STORAGE', 'ISSUED', 'IN_PRODUCTION', 'COMPLETED', 'REJECTED']
        for status in new_statuses:
            if status not in existing_status_values:
                try:
                    op.execute(f"ALTER TYPE materialstatus ADD VALUE '{status}'")
                except Exception:
                    # Value might already exist, continue
                    pass
    except Exception:
        # Enum might not exist, continue
        pass
    
    # Add foreign key constraints if they don't exist
    # Check and add po_id foreign key
    result = conn.execute(sa.text("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name='materials' AND constraint_name='fk_materials_po_id_purchase_orders'
    """))
    if result.fetchone() is None:
        op.create_foreign_key('fk_materials_po_id_purchase_orders', 'materials', 'purchase_orders', ['po_id'], ['id'])
    
    # Check and add po_line_item_id foreign key
    result = conn.execute(sa.text("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name='materials' AND constraint_name='fk_materials_po_line_item_id_po_line_items'
    """))
    if result.fetchone() is None:
        op.create_foreign_key('fk_materials_po_line_item_id_po_line_items', 'materials', 'po_line_items', ['po_line_item_id'], ['id'])
    
    # Check and add supplier_id foreign key (if not already exists)
    result = conn.execute(sa.text("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name='materials' AND constraint_name='fk_materials_supplier_id_suppliers'
    """))
    if result.fetchone() is None:
        op.create_foreign_key('fk_materials_supplier_id_suppliers', 'materials', 'suppliers', ['supplier_id'], ['id'])
    
    # Check and add project_id foreign key
    result = conn.execute(sa.text("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name='materials' AND constraint_name='fk_materials_project_id_projects'
    """))
    if result.fetchone() is None:
        op.create_foreign_key('fk_materials_project_id_projects', 'materials', 'projects', ['project_id'], ['id'])
    
    # Check and add qa_inspected_by foreign key
    result = conn.execute(sa.text("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name='materials' AND constraint_name='fk_materials_qa_inspected_by_users'
    """))
    if result.fetchone() is None:
        op.create_foreign_key('fk_materials_qa_inspected_by_users', 'materials', 'users', ['qa_inspected_by'], ['id'])
    
    # Check and add barcode_id foreign key
    result = conn.execute(sa.text("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name='materials' AND constraint_name='fk_materials_barcode_id_barcode_labels'
    """))
    if result.fetchone() is None:
        op.create_foreign_key('fk_materials_barcode_id_barcode_labels', 'materials', 'barcode_labels', ['barcode_id'], ['id'])


def downgrade() -> None:
    # Rename item_number back to part_number
    op.drop_index('ix_materials_item_number', table_name='materials', if_exists=True)
    op.alter_column('materials', 'item_number',
                   new_column_name='part_number',
                   existing_type=sa.String(length=100),
                   existing_nullable=False)
    op.create_index('ix_materials_part_number', 'materials', ['part_number'], unique=True)
    
    # Rename title back to name
    op.drop_index('ix_materials_title', table_name='materials', if_exists=True)
    op.alter_column('materials', 'title',
                   new_column_name='name',
                   existing_type=sa.String(length=200),
                   existing_nullable=False)
    op.create_index('ix_materials_name', 'materials', ['name'], unique=False)
    
    # Drop foreign key constraints
    op.drop_constraint('fk_materials_barcode_id_barcode_labels', 'materials', type_='foreignkey')
    op.drop_constraint('fk_materials_qa_inspected_by_users', 'materials', type_='foreignkey')
    op.drop_constraint('fk_materials_project_id_projects', 'materials', type_='foreignkey')
    op.drop_constraint('fk_materials_supplier_id_suppliers', 'materials', type_='foreignkey')
    op.drop_constraint('fk_materials_po_line_item_id_po_line_items', 'materials', type_='foreignkey')
    op.drop_constraint('fk_materials_po_id_purchase_orders', 'materials', type_='foreignkey')
    
    # Drop new columns
    columns_to_drop = [
        'heat_number', 'batch_number', 'quantity', 'min_stock_level', 'max_stock_level',
        'po_id', 'po_line_item_id', 'supplier_id', 'supplier_batch_number', 'project_id',
        'location', 'storage_bin', 'received_date', 'inspection_date', 'issued_date',
        'production_start_date', 'completion_date', 'qa_status', 'qa_inspected_by',
        'certificate_number', 'barcode_id'
    ]
    
    for col_name in columns_to_drop:
        op.drop_column('materials', col_name, if_exists=True)
