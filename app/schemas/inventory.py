"""Inventory Pydantic schemas."""
from datetime import datetime, date
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class InventoryStatus(str, Enum):
    """Inventory status enumeration."""
    AVAILABLE = "available"
    RESERVED = "reserved"
    QUARANTINE = "quarantine"
    EXPIRED = "expired"
    CONSUMED = "consumed"


class TransactionType(str, Enum):
    """Transaction type enumeration."""
    RECEIPT = "receipt"
    ISSUE = "issue"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    SCRAP = "scrap"
    QUARANTINE = "quarantine"
    RELEASE = "release"


# Inventory Schemas
class InventoryBase(BaseModel):
    """Base inventory schema."""
    material_id: int
    lot_number: str = Field(..., min_length=1, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    quantity: float = Field(..., ge=0)
    reserved_quantity: float = Field(0, ge=0)
    unit_of_measure: str = Field(..., max_length=20)
    status: InventoryStatus = InventoryStatus.AVAILABLE
    location: str = Field(..., min_length=1, max_length=100)
    bin_number: Optional[str] = Field(None, max_length=50)
    received_date: date
    manufacture_date: Optional[date] = None
    expiration_date: Optional[date] = None
    certificate_of_conformance: Optional[str] = Field(None, max_length=255)
    heat_number: Optional[str] = Field(None, max_length=100)
    mill_test_report: Optional[str] = Field(None, max_length=255)
    unit_cost: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class InventoryCreate(InventoryBase):
    """Schema for creating inventory."""
    pass


class InventoryUpdate(BaseModel):
    """Schema for updating inventory."""
    lot_number: Optional[str] = Field(None, min_length=1, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    quantity: Optional[float] = Field(None, ge=0)
    reserved_quantity: Optional[float] = Field(None, ge=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    status: Optional[InventoryStatus] = None
    location: Optional[str] = Field(None, min_length=1, max_length=100)
    bin_number: Optional[str] = Field(None, max_length=50)
    manufacture_date: Optional[date] = None
    expiration_date: Optional[date] = None
    certificate_of_conformance: Optional[str] = Field(None, max_length=255)
    heat_number: Optional[str] = Field(None, max_length=100)
    mill_test_report: Optional[str] = Field(None, max_length=255)
    unit_cost: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class InventoryResponse(InventoryBase):
    """Schema for inventory response."""
    id: int
    available_quantity: float
    is_expired: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Inventory Transaction Schemas
class InventoryTransactionBase(BaseModel):
    """Base inventory transaction schema."""
    inventory_id: int
    transaction_type: TransactionType
    quantity: float = Field(..., gt=0)
    unit_of_measure: str = Field(..., max_length=20)
    reference_number: Optional[str] = Field(None, max_length=100)
    work_order: Optional[str] = Field(None, max_length=100)
    from_location: Optional[str] = Field(None, max_length=100)
    to_location: Optional[str] = Field(None, max_length=100)
    reason: Optional[str] = None
    notes: Optional[str] = None


class InventoryTransactionCreate(InventoryTransactionBase):
    """Schema for creating an inventory transaction."""
    pass


class InventoryTransactionResponse(InventoryTransactionBase):
    """Schema for inventory transaction response."""
    id: int
    performed_by: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
