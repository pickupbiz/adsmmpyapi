"""Add Purchase Order models with approval workflow and material lifecycle

This migration adds:
- purchase_orders table (enhanced PO with approval workflow)
- po_line_items table (PO line items with material lifecycle tracking)
- po_approval_history table (audit trail for PO approvals)
- goods_receipt_notes table (GRN for material receiving)
- grn_line_items table (GRN line items with inspection tracking)
- New enums: postatus, popriority, approvalaction, materialstage, grnstatus

Revision ID: 7d3e4f5g6h7i
Revises: 6c2d3e4f5g6h
Create Date: 2026-01-22 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7d3e4f5g6h7i'
down_revision: Union[str, None] = '6c2d3e4f5g6h'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types (using DO block to handle IF NOT EXISTS in PostgreSQL)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE postatus AS ENUM ('draft', 'pending_approval', 'approved', 'rejected', 'ordered', 'partially_received', 'received', 'closed', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE popriority AS ENUM ('low', 'normal', 'high', 'critical', 'aog');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE approvalaction AS ENUM ('submitted', 'approved', 'rejected', 'returned', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE materialstage AS ENUM ('on_order', 'raw_material', 'in_inspection', 'wip', 'finished_goods', 'consumed', 'scrapped');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE grnstatus AS ENUM ('draft', 'pending_inspection', 'inspection_passed', 'inspection_failed', 'accepted', 'rejected', 'partial');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create purchase_orders table
    # Use postgresql.ENUM with create_type=False to avoid auto-creating
    postatus_enum = postgresql.ENUM('draft', 'pending_approval', 'approved', 'rejected', 'ordered', 'partially_received', 'received', 'closed', 'cancelled', name='postatus', create_type=False)
    popriority_enum = postgresql.ENUM('low', 'normal', 'high', 'critical', 'aog', name='popriority', create_type=False)
    
    op.create_table('purchase_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('po_number', sa.String(length=50), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('status', postatus_enum, nullable=False),
        sa.Column('priority', popriority_enum, nullable=False),
        sa.Column('po_date', sa.Date(), nullable=False),
        sa.Column('required_date', sa.Date(), nullable=True),
        sa.Column('expected_delivery_date', sa.Date(), nullable=True),
        sa.Column('approved_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ordered_date', sa.Date(), nullable=True),
        sa.Column('subtotal', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('shipping_cost', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('requires_approval', sa.Boolean(), nullable=False),
        sa.Column('approval_threshold', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('approval_notes', sa.Text(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('shipping_method', sa.String(length=100), nullable=True),
        sa.Column('shipping_address', sa.Text(), nullable=True),
        sa.Column('tracking_number', sa.String(length=100), nullable=True),
        sa.Column('requisition_number', sa.String(length=100), nullable=True),
        sa.Column('project_reference', sa.String(length=100), nullable=True),
        sa.Column('work_order_reference', sa.String(length=100), nullable=True),
        sa.Column('requires_certification', sa.Boolean(), nullable=False),
        sa.Column('requires_inspection', sa.Boolean(), nullable=False),
        sa.Column('payment_terms', sa.String(length=100), nullable=True),
        sa.Column('delivery_terms', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),
        sa.Column('revision_number', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], name='fk_purchase_orders_supplier_id'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], name='fk_purchase_orders_created_by_id'),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], name='fk_purchase_orders_approved_by_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_purchase_orders_id', 'purchase_orders', ['id'])
    op.create_index('ix_purchase_orders_po_number', 'purchase_orders', ['po_number'], unique=True)
    
    # Create po_line_items table
    materialstage_enum = postgresql.ENUM('on_order', 'raw_material', 'in_inspection', 'wip', 'finished_goods', 'consumed', 'scrapped', name='materialstage', create_type=False)
    
    op.create_table('po_line_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('purchase_order_id', sa.Integer(), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('quantity_ordered', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('quantity_received', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('quantity_accepted', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('quantity_rejected', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('unit_of_measure', sa.String(length=20), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('discount_percent', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('total_price', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('material_stage', materialstage_enum, nullable=False),
        sa.Column('required_date', sa.Date(), nullable=True),
        sa.Column('promised_date', sa.Date(), nullable=True),
        sa.Column('specification', sa.String(length=200), nullable=True),
        sa.Column('revision', sa.String(length=20), nullable=True),
        sa.Column('requires_certification', sa.Boolean(), nullable=False),
        sa.Column('certification_received', sa.Boolean(), nullable=False),
        sa.Column('requires_inspection', sa.Boolean(), nullable=False),
        sa.Column('inspection_completed', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], name='fk_po_line_items_purchase_order_id'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], name='fk_po_line_items_material_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_po_line_items_id', 'po_line_items', ['id'])
    
    # Create po_approval_history table
    approvalaction_enum = postgresql.ENUM('submitted', 'approved', 'rejected', 'returned', 'cancelled', name='approvalaction', create_type=False)
    
    op.create_table('po_approval_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('purchase_order_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', approvalaction_enum, nullable=False),
        sa.Column('from_status', postatus_enum, nullable=True),
        sa.Column('to_status', postatus_enum, nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('po_total_at_action', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('po_revision_at_action', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], name='fk_po_approval_history_purchase_order_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_po_approval_history_user_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_po_approval_history_id', 'po_approval_history', ['id'])
    
    # Create goods_receipt_notes table
    grnstatus_enum = postgresql.ENUM('draft', 'pending_inspection', 'inspection_passed', 'inspection_failed', 'accepted', 'rejected', 'partial', name='grnstatus', create_type=False)
    
    op.create_table('goods_receipt_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('grn_number', sa.String(length=50), nullable=False),
        sa.Column('purchase_order_id', sa.Integer(), nullable=False),
        sa.Column('received_by_id', sa.Integer(), nullable=False),
        sa.Column('inspected_by_id', sa.Integer(), nullable=True),
        sa.Column('status', grnstatus_enum, nullable=False),
        sa.Column('receipt_date', sa.Date(), nullable=False),
        sa.Column('inspection_date', sa.Date(), nullable=True),
        sa.Column('delivery_note_number', sa.String(length=100), nullable=True),
        sa.Column('invoice_number', sa.String(length=100), nullable=True),
        sa.Column('carrier', sa.String(length=100), nullable=True),
        sa.Column('tracking_number', sa.String(length=100), nullable=True),
        sa.Column('packing_slip_received', sa.Boolean(), nullable=False),
        sa.Column('coc_received', sa.Boolean(), nullable=False),
        sa.Column('mtr_received', sa.Boolean(), nullable=False),
        sa.Column('storage_location', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('inspection_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], name='fk_goods_receipt_notes_purchase_order_id'),
        sa.ForeignKeyConstraint(['received_by_id'], ['users.id'], name='fk_goods_receipt_notes_received_by_id'),
        sa.ForeignKeyConstraint(['inspected_by_id'], ['users.id'], name='fk_goods_receipt_notes_inspected_by_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_goods_receipt_notes_id', 'goods_receipt_notes', ['id'])
    op.create_index('ix_goods_receipt_notes_grn_number', 'goods_receipt_notes', ['grn_number'], unique=True)
    
    # Create grn_line_items table
    op.create_table('grn_line_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('goods_receipt_id', sa.Integer(), nullable=False),
        sa.Column('po_line_item_id', sa.Integer(), nullable=False),
        sa.Column('quantity_received', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('quantity_accepted', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('quantity_rejected', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('unit_of_measure', sa.String(length=20), nullable=False),
        sa.Column('lot_number', sa.String(length=100), nullable=True),
        sa.Column('batch_number', sa.String(length=100), nullable=True),
        sa.Column('serial_numbers', sa.Text(), nullable=True),
        sa.Column('heat_number', sa.String(length=100), nullable=True),
        sa.Column('manufacture_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('inspection_status', sa.String(length=50), nullable=True),
        sa.Column('inspection_notes', sa.Text(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('ncr_number', sa.String(length=50), nullable=True),
        sa.Column('storage_location', sa.String(length=100), nullable=True),
        sa.Column('bin_number', sa.String(length=50), nullable=True),
        sa.Column('inventory_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['goods_receipt_id'], ['goods_receipt_notes.id'], name='fk_grn_line_items_goods_receipt_id'),
        sa.ForeignKeyConstraint(['po_line_item_id'], ['po_line_items.id'], name='fk_grn_line_items_po_line_item_id'),
        sa.ForeignKeyConstraint(['inventory_id'], ['inventory.id'], name='fk_grn_line_items_inventory_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_grn_line_items_id', 'grn_line_items', ['id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_grn_line_items_id', table_name='grn_line_items')
    op.drop_table('grn_line_items')
    
    op.drop_index('ix_goods_receipt_notes_grn_number', table_name='goods_receipt_notes')
    op.drop_index('ix_goods_receipt_notes_id', table_name='goods_receipt_notes')
    op.drop_table('goods_receipt_notes')
    
    op.drop_index('ix_po_approval_history_id', table_name='po_approval_history')
    op.drop_table('po_approval_history')
    
    op.drop_index('ix_po_line_items_id', table_name='po_line_items')
    op.drop_table('po_line_items')
    
    op.drop_index('ix_purchase_orders_po_number', table_name='purchase_orders')
    op.drop_index('ix_purchase_orders_id', table_name='purchase_orders')
    op.drop_table('purchase_orders')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS grnstatus")
    op.execute("DROP TYPE IF EXISTS materialstage")
    op.execute("DROP TYPE IF EXISTS approvalaction")
    op.execute("DROP TYPE IF EXISTS popriority")
    op.execute("DROP TYPE IF EXISTS postatus")
