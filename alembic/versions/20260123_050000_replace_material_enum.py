"""Replace materialtype enum with new values

This migration:
- Creates a new materialtype enum with lowercase values (raw, wip, finished)
- Migrates existing data from old enum values to new ones
- Replaces the old enum with the new one
- Does the same for materialstatus enum

Revision ID: b1c2d3e4f5a6
Revises: a0b1c2d3e4f5
Create Date: 2026-01-23 05:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a0b1c2d3e4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Step 1: Create new enum types with correct values
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE materialtype_new AS ENUM ('raw', 'wip', 'finished');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE materialstatus_new AS ENUM (
                'ordered', 'received', 'in_inspection', 'in_storage',
                'issued', 'in_production', 'completed', 'rejected'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Step 2: Add a temporary column with the new enum type
    op.add_column('materials', sa.Column('material_type_new', postgresql.ENUM('raw', 'wip', 'finished', name='materialtype_new', create_type=False), nullable=True))
    op.add_column('materials', sa.Column('status_new', postgresql.ENUM('ordered', 'received', 'in_inspection', 'in_storage', 'issued', 'in_production', 'completed', 'rejected', name='materialstatus_new', create_type=False), nullable=True))
    
    # Step 3: Migrate existing data
    # Map old material_type values to new ones
    # Default to 'raw' for any old values
    op.execute("""
        UPDATE materials 
        SET material_type_new = CASE
            WHEN material_type::text = 'METAL' THEN 'raw'::materialtype_new
            WHEN material_type::text = 'COMPOSITE' THEN 'raw'::materialtype_new
            WHEN material_type::text = 'POLYMER' THEN 'raw'::materialtype_new
            WHEN material_type::text = 'CERAMIC' THEN 'raw'::materialtype_new
            WHEN material_type::text = 'ALLOY' THEN 'raw'::materialtype_new
            WHEN material_type::text = 'COATING' THEN 'raw'::materialtype_new
            WHEN material_type::text = 'ADHESIVE' THEN 'raw'::materialtype_new
            WHEN material_type::text = 'OTHER' THEN 'raw'::materialtype_new
            WHEN material_type::text = 'RAW' THEN 'raw'::materialtype_new
            WHEN material_type::text = 'WIP' THEN 'wip'::materialtype_new
            WHEN material_type::text = 'FINISHED' THEN 'finished'::materialtype_new
            ELSE 'raw'::materialtype_new
        END
    """)
    
    # Map old status values to new ones
    op.execute("""
        UPDATE materials 
        SET status_new = CASE
            WHEN status::text = 'ACTIVE' THEN 'in_storage'::materialstatus_new
            WHEN status::text = 'DISCONTINUED' THEN 'rejected'::materialstatus_new
            WHEN status::text = 'PENDING_APPROVAL' THEN 'ordered'::materialstatus_new
            WHEN status::text = 'RESTRICTED' THEN 'in_inspection'::materialstatus_new
            WHEN status::text = 'ORDERED' THEN 'ordered'::materialstatus_new
            WHEN status::text = 'RECEIVED' THEN 'received'::materialstatus_new
            WHEN status::text = 'IN_INSPECTION' THEN 'in_inspection'::materialstatus_new
            WHEN status::text = 'IN_STORAGE' THEN 'in_storage'::materialstatus_new
            WHEN status::text = 'ISSUED' THEN 'issued'::materialstatus_new
            WHEN status::text = 'IN_PRODUCTION' THEN 'in_production'::materialstatus_new
            WHEN status::text = 'COMPLETED' THEN 'completed'::materialstatus_new
            WHEN status::text = 'REJECTED' THEN 'rejected'::materialstatus_new
            ELSE 'ordered'::materialstatus_new
        END
    """)
    
    # Step 4: Drop old columns
    op.drop_column('materials', 'material_type')
    op.drop_column('materials', 'status')
    
    # Step 5: Rename new columns to original names
    op.alter_column('materials', 'material_type_new', new_column_name='material_type')
    op.alter_column('materials', 'status_new', new_column_name='status')
    
    # Step 6: Make columns NOT NULL
    op.alter_column('materials', 'material_type', nullable=False)
    op.alter_column('materials', 'status', nullable=False)
    
    # Step 7: Drop old enum types
    op.execute("DROP TYPE IF EXISTS materialtype CASCADE")
    op.execute("DROP TYPE IF EXISTS materialstatus CASCADE")
    
    # Step 8: Rename new enum types to original names
    op.execute("ALTER TYPE materialtype_new RENAME TO materialtype")
    op.execute("ALTER TYPE materialstatus_new RENAME TO materialstatus")


def downgrade() -> None:
    conn = op.get_bind()
    
    # Reverse the process
    # Create old enum types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE materialtype_old AS ENUM ('METAL', 'COMPOSITE', 'POLYMER', 'CERAMIC', 'ALLOY', 'COATING', 'ADHESIVE', 'OTHER');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE materialstatus_old AS ENUM ('ACTIVE', 'DISCONTINUED', 'PENDING_APPROVAL', 'RESTRICTED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Add temporary columns
    op.add_column('materials', sa.Column('material_type_old', postgresql.ENUM('METAL', 'COMPOSITE', 'POLYMER', 'CERAMIC', 'ALLOY', 'COATING', 'ADHESIVE', 'OTHER', name='materialtype_old', create_type=False), nullable=True))
    op.add_column('materials', sa.Column('status_old', postgresql.ENUM('ACTIVE', 'DISCONTINUED', 'PENDING_APPROVAL', 'RESTRICTED', name='materialstatus_old', create_type=False), nullable=True))
    
    # Migrate data back
    op.execute("""
        UPDATE materials 
        SET material_type_old = CASE
            WHEN material_type::text = 'raw' THEN 'OTHER'::materialtype_old
            WHEN material_type::text = 'wip' THEN 'OTHER'::materialtype_old
            WHEN material_type::text = 'finished' THEN 'OTHER'::materialtype_old
            ELSE 'OTHER'::materialtype_old
        END
    """)
    
    op.execute("""
        UPDATE materials 
        SET status_old = CASE
            WHEN status::text = 'ordered' THEN 'PENDING_APPROVAL'::materialstatus_old
            WHEN status::text = 'received' THEN 'ACTIVE'::materialstatus_old
            WHEN status::text = 'in_inspection' THEN 'PENDING_APPROVAL'::materialstatus_old
            WHEN status::text = 'in_storage' THEN 'ACTIVE'::materialstatus_old
            WHEN status::text = 'issued' THEN 'ACTIVE'::materialstatus_old
            WHEN status::text = 'in_production' THEN 'ACTIVE'::materialstatus_old
            WHEN status::text = 'completed' THEN 'ACTIVE'::materialstatus_old
            WHEN status::text = 'rejected' THEN 'DISCONTINUED'::materialstatus_old
            ELSE 'ACTIVE'::materialstatus_old
        END
    """)
    
    # Drop new columns
    op.drop_column('materials', 'material_type')
    op.drop_column('materials', 'status')
    
    # Rename old columns
    op.alter_column('materials', 'material_type_old', new_column_name='material_type')
    op.alter_column('materials', 'status_old', new_column_name='status')
    
    # Make NOT NULL
    op.alter_column('materials', 'material_type', nullable=False)
    op.alter_column('materials', 'status', nullable=False)
    
    # Drop new enum types
    op.execute("DROP TYPE IF EXISTS materialtype CASCADE")
    op.execute("DROP TYPE IF EXISTS materialstatus CASCADE")
    
    # Rename old enum types
    op.execute("ALTER TYPE materialtype_old RENAME TO materialtype")
    op.execute("ALTER TYPE materialstatus_old RENAME TO materialstatus")
