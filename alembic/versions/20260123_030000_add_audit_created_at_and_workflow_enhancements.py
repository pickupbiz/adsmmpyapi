"""Add audit created_at and workflow enhancements.

Revision ID: 0a6b7c8d9e0f
Revises: 9f5g6h7i8j9k
Create Date: 2026-01-23 03:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '0a6b7c8d9e0f'
down_revision = '9f5g6h7i8j9k'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add created_at to audit_logs if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='audit_logs' AND column_name='created_at'
            ) THEN
                ALTER TABLE audit_logs ADD COLUMN created_at TIMESTAMP DEFAULT NOW() NOT NULL;
            END IF;
        END $$;
    """)
    
    # Add rejection_reason to purchase_orders if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='purchase_orders' AND column_name='rejection_reason'
            ) THEN
                ALTER TABLE purchase_orders ADD COLUMN rejection_reason TEXT;
            END IF;
        END $$;
    """)
    
    # Add can_approve_workflows to users if it doesn't exist (already should exist)
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='users' AND column_name='can_approve_workflows'
            ) THEN
                ALTER TABLE users ADD COLUMN can_approve_workflows BOOLEAN DEFAULT TRUE NOT NULL;
            END IF;
        END $$;
    """)
    
    # Create index on audit_logs for faster audit trail queries
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE indexname = 'ix_audit_logs_entity_type_entity_id'
            ) THEN
                CREATE INDEX ix_audit_logs_entity_type_entity_id ON audit_logs(entity_type, entity_id);
            END IF;
        END $$;
    """)
    
    # Create index on workflow_instances for faster lookups by reference
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE indexname = 'ix_workflow_instances_reference'
            ) THEN
                CREATE INDEX ix_workflow_instances_reference ON workflow_instances(reference_type, reference_id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS ix_workflow_instances_reference;")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_entity_type_entity_id;")
    
    # Note: We don't drop the columns as they may have data
