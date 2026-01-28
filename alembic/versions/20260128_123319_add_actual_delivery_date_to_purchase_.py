"""add_actual_delivery_date_to_purchase_orders

Revision ID: c8cd1ffc77af
Revises: c2d3e4f5a6b7
Create Date: 2026-01-28 12:33:19.140700

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8cd1ffc77af'
down_revision: Union[str, None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add actual_delivery_date column to purchase_orders table
    # Check if column already exists before adding (for safety)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('purchase_orders')]
    
    if 'actual_delivery_date' not in columns:
        op.add_column('purchase_orders',
            sa.Column('actual_delivery_date', sa.Date(), nullable=True)
        )


def downgrade() -> None:
    # Remove actual_delivery_date column from purchase_orders table
    op.drop_column('purchase_orders', 'actual_delivery_date')
