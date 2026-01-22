"""Order Pydantic schemas."""
from datetime import datetime, date
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class OrderStatus(str, Enum):
    """Order status enumeration."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ORDERED = "ordered"
    SHIPPED = "shipped"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class OrderPriority(str, Enum):
    """Order priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    AOG = "aog"


# Order Item Schemas
class OrderItemBase(BaseModel):
    """Base order item schema."""
    material_id: int
    quantity_ordered: float = Field(..., gt=0)
    unit_of_measure: str = Field(..., max_length=20)
    unit_price: float = Field(..., ge=0)
    expected_delivery_date: Optional[date] = None
    specification_notes: Optional[str] = None
    notes: Optional[str] = None


class OrderItemCreate(OrderItemBase):
    """Schema for creating an order item."""
    pass


class OrderItemUpdate(BaseModel):
    """Schema for updating an order item."""
    material_id: Optional[int] = None
    quantity_ordered: Optional[float] = Field(None, gt=0)
    quantity_received: Optional[float] = Field(None, ge=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[float] = Field(None, ge=0)
    expected_delivery_date: Optional[date] = None
    specification_notes: Optional[str] = None
    notes: Optional[str] = None


class OrderItemResponse(OrderItemBase):
    """Schema for order item response."""
    id: int
    order_id: int
    quantity_received: float
    total_price: float
    is_fully_received: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Order Schemas
class OrderBase(BaseModel):
    """Base order schema."""
    supplier_id: int
    status: OrderStatus = OrderStatus.DRAFT
    priority: OrderPriority = OrderPriority.NORMAL
    order_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    shipping_method: Optional[str] = Field(None, max_length=100)
    purchase_order_number: Optional[str] = Field(None, max_length=100)
    work_order_reference: Optional[str] = Field(None, max_length=100)
    requires_certification: bool = True
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    """Schema for creating an order."""
    items: List[OrderItemCreate] = Field(default_factory=list)


class OrderUpdate(BaseModel):
    """Schema for updating an order."""
    supplier_id: Optional[int] = None
    status: Optional[OrderStatus] = None
    priority: Optional[OrderPriority] = None
    order_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    shipping_method: Optional[str] = Field(None, max_length=100)
    tracking_number: Optional[str] = Field(None, max_length=100)
    purchase_order_number: Optional[str] = Field(None, max_length=100)
    work_order_reference: Optional[str] = Field(None, max_length=100)
    tax: Optional[float] = Field(None, ge=0)
    shipping_cost: Optional[float] = Field(None, ge=0)
    requires_certification: Optional[bool] = None
    certification_received: Optional[bool] = None
    notes: Optional[str] = None


class OrderResponse(OrderBase):
    """Schema for order response."""
    id: int
    order_number: str
    created_by: int
    actual_delivery_date: Optional[date]
    subtotal: float
    tax: float
    shipping_cost: float
    total: float
    currency: str
    tracking_number: Optional[str]
    certification_received: bool
    items: List[OrderItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
