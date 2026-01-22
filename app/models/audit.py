"""Audit trail models for tracking all changes."""
import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Enum, ForeignKey, DateTime, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class AuditAction(str, enum.Enum):
    """Type of audit action."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    EXPORT = "export"
    IMPORT = "import"
    LOGIN = "login"
    LOGOUT = "logout"
    APPROVE = "approve"
    REJECT = "reject"
    SUBMIT = "submit"
    CANCEL = "cancel"
    PRINT = "print"
    SCAN = "scan"


class AuditLog(Base):
    """Audit log for tracking all system changes and actions."""
    
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # User who performed the action
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Denormalized for history
    user_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)    # Denormalized for history
    
    # Action details
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), nullable=False, index=True)
    
    # Entity being acted upon
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # 'material', 'order', etc.
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    entity_reference: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # Human-readable reference
    
    # Change details
    old_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Previous state
    new_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # New state
    changed_fields: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of changed field names
    
    # Context
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # For request correlation
    
    # Additional data
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', entity='{self.entity_type}:{self.entity_id}')>"


class DataChangeLog(Base):
    """Detailed change log for specific field-level changes."""
    
    __tablename__ = "data_change_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    audit_log_id: Mapped[int] = mapped_column(ForeignKey("audit_logs.id"), nullable=False, index=True)
    
    # Field details
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    field_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Values (stored as strings for consistency)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    audit_log = relationship("AuditLog", backref="field_changes")
    
    def __repr__(self) -> str:
        return f"<DataChangeLog(id={self.id}, field='{self.field_name}')>"


class LoginHistory(Base):
    """Login history for security monitoring."""
    
    __tablename__ = "login_history"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    # Timestamp
    login_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    logout_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Status
    is_successful: Mapped[bool] = mapped_column(default=True, nullable=False)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Session info
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    token_jti: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # JWT ID
    
    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    device_info: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Relationships
    user = relationship("User", backref="login_history")
    
    def __repr__(self) -> str:
        return f"<LoginHistory(id={self.id}, user_id={self.user_id}, login_at='{self.login_at}')>"
