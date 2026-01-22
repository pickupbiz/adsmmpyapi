"""Certification Pydantic schemas."""
from datetime import datetime, date
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class CertificationType(str, Enum):
    """Certification type enumeration."""
    AS9100 = "as9100"
    NADCAP = "nadcap"
    ISO9001 = "iso9001"
    MIL_SPEC = "mil_spec"
    AMS = "ams"
    ASTM = "astm"
    FAA = "faa"
    EASA = "easa"
    OTHER = "other"


class CertificationStatus(str, Enum):
    """Certification status enumeration."""
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING = "pending"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


# Certification Schemas
class CertificationBase(BaseModel):
    """Base certification schema."""
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    certification_type: CertificationType
    status: CertificationStatus = CertificationStatus.ACTIVE
    issuing_authority: str = Field(..., min_length=1, max_length=200)
    certificate_number: Optional[str] = Field(None, max_length=100)
    issue_date: date
    expiration_date: Optional[date] = None
    last_audit_date: Optional[date] = None
    next_audit_date: Optional[date] = None
    description: Optional[str] = None
    scope: Optional[str] = None
    document_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class CertificationCreate(CertificationBase):
    """Schema for creating a certification."""
    pass


class CertificationUpdate(BaseModel):
    """Schema for updating a certification."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    certification_type: Optional[CertificationType] = None
    status: Optional[CertificationStatus] = None
    issuing_authority: Optional[str] = Field(None, min_length=1, max_length=200)
    certificate_number: Optional[str] = Field(None, max_length=100)
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None
    last_audit_date: Optional[date] = None
    next_audit_date: Optional[date] = None
    description: Optional[str] = None
    scope: Optional[str] = None
    document_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class CertificationResponse(CertificationBase):
    """Schema for certification response."""
    id: int
    is_expired: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Material Certification Schemas
class MaterialCertificationBase(BaseModel):
    """Base material certification schema."""
    material_id: int
    certification_id: int
    is_mandatory: bool = True
    is_verified: bool = False
    verified_date: Optional[date] = None
    verified_by: Optional[str] = Field(None, max_length=200)
    verification_document: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class MaterialCertificationCreate(MaterialCertificationBase):
    """Schema for creating a material certification link."""
    pass


class MaterialCertificationUpdate(BaseModel):
    """Schema for updating a material certification link."""
    is_mandatory: Optional[bool] = None
    is_verified: Optional[bool] = None
    verified_date: Optional[date] = None
    verified_by: Optional[str] = Field(None, max_length=200)
    verification_document: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class MaterialCertificationResponse(MaterialCertificationBase):
    """Schema for material certification response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
