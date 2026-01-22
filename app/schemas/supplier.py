"""Supplier Pydantic schemas."""
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class SupplierStatus(str, Enum):
    """Supplier status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_APPROVAL = "pending_approval"
    SUSPENDED = "suspended"
    BLACKLISTED = "blacklisted"


class SupplierTier(str, Enum):
    """Supplier tier enumeration."""
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"


# Supplier Schemas
class SupplierBase(BaseModel):
    """Base supplier schema."""
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    status: SupplierStatus = SupplierStatus.PENDING_APPROVAL
    tier: SupplierTier = SupplierTier.TIER_2
    
    # Contact
    contact_name: Optional[str] = Field(None, max_length=200)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    
    # Address
    address_line_1: Optional[str] = Field(None, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field("USA", max_length=100)
    
    # Certifications
    is_as9100_certified: bool = False
    is_nadcap_certified: bool = False
    is_itar_compliant: bool = False
    cage_code: Optional[str] = Field(None, max_length=20)
    
    # Ratings
    quality_rating: Optional[float] = Field(None, ge=0, le=5)
    delivery_rating: Optional[float] = Field(None, ge=0, le=5)
    
    notes: Optional[str] = None


class SupplierCreate(SupplierBase):
    """Schema for creating a supplier."""
    pass


class SupplierUpdate(BaseModel):
    """Schema for updating a supplier."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    status: Optional[SupplierStatus] = None
    tier: Optional[SupplierTier] = None
    contact_name: Optional[str] = Field(None, max_length=200)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    address_line_1: Optional[str] = Field(None, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    is_as9100_certified: Optional[bool] = None
    is_nadcap_certified: Optional[bool] = None
    is_itar_compliant: Optional[bool] = None
    cage_code: Optional[str] = Field(None, max_length=20)
    quality_rating: Optional[float] = Field(None, ge=0, le=5)
    delivery_rating: Optional[float] = Field(None, ge=0, le=5)
    notes: Optional[str] = None


class SupplierResponse(SupplierBase):
    """Schema for supplier response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Supplier Material Schemas
class SupplierMaterialBase(BaseModel):
    """Base supplier material schema."""
    supplier_id: int
    material_id: int
    supplier_part_number: Optional[str] = Field(None, max_length=100)
    unit_price: Optional[float] = Field(None, ge=0)
    currency: str = Field("USD", max_length=3)
    minimum_order_quantity: Optional[float] = Field(None, ge=0)
    lead_time_days: Optional[int] = Field(None, ge=0)
    is_preferred: bool = False
    notes: Optional[str] = None


class SupplierMaterialCreate(SupplierMaterialBase):
    """Schema for creating a supplier material link."""
    pass


class SupplierMaterialUpdate(BaseModel):
    """Schema for updating a supplier material link."""
    supplier_part_number: Optional[str] = Field(None, max_length=100)
    unit_price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    minimum_order_quantity: Optional[float] = Field(None, ge=0)
    lead_time_days: Optional[int] = Field(None, ge=0)
    is_preferred: Optional[bool] = None
    notes: Optional[str] = None


class SupplierMaterialResponse(SupplierMaterialBase):
    """Schema for supplier material response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
