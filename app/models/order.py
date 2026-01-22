"""Order models for material procurement."""
import enum
from datetime import date
from typing import Optional, List
from sqlalchemy import String, Text, Numeric, Enum, ForeignKey, Boolean, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin


class OrderStatus(str, enum.Enum):
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


class OrderPriority(str, enum.Enum):
    """Order priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    AOG = "aog"  # Aircraft on Ground - highest priority


class Order(Base, TimestampMixin):
    """Order model for material procurement."""
    
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Status and priority
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        default=OrderStatus.DRAFT,
        nullable=False
    )
    priority: Mapped[OrderPriority] = mapped_column(
        Enum(OrderPriority),
        default=OrderPriority.NORMAL,
        nullable=False
    )
    
    # Dates
    order_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Financial
    subtotal: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    tax: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    shipping_cost: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    total: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Shipping
    shipping_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Reference
    purchase_order_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    work_order_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Compliance
    requires_certification: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    certification_received: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="orders")
    created_by_user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def calculate_totals(self) -> None:
        """Calculate order totals from items."""
        self.subtotal = sum(item.total_price for item in self.items if item.total_price)
        self.total = float(self.subtotal) + float(self.tax) + float(self.shipping_cost)
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, order_number='{self.order_number}', status='{self.status}')>"


class OrderItem(Base, TimestampMixin):
    """Order line item model."""
    
    __tablename__ = "order_items"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), nullable=False)
    
    # Quantity
    quantity_ordered: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    quantity_received: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Pricing
    unit_price: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    
    # Delivery
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Specification
    specification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    material = relationship("Material", back_populates="order_items")
    
    @property
    def is_fully_received(self) -> bool:
        """Check if item is fully received."""
        return float(self.quantity_received) >= float(self.quantity_ordered)
    
    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, material_id={self.material_id})>"
