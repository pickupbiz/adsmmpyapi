"""Certification models for aerospace compliance."""
import enum
from datetime import date
from typing import Optional
from sqlalchemy import String, Text, Enum, ForeignKey, Boolean, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin


class CertificationType(str, enum.Enum):
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


class CertificationStatus(str, enum.Enum):
    """Certification status enumeration."""
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING = "pending"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


class Certification(Base, TimestampMixin):
    """Certification model for tracking industry certifications."""
    
    __tablename__ = "certifications"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    certification_type: Mapped[CertificationType] = mapped_column(
        Enum(CertificationType),
        nullable=False
    )
    status: Mapped[CertificationStatus] = mapped_column(
        Enum(CertificationStatus),
        default=CertificationStatus.ACTIVE,
        nullable=False
    )
    
    # Issuing authority
    issuing_authority: Mapped[str] = mapped_column(String(200), nullable=False)
    certificate_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Dates
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiration_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_audit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    next_audit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Details
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    material_certifications = relationship("MaterialCertification", back_populates="certification")
    
    @property
    def is_expired(self) -> bool:
        """Check if certification is expired."""
        if self.expiration_date:
            return date.today() > self.expiration_date
        return False
    
    def __repr__(self) -> str:
        return f"<Certification(id={self.id}, code='{self.code}', type='{self.certification_type}')>"


class MaterialCertification(Base, TimestampMixin):
    """Association table linking materials to their certifications."""
    
    __tablename__ = "material_certifications"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), nullable=False)
    certification_id: Mapped[int] = mapped_column(ForeignKey("certifications.id"), nullable=False)
    
    # Status
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Verification details
    verified_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    verified_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    verification_document: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    material = relationship("Material", back_populates="certifications")
    certification = relationship("Certification", back_populates="material_certifications")
    
    def __repr__(self) -> str:
        return f"<MaterialCertification(material_id={self.material_id}, cert_id={self.certification_id})>"
