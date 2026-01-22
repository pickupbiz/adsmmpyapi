"""Add material instance models with PO integration.

Revision ID: 8e4f5g6h7i8j
Revises: 7d3e4f5g6h7i
Create Date: 2026-01-23 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8e4f5g6h7i8j'
down_revision: Union[str, None] = '7d3e4f5g6h7i'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types (using DO block to handle IF NOT EXISTS in PostgreSQL)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE materiallifecyclestatus AS ENUM (
                'ordered', 'received', 'in_inspection', 'in_storage', 'reserved',
                'issued', 'in_production', 'completed', 'rejected', 'scrapped', 'returned'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE materialcondition AS ENUM (
                'new', 'serviceable', 'unserviceable', 'overhauled', 'repairable', 'scrap'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Define enum types with create_type=False since we created them above
    lifecycle_status_enum = postgresql.ENUM(
        'ordered', 'received', 'in_inspection', 'in_storage', 'reserved',
        'issued', 'in_production', 'completed', 'rejected', 'scrapped', 'returned',
        name='materiallifecyclestatus', create_type=False
    )
    
    condition_enum = postgresql.ENUM(
        'new', 'serviceable', 'unserviceable', 'overhauled', 'repairable', 'scrap',
        name='materialcondition', create_type=False
    )
    
    # Create material_instances table
    op.create_table('material_instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_number', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('purchase_order_id', sa.Integer(), nullable=True),
        sa.Column('po_line_item_id', sa.Integer(), nullable=True),
        sa.Column('grn_line_item_id', sa.Integer(), nullable=True),
        sa.Column('supplier_id', sa.Integer(), nullable=True),
        sa.Column('specification', sa.String(length=200), nullable=True),
        sa.Column('revision', sa.String(length=20), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('reserved_quantity', sa.Numeric(precision=14, scale=4), nullable=False, server_default='0'),
        sa.Column('issued_quantity', sa.Numeric(precision=14, scale=4), nullable=False, server_default='0'),
        sa.Column('unit_of_measure', sa.String(length=20), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('lot_number', sa.String(length=100), nullable=True),
        sa.Column('batch_number', sa.String(length=100), nullable=True),
        sa.Column('serial_number', sa.String(length=100), nullable=True),
        sa.Column('heat_number', sa.String(length=100), nullable=True),
        sa.Column('lifecycle_status', lifecycle_status_enum, nullable=False, server_default='ordered'),
        sa.Column('condition', condition_enum, nullable=False, server_default='new'),
        sa.Column('order_date', sa.Date(), nullable=True),
        sa.Column('received_date', sa.Date(), nullable=True),
        sa.Column('inspection_date', sa.Date(), nullable=True),
        sa.Column('manufacture_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('storage_location', sa.String(length=100), nullable=True),
        sa.Column('bin_number', sa.String(length=50), nullable=True),
        sa.Column('certificate_number', sa.String(length=100), nullable=True),
        sa.Column('certificate_received', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('inspection_passed', sa.Boolean(), nullable=True),
        sa.Column('inspection_notes', sa.Text(), nullable=True),
        sa.Column('po_reference', sa.String(length=50), nullable=True),
        sa.Column('project_reference', sa.String(length=100), nullable=True),
        sa.Column('work_order_reference', sa.String(length=100), nullable=True),
        sa.Column('received_by_id', sa.Integer(), nullable=True),
        sa.Column('inspected_by_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], name='fk_material_instances_material_id'),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], name='fk_material_instances_po_id'),
        sa.ForeignKeyConstraint(['po_line_item_id'], ['po_line_items.id'], name='fk_material_instances_po_line_id'),
        sa.ForeignKeyConstraint(['grn_line_item_id'], ['grn_line_items.id'], name='fk_material_instances_grn_line_id'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], name='fk_material_instances_supplier_id'),
        sa.ForeignKeyConstraint(['received_by_id'], ['users.id'], name='fk_material_instances_received_by'),
        sa.ForeignKeyConstraint(['inspected_by_id'], ['users.id'], name='fk_material_instances_inspected_by'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_material_instances_id', 'material_instances', ['id'])
    op.create_index('ix_material_instances_item_number', 'material_instances', ['item_number'], unique=True)
    op.create_index('ix_material_instances_lot_number', 'material_instances', ['lot_number'])
    op.create_index('ix_material_instances_serial_number', 'material_instances', ['serial_number'])
    op.create_index('ix_material_instances_heat_number', 'material_instances', ['heat_number'])
    op.create_index('ix_material_instances_lifecycle_status', 'material_instances', ['lifecycle_status'])
    
    # Create material_allocations table
    op.create_table('material_allocations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('material_instance_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('bom_id', sa.Integer(), nullable=True),
        sa.Column('work_order_reference', sa.String(length=100), nullable=True),
        sa.Column('allocation_number', sa.String(length=50), nullable=False),
        sa.Column('quantity_allocated', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('quantity_issued', sa.Numeric(precision=14, scale=4), nullable=False, server_default='0'),
        sa.Column('quantity_returned', sa.Numeric(precision=14, scale=4), nullable=False, server_default='0'),
        sa.Column('unit_of_measure', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_fulfilled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('allocation_date', sa.Date(), nullable=False),
        sa.Column('required_date', sa.Date(), nullable=True),
        sa.Column('issued_date', sa.Date(), nullable=True),
        sa.Column('allocated_by_id', sa.Integer(), nullable=False),
        sa.Column('issued_by_id', sa.Integer(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['material_instance_id'], ['material_instances.id'], name='fk_material_allocations_instance_id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='fk_material_allocations_project_id'),
        sa.ForeignKeyConstraint(['bom_id'], ['bill_of_materials.id'], name='fk_material_allocations_bom_id'),
        sa.ForeignKeyConstraint(['allocated_by_id'], ['users.id'], name='fk_material_allocations_allocated_by'),
        sa.ForeignKeyConstraint(['issued_by_id'], ['users.id'], name='fk_material_allocations_issued_by'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_material_allocations_id', 'material_allocations', ['id'])
    op.create_index('ix_material_allocations_allocation_number', 'material_allocations', ['allocation_number'], unique=True)
    
    # Create material_status_history table
    op.create_table('material_status_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('material_instance_id', sa.Integer(), nullable=False),
        sa.Column('from_status', lifecycle_status_enum, nullable=True),
        sa.Column('to_status', lifecycle_status_enum, nullable=False),
        sa.Column('changed_by_id', sa.Integer(), nullable=False),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('reference_number', sa.String(length=100), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['material_instance_id'], ['material_instances.id'], name='fk_material_status_history_instance_id'),
        sa.ForeignKeyConstraint(['changed_by_id'], ['users.id'], name='fk_material_status_history_changed_by'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_material_status_history_id', 'material_status_history', ['id'])
    
    # Create bom_source_tracking table
    op.create_table('bom_source_tracking',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bom_id', sa.Integer(), nullable=False),
        sa.Column('bom_item_id', sa.Integer(), nullable=False),
        sa.Column('purchase_order_id', sa.Integer(), nullable=True),
        sa.Column('po_line_item_id', sa.Integer(), nullable=True),
        sa.Column('material_instance_id', sa.Integer(), nullable=True),
        sa.Column('quantity_required', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('quantity_allocated', sa.Numeric(precision=14, scale=4), nullable=False, server_default='0'),
        sa.Column('quantity_consumed', sa.Numeric(precision=14, scale=4), nullable=False, server_default='0'),
        sa.Column('unit_of_measure', sa.String(length=20), nullable=False),
        sa.Column('is_fulfilled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('required_date', sa.Date(), nullable=True),
        sa.Column('allocated_date', sa.Date(), nullable=True),
        sa.Column('consumed_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['bom_id'], ['bill_of_materials.id'], name='fk_bom_source_tracking_bom_id'),
        sa.ForeignKeyConstraint(['bom_item_id'], ['bom_items.id'], name='fk_bom_source_tracking_bom_item_id'),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], name='fk_bom_source_tracking_po_id'),
        sa.ForeignKeyConstraint(['po_line_item_id'], ['po_line_items.id'], name='fk_bom_source_tracking_po_line_id'),
        sa.ForeignKeyConstraint(['material_instance_id'], ['material_instances.id'], name='fk_bom_source_tracking_material_instance_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bom_source_tracking_id', 'bom_source_tracking', ['id'])


def downgrade() -> None:
    # Drop tables
    op.drop_index('ix_bom_source_tracking_id', table_name='bom_source_tracking')
    op.drop_table('bom_source_tracking')
    
    op.drop_index('ix_material_status_history_id', table_name='material_status_history')
    op.drop_table('material_status_history')
    
    op.drop_index('ix_material_allocations_allocation_number', table_name='material_allocations')
    op.drop_index('ix_material_allocations_id', table_name='material_allocations')
    op.drop_table('material_allocations')
    
    op.drop_index('ix_material_instances_lifecycle_status', table_name='material_instances')
    op.drop_index('ix_material_instances_heat_number', table_name='material_instances')
    op.drop_index('ix_material_instances_serial_number', table_name='material_instances')
    op.drop_index('ix_material_instances_lot_number', table_name='material_instances')
    op.drop_index('ix_material_instances_item_number', table_name='material_instances')
    op.drop_index('ix_material_instances_id', table_name='material_instances')
    op.drop_table('material_instances')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS materialcondition")
    op.execute("DROP TYPE IF EXISTS materiallifecyclestatus")
