"""Fix barcodetype and barcodestatus enums to use lowercase values (match Python model)

The initial migration created these enums with uppercase. The SQLAlchemy model uses
values_callable with lowercase (.value). This migration renames enum values so INSERT/UPDATE work.

Revision ID: d9de2ffd88bg
Revises: c8cd1ffc77af
Create Date: 2026-01-29

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'd9de2ffd88bg'
down_revision: Union[str, None] = 'c8cd1ffc77af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # barcodetype: rename from uppercase to lowercase
    op.execute("ALTER TYPE barcodetype RENAME VALUE 'CODE128' TO 'code128'")
    op.execute("ALTER TYPE barcodetype RENAME VALUE 'CODE39' TO 'code39'")
    op.execute("ALTER TYPE barcodetype RENAME VALUE 'QR_CODE' TO 'qr_code'")
    op.execute("ALTER TYPE barcodetype RENAME VALUE 'DATA_MATRIX' TO 'data_matrix'")
    op.execute("ALTER TYPE barcodetype RENAME VALUE 'EAN13' TO 'ean13'")
    op.execute("ALTER TYPE barcodetype RENAME VALUE 'UPC' TO 'upc'")

    # barcodestatus: rename from uppercase to lowercase ('consumed' already added lowercase)
    op.execute("ALTER TYPE barcodestatus RENAME VALUE 'ACTIVE' TO 'active'")
    op.execute("ALTER TYPE barcodestatus RENAME VALUE 'INACTIVE' TO 'inactive'")
    op.execute("ALTER TYPE barcodestatus RENAME VALUE 'EXPIRED' TO 'expired'")
    op.execute("ALTER TYPE barcodestatus RENAME VALUE 'VOID' TO 'void'")


def downgrade() -> None:
    op.execute("ALTER TYPE barcodetype RENAME VALUE 'code128' TO 'CODE128'")
    op.execute("ALTER TYPE barcodetype RENAME VALUE 'code39' TO 'CODE39'")
    op.execute("ALTER TYPE barcodetype RENAME VALUE 'qr_code' TO 'QR_CODE'")
    op.execute("ALTER TYPE barcodetype RENAME VALUE 'data_matrix' TO 'DATA_MATRIX'")
    op.execute("ALTER TYPE barcodetype RENAME VALUE 'ean13' TO 'EAN13'")
    op.execute("ALTER TYPE barcodetype RENAME VALUE 'upc' TO 'UPC'")

    op.execute("ALTER TYPE barcodestatus RENAME VALUE 'active' TO 'ACTIVE'")
    op.execute("ALTER TYPE barcodestatus RENAME VALUE 'inactive' TO 'INACTIVE'")
    op.execute("ALTER TYPE barcodestatus RENAME VALUE 'expired' TO 'EXPIRED'")
    op.execute("ALTER TYPE barcodestatus RENAME VALUE 'void' TO 'VOID'")
