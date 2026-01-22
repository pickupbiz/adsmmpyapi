"""Audit Pydantic schemas."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class AuditAction(str, Enum):
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


# Audit Log Schemas
class AuditLogBase(BaseModel):
    """Base audit log schema."""
    action: AuditAction
    entity_type: str = Field(..., max_length=100)
    entity_id: Optional[int] = None
    entity_reference: Optional[str] = Field(None, max_length=200)
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    changed_fields: Optional[List[str]] = None
    description: Optional[str] = None
    ip_address: Optional[str] = Field(None, max_length=50)
    user_agent: Optional[str] = Field(None, max_length=500)
    request_id: Optional[str] = Field(None, max_length=100)
    extra_data: Optional[Dict[str, Any]] = None


class AuditLogCreate(AuditLogBase):
    """Schema for creating an audit log."""
    user_id: Optional[int] = None
    user_email: Optional[str] = Field(None, max_length=255)
    user_role: Optional[str] = Field(None, max_length=50)


class AuditLogResponse(AuditLogBase):
    """Schema for audit log response."""
    id: int
    timestamp: datetime
    user_id: Optional[int]
    user_email: Optional[str]
    user_role: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


# Data Change Log Schemas
class DataChangeLogResponse(BaseModel):
    """Schema for data change log response."""
    id: int
    audit_log_id: int
    field_name: str
    field_type: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


# Login History Schemas
class LoginHistoryResponse(BaseModel):
    """Schema for login history response."""
    id: int
    user_id: int
    login_at: datetime
    logout_at: Optional[datetime]
    is_successful: bool
    failure_reason: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_info: Optional[str]
    location: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


# Audit Query Schemas
class AuditLogQuery(BaseModel):
    """Schema for querying audit logs."""
    user_id: Optional[int] = None
    action: Optional[AuditAction] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
