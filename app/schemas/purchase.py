"""Simplified Purchase Order schemas for basic operations."""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.schemas.user import UserBase


class SimpleSupplierBase(BaseModel):
    """Simplified supplier base schema."""
    name: str
    code: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class SimpleSupplierCreate(SimpleSupplierBase):
    """Schema for creating a supplier."""
    pass


class SimpleSupplier(SimpleSupplierBase):
    """Schema for supplier response."""
    id: int
    rating: float
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class SimplePOLineItemBase(BaseModel):
    """Base schema for PO line item."""
    material_id: int
    quantity_ordered: float
    unit_price: float
    notes: Optional[str] = None


class SimplePOLineItemCreate(SimplePOLineItemBase):
    """Schema for creating a PO line item."""
    pass


class SimplePOLineItem(SimplePOLineItemBase):
    """Schema for PO line item response."""
    id: int
    purchase_order_id: int  # Fixed: matches model field name
    quantity_received: float
    total_price: float
    
    model_config = ConfigDict(from_attributes=True)


class SimplePurchaseOrderBase(BaseModel):
    """Base schema for purchase order."""
    supplier_id: int
    total_amount: float
    expected_delivery_date: Optional[datetime] = None
    notes: Optional[str] = None


class SimplePurchaseOrderCreate(SimplePurchaseOrderBase):
    """Schema for creating a purchase order."""
    line_items: List[SimplePOLineItemCreate]


class SimplePurchaseOrder(SimplePurchaseOrderBase):
    """Schema for purchase order response."""
    id: int
    po_number: str
    status: str
    created_by_id: int  # Fixed: matches model field name
    approved_by_id: Optional[int] = None  # Fixed: matches model field name
    ordered_date: Optional[datetime] = None  # Fixed: matches model field name (ordered_date not order_date)
    actual_delivery_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    supplier: Optional[SimpleSupplier] = None
    creator: Optional[UserBase] = None
    approver: Optional[UserBase] = None
    line_items: List[SimplePOLineItem] = []
    
    model_config = ConfigDict(from_attributes=True)
