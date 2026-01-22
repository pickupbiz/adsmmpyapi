"""Enhance barcode with PO integration and traceability

This migration:
- Adds new fields to barcode_labels for PO integration
- Adds new enum types for barcode entity types and traceability stages
- Creates barcode_templates table
- Updates barcode_scan_logs with PO context fields

Revision ID: 9f5g6h7i8j9k
Revises: 8e4f5g6h7i8j
Create Date: 2026-01-23 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9f5g6h7i8j9k'
down_revision: Union[str, None] = '8e4f5g6h7i8j'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create new enum types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE barcodeentitytype AS ENUM (
                'raw_material', 'wip', 'finished_goods', 'material_instance',
                'po_line_item', 'grn_line_item', 'inventory', 'part'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE traceabilitystage AS ENUM (
                'ordered', 'received', 'inspected', 'in_storage',
                'in_production', 'completed', 'consumed', 'shipped'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Add 'consumed' to existing barcodestatus enum if not exists
    op.execute("""
        DO $$ BEGIN
            ALTER TYPE barcodestatus ADD VALUE IF NOT EXISTS 'consumed';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create barcodetype enum if not exists (may already exist from initial barcode model)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE barcodetype AS ENUM (
                'code128', 'code39', 'qr_code', 'data_matrix', 'ean13', 'upc'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Define enum types for new columns
    barcodeentitytype_enum = postgresql.ENUM(
        'raw_material', 'wip', 'finished_goods', 'material_instance',
        'po_line_item', 'grn_line_item', 'inventory', 'part',
        name='barcodeentitytype', create_type=False
    )
    
    traceabilitystage_enum = postgresql.ENUM(
        'ordered', 'received', 'inspected', 'in_storage',
        'in_production', 'completed', 'consumed', 'shipped',
        name='traceabilitystage', create_type=False
    )
    
    barcodetype_enum = postgresql.ENUM(
        'code128', 'code39', 'qr_code', 'data_matrix', 'ean13', 'upc',
        name='barcodetype', create_type=False
    )
    
    # Alter entity_type column from string to enum
    # First add new column, copy data, drop old, rename
    op.add_column('barcode_labels',
        sa.Column('entity_type_new', barcodeentitytype_enum, nullable=True)
    )
    
    # Map old string values to new enum values
    op.execute("""
        UPDATE barcode_labels 
        SET entity_type_new = CASE 
            WHEN entity_type = 'material' THEN 'raw_material'::barcodeentitytype
            WHEN entity_type = 'inventory' THEN 'inventory'::barcodeentitytype
            WHEN entity_type = 'part' THEN 'part'::barcodeentitytype
            ELSE 'raw_material'::barcodeentitytype
        END
    """)
    
    # Drop old column and rename new
    op.drop_column('barcode_labels', 'entity_type')
    op.alter_column('barcode_labels', 'entity_type_new', new_column_name='entity_type')
    op.alter_column('barcode_labels', 'entity_type', nullable=False)
    
    # Add traceability_stage column
    op.add_column('barcode_labels',
        sa.Column('traceability_stage', traceabilitystage_enum, server_default='received', nullable=False)
    )
    
    # Add PO integration columns
    op.add_column('barcode_labels', sa.Column('purchase_order_id', sa.Integer(), nullable=True))
    op.add_column('barcode_labels', sa.Column('po_line_item_id', sa.Integer(), nullable=True))
    op.add_column('barcode_labels', sa.Column('grn_id', sa.Integer(), nullable=True))
    op.add_column('barcode_labels', sa.Column('material_instance_id', sa.Integer(), nullable=True))
    op.add_column('barcode_labels', sa.Column('po_number', sa.String(50), nullable=True))
    op.add_column('barcode_labels', sa.Column('grn_number', sa.String(50), nullable=True))
    
    # Add material details columns
    op.add_column('barcode_labels', sa.Column('material_id', sa.Integer(), nullable=True))
    op.add_column('barcode_labels', sa.Column('material_part_number', sa.String(100), nullable=True))
    op.add_column('barcode_labels', sa.Column('material_name', sa.String(200), nullable=True))
    op.add_column('barcode_labels', sa.Column('specification', sa.String(200), nullable=True))
    
    # Add additional tracking columns
    op.add_column('barcode_labels', sa.Column('heat_number', sa.String(100), nullable=True))
    op.add_column('barcode_labels', sa.Column('initial_quantity', sa.Float(), nullable=True))
    op.add_column('barcode_labels', sa.Column('current_quantity', sa.Float(), nullable=True))
    op.add_column('barcode_labels', sa.Column('unit_of_measure', sa.String(20), nullable=True))
    
    # Add supplier columns
    op.add_column('barcode_labels', sa.Column('supplier_id', sa.Integer(), nullable=True))
    op.add_column('barcode_labels', sa.Column('supplier_name', sa.String(200), nullable=True))
    
    # Add date columns
    op.add_column('barcode_labels', sa.Column('manufacture_date', sa.Date(), nullable=True))
    op.add_column('barcode_labels', sa.Column('expiry_date', sa.Date(), nullable=True))
    op.add_column('barcode_labels', sa.Column('received_date', sa.Date(), nullable=True))
    
    # Add QR data column (JSON)
    op.add_column('barcode_labels', sa.Column('qr_data', postgresql.JSON(), nullable=True))
    
    # Add traceability chain column
    op.add_column('barcode_labels', sa.Column('parent_barcode_id', sa.Integer(), nullable=True))
    
    # Add location columns
    op.add_column('barcode_labels', sa.Column('current_location', sa.String(100), nullable=True))
    op.add_column('barcode_labels', sa.Column('bin_number', sa.String(50), nullable=True))
    
    # Add reference columns
    op.add_column('barcode_labels', sa.Column('project_reference', sa.String(100), nullable=True))
    op.add_column('barcode_labels', sa.Column('work_order_reference', sa.String(100), nullable=True))
    
    # Add last_scan_action column
    op.add_column('barcode_labels', sa.Column('last_scan_action', sa.String(50), nullable=True))
    
    # Create foreign keys
    op.create_foreign_key('fk_barcode_labels_purchase_order_id', 'barcode_labels',
        'purchase_orders', ['purchase_order_id'], ['id'])
    op.create_foreign_key('fk_barcode_labels_po_line_item_id', 'barcode_labels',
        'po_line_items', ['po_line_item_id'], ['id'])
    op.create_foreign_key('fk_barcode_labels_grn_id', 'barcode_labels',
        'goods_receipt_notes', ['grn_id'], ['id'])
    op.create_foreign_key('fk_barcode_labels_material_instance_id', 'barcode_labels',
        'material_instances', ['material_instance_id'], ['id'])
    op.create_foreign_key('fk_barcode_labels_material_id', 'barcode_labels',
        'materials', ['material_id'], ['id'])
    op.create_foreign_key('fk_barcode_labels_supplier_id', 'barcode_labels',
        'suppliers', ['supplier_id'], ['id'])
    op.create_foreign_key('fk_barcode_labels_parent_barcode_id', 'barcode_labels',
        'barcode_labels', ['parent_barcode_id'], ['id'])
    
    # Create indexes
    op.create_index('ix_barcode_labels_purchase_order_id', 'barcode_labels', ['purchase_order_id'])
    op.create_index('ix_barcode_labels_material_instance_id', 'barcode_labels', ['material_instance_id'])
    op.create_index('ix_barcode_labels_po_number', 'barcode_labels', ['po_number'])
    op.create_index('ix_barcode_labels_heat_number', 'barcode_labels', ['heat_number'])
    
    # ==========================================================================
    # Update barcode_scan_logs table
    # ==========================================================================
    
    # Add PO context columns
    op.add_column('barcode_scan_logs', sa.Column('purchase_order_id', sa.Integer(), nullable=True))
    op.add_column('barcode_scan_logs', sa.Column('grn_id', sa.Integer(), nullable=True))
    
    # Add quantity tracking columns
    op.add_column('barcode_scan_logs', sa.Column('quantity_scanned', sa.Float(), nullable=True))
    op.add_column('barcode_scan_logs', sa.Column('quantity_before', sa.Float(), nullable=True))
    op.add_column('barcode_scan_logs', sa.Column('quantity_after', sa.Float(), nullable=True))
    
    # Add status/stage change columns
    op.add_column('barcode_scan_logs', sa.Column('status_before', sa.String(50), nullable=True))
    op.add_column('barcode_scan_logs', sa.Column('status_after', sa.String(50), nullable=True))
    op.add_column('barcode_scan_logs', sa.Column('stage_before', sa.String(50), nullable=True))
    op.add_column('barcode_scan_logs', sa.Column('stage_after', sa.String(50), nullable=True))
    
    # Add location change columns
    op.add_column('barcode_scan_logs', sa.Column('location_from', sa.String(100), nullable=True))
    op.add_column('barcode_scan_logs', sa.Column('location_to', sa.String(100), nullable=True))
    
    # Add validation result column (JSON)
    op.add_column('barcode_scan_logs', sa.Column('validation_result', postgresql.JSON(), nullable=True))
    
    # Add reference type column
    op.add_column('barcode_scan_logs', sa.Column('reference_type', sa.String(50), nullable=True))
    
    # Add client info columns
    op.add_column('barcode_scan_logs', sa.Column('ip_address', sa.String(50), nullable=True))
    op.add_column('barcode_scan_logs', sa.Column('user_agent', sa.String(255), nullable=True))
    
    # Create foreign keys for scan logs
    op.create_foreign_key('fk_barcode_scan_logs_purchase_order_id', 'barcode_scan_logs',
        'purchase_orders', ['purchase_order_id'], ['id'])
    op.create_foreign_key('fk_barcode_scan_logs_grn_id', 'barcode_scan_logs',
        'goods_receipt_notes', ['grn_id'], ['id'])
    
    # ==========================================================================
    # Create barcode_templates table
    # ==========================================================================
    
    # Use VARCHAR for barcode_type and entity_type to avoid enum issues
    # Validation is handled in the application layer
    op.create_table('barcode_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('barcode_type', sa.String(50), nullable=False),  # 'code128', 'qr_code', etc.
        sa.Column('entity_type', sa.String(50), nullable=False),   # 'raw_material', 'wip', etc.
        sa.Column('format_pattern', sa.String(255), nullable=False),
        sa.Column('prefix', sa.String(20), nullable=False),
        sa.Column('sequence_start', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('sequence_current', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sequence_padding', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('qr_data_template', postgresql.JSON(), nullable=True),
        sa.Column('include_po_reference', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('include_material_details', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('include_lot_info', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('include_dates', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('include_supplier', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_barcode_templates_id', 'barcode_templates', ['id'])
    op.create_index('ix_barcode_templates_name', 'barcode_templates', ['name'], unique=True)
    
    # Insert default templates (using VARCHAR values)
    op.execute("""
        INSERT INTO barcode_templates (name, description, barcode_type, entity_type, format_pattern, prefix)
        VALUES 
            ('Raw Material', 'Default template for raw materials received from PO', 'qr_code', 'raw_material', '{prefix}-{po_number}-{date}-{seq}', 'RM'),
            ('WIP', 'Default template for Work in Progress items', 'qr_code', 'wip', '{prefix}-{wo}-{date}-{seq}', 'WIP'),
            ('Finished Goods', 'Default template for finished goods', 'qr_code', 'finished_goods', '{prefix}-{part}-{sn}', 'FG'),
            ('Inventory', 'Default template for inventory items', 'code128', 'inventory', '{prefix}-{material}-{lot}-{seq}', 'INV')
    """)


def downgrade() -> None:
    # Drop barcode_templates table
    op.drop_index('ix_barcode_templates_name', table_name='barcode_templates')
    op.drop_index('ix_barcode_templates_id', table_name='barcode_templates')
    op.drop_table('barcode_templates')
    
    # Drop foreign keys from barcode_scan_logs
    op.drop_constraint('fk_barcode_scan_logs_grn_id', 'barcode_scan_logs', type_='foreignkey')
    op.drop_constraint('fk_barcode_scan_logs_purchase_order_id', 'barcode_scan_logs', type_='foreignkey')
    
    # Drop new columns from barcode_scan_logs
    op.drop_column('barcode_scan_logs', 'user_agent')
    op.drop_column('barcode_scan_logs', 'ip_address')
    op.drop_column('barcode_scan_logs', 'reference_type')
    op.drop_column('barcode_scan_logs', 'validation_result')
    op.drop_column('barcode_scan_logs', 'location_to')
    op.drop_column('barcode_scan_logs', 'location_from')
    op.drop_column('barcode_scan_logs', 'stage_after')
    op.drop_column('barcode_scan_logs', 'stage_before')
    op.drop_column('barcode_scan_logs', 'status_after')
    op.drop_column('barcode_scan_logs', 'status_before')
    op.drop_column('barcode_scan_logs', 'quantity_after')
    op.drop_column('barcode_scan_logs', 'quantity_before')
    op.drop_column('barcode_scan_logs', 'quantity_scanned')
    op.drop_column('barcode_scan_logs', 'grn_id')
    op.drop_column('barcode_scan_logs', 'purchase_order_id')
    
    # Drop indexes from barcode_labels
    op.drop_index('ix_barcode_labels_heat_number', table_name='barcode_labels')
    op.drop_index('ix_barcode_labels_po_number', table_name='barcode_labels')
    op.drop_index('ix_barcode_labels_material_instance_id', table_name='barcode_labels')
    op.drop_index('ix_barcode_labels_purchase_order_id', table_name='barcode_labels')
    
    # Drop foreign keys from barcode_labels
    op.drop_constraint('fk_barcode_labels_parent_barcode_id', 'barcode_labels', type_='foreignkey')
    op.drop_constraint('fk_barcode_labels_supplier_id', 'barcode_labels', type_='foreignkey')
    op.drop_constraint('fk_barcode_labels_material_id', 'barcode_labels', type_='foreignkey')
    op.drop_constraint('fk_barcode_labels_material_instance_id', 'barcode_labels', type_='foreignkey')
    op.drop_constraint('fk_barcode_labels_grn_id', 'barcode_labels', type_='foreignkey')
    op.drop_constraint('fk_barcode_labels_po_line_item_id', 'barcode_labels', type_='foreignkey')
    op.drop_constraint('fk_barcode_labels_purchase_order_id', 'barcode_labels', type_='foreignkey')
    
    # Drop new columns from barcode_labels
    op.drop_column('barcode_labels', 'last_scan_action')
    op.drop_column('barcode_labels', 'work_order_reference')
    op.drop_column('barcode_labels', 'project_reference')
    op.drop_column('barcode_labels', 'bin_number')
    op.drop_column('barcode_labels', 'current_location')
    op.drop_column('barcode_labels', 'parent_barcode_id')
    op.drop_column('barcode_labels', 'qr_data')
    op.drop_column('barcode_labels', 'received_date')
    op.drop_column('barcode_labels', 'expiry_date')
    op.drop_column('barcode_labels', 'manufacture_date')
    op.drop_column('barcode_labels', 'supplier_name')
    op.drop_column('barcode_labels', 'supplier_id')
    op.drop_column('barcode_labels', 'unit_of_measure')
    op.drop_column('barcode_labels', 'current_quantity')
    op.drop_column('barcode_labels', 'initial_quantity')
    op.drop_column('barcode_labels', 'heat_number')
    op.drop_column('barcode_labels', 'specification')
    op.drop_column('barcode_labels', 'material_name')
    op.drop_column('barcode_labels', 'material_part_number')
    op.drop_column('barcode_labels', 'material_id')
    op.drop_column('barcode_labels', 'grn_number')
    op.drop_column('barcode_labels', 'po_number')
    op.drop_column('barcode_labels', 'material_instance_id')
    op.drop_column('barcode_labels', 'grn_id')
    op.drop_column('barcode_labels', 'po_line_item_id')
    op.drop_column('barcode_labels', 'purchase_order_id')
    op.drop_column('barcode_labels', 'traceability_stage')
    
    # Revert entity_type to string
    op.add_column('barcode_labels', sa.Column('entity_type_old', sa.String(50), nullable=True))
    op.execute("UPDATE barcode_labels SET entity_type_old = entity_type::text")
    op.drop_column('barcode_labels', 'entity_type')
    op.alter_column('barcode_labels', 'entity_type_old', new_column_name='entity_type')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS traceabilitystage")
    op.execute("DROP TYPE IF EXISTS barcodeentitytype")
