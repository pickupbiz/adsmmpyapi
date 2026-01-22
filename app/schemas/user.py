"""User Pydantic schemas."""
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRole(str, Enum):
    """User role enumeration."""
    DIRECTOR = "director"
    HEAD_OF_OPERATIONS = "head_of_operations"
    STORE = "store"
    PURCHASE = "purchase"
    QA = "qa"
    ENGINEER = "engineer"
    TECHNICIAN = "technician"
    VIEWER = "viewer"


class Department(str, Enum):
    """Department enumeration."""
    OPERATIONS = "operations"
    PROCUREMENT = "procurement"
    QUALITY_ASSURANCE = "quality_assurance"
    ENGINEERING = "engineering"
    PRODUCTION = "production"
    STORES = "stores"
    FINANCE = "finance"
    ADMINISTRATION = "administration"


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    employee_id: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=50)
    role: UserRole = UserRole.VIEWER
    department: Optional[Department] = None
    designation: Optional[str] = Field(None, max_length=100)
    reports_to_id: Optional[int] = None
    approval_limit: Optional[float] = Field(None, ge=0)
    can_approve_workflows: bool = False
    notes: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=8, max_length=100)
    is_active: bool = True
    is_superuser: bool = False


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    employee_id: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=50)
    role: Optional[UserRole] = None
    department: Optional[Department] = None
    designation: Optional[str] = Field(None, max_length=100)
    reports_to_id: Optional[int] = None
    approval_limit: Optional[float] = Field(None, ge=0)
    can_approve_workflows: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""
    sub: str
    role: str
    exp: datetime
    type: str
