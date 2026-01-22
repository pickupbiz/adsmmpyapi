"""User model for authentication and authorization."""
import enum
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, Enum, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.inventory import InventoryTransaction
    from app.models.workflow import WorkflowApproval
    from app.models.audit import AuditLog


class UserRole(str, enum.Enum):
    """User role enumeration for aerospace materials management."""
    ADMIN = "admin"                          # Legacy admin role (maps to director)
    DIRECTOR = "director"                    # Full access, final approvals
    HEAD_OF_OPERATIONS = "head_of_operations"  # Operations oversight
    STORE = "store"                          # Inventory management
    PURCHASE = "purchase"                    # Procurement and orders
    QA = "qa"                                # Quality assurance
    ENGINEER = "engineer"                    # Technical specifications
    TECHNICIAN = "technician"                # Floor operations
    VIEWER = "viewer"                        # Read-only access


class Department(str, enum.Enum):
    """Department enumeration."""
    OPERATIONS = "OPERATIONS"
    PROCUREMENT = "PROCUREMENT"
    QUALITY_ASSURANCE = "QUALITY_ASSURANCE"
    ENGINEERING = "ENGINEERING"
    PRODUCTION = "PRODUCTION"
    STORES = "STORES"
    FINANCE = "FINANCE"
    ADMINISTRATION = "ADMINISTRATION"


class User(Base, TimestampMixin):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Personal information
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    employee_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Role and department
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.VIEWER,
        nullable=False
    )
    department: Mapped[Optional[Department]] = mapped_column(
        Enum(Department, values_callable=lambda x: [e.value for e in x]),
        nullable=True
    )
    designation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Reporting structure
    reports_to_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )
    
    # Approval limits
    approval_limit: Mapped[Optional[float]] = mapped_column(nullable=True)  # Max amount user can approve
    can_approve_workflows: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Signature for approvals
    signature_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Self-referential relationship for reporting structure
    reports_to = relationship("User", remote_side="User.id", backref="direct_reports")
    
    # Relationships
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="created_by_user", foreign_keys="Order.created_by")
    inventory_transactions: Mapped[List["InventoryTransaction"]] = relationship(
        "InventoryTransaction", 
        back_populates="performed_by_user"
    )
    workflow_approvals: Mapped[List["WorkflowApproval"]] = relationship(
        "WorkflowApproval",
        back_populates="approver",
        foreign_keys="WorkflowApproval.approver_id"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    def has_permission(self, required_roles: List[UserRole]) -> bool:
        """Check if user has one of the required roles."""
        if self.is_superuser:
            return True
        return self.role in required_roles
    
    def can_approve_amount(self, amount: float) -> bool:
        """Check if user can approve a specific amount."""
        if self.is_superuser:
            return True
        if not self.can_approve_workflows:
            return False
        if self.approval_limit is None:
            return True
        return amount <= self.approval_limit
