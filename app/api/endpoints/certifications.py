"""Certification management endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.certification import Certification, MaterialCertification, CertificationType, CertificationStatus
from app.schemas.certification import (
    CertificationCreate, CertificationUpdate, CertificationResponse,
    MaterialCertificationCreate, MaterialCertificationUpdate, MaterialCertificationResponse
)
from app.schemas.common import PaginatedResponse
from app.api.dependencies import (
    require_engineer,
    require_any_role,
    PaginationParams
)

router = APIRouter(prefix="/certifications", tags=["Certifications"])


@router.get("", response_model=PaginatedResponse[CertificationResponse])
def list_certifications(
    pagination: PaginationParams = Depends(),
    certification_type: Optional[CertificationType] = Query(None),
    status: Optional[CertificationStatus] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """
    List all certifications with optional filtering.
    """
    query = db.query(Certification)
    
    if certification_type:
        query = query.filter(Certification.certification_type == certification_type)
    if status:
        query = query.filter(Certification.status == status)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Certification.name.ilike(search_term)) |
            (Certification.code.ilike(search_term))
        )
    
    total = query.count()
    certs = query.offset(pagination.offset).limit(pagination.limit).all()
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return PaginatedResponse(
        items=certs,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages
    )


@router.get("/{certification_id}", response_model=CertificationResponse)
def get_certification(
    certification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get certification by ID."""
    cert = db.query(Certification).filter(Certification.id == certification_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found"
        )
    return cert


@router.post("", response_model=CertificationResponse, status_code=status.HTTP_201_CREATED)
def create_certification(
    cert_in: CertificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Create a new certification."""
    existing = db.query(Certification).filter(Certification.code == cert_in.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certification code already exists"
        )
    
    cert = Certification(**cert_in.model_dump())
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return cert


@router.put("/{certification_id}", response_model=CertificationResponse)
def update_certification(
    certification_id: int,
    cert_in: CertificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Update a certification."""
    cert = db.query(Certification).filter(Certification.id == certification_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found"
        )
    
    update_data = cert_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cert, field, value)
    
    db.commit()
    db.refresh(cert)
    return cert


@router.delete("/{certification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_certification(
    certification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Delete a certification."""
    cert = db.query(Certification).filter(Certification.id == certification_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found"
        )
    
    db.delete(cert)
    db.commit()


# Material Certifications endpoints
@router.post("/materials", response_model=MaterialCertificationResponse, status_code=status.HTTP_201_CREATED)
def add_material_certification(
    link_in: MaterialCertificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Link a certification to a material."""
    link = MaterialCertification(**link_in.model_dump())
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.put("/materials/{link_id}", response_model=MaterialCertificationResponse)
def update_material_certification(
    link_id: int,
    link_in: MaterialCertificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Update a material certification link."""
    link = db.query(MaterialCertification).filter(MaterialCertification.id == link_id).first()
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material certification link not found"
        )
    
    update_data = link_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(link, field, value)
    
    db.commit()
    db.refresh(link)
    return link


@router.delete("/materials/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_material_certification(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Remove a certification from a material."""
    link = db.query(MaterialCertification).filter(MaterialCertification.id == link_id).first()
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material certification link not found"
        )
    
    db.delete(link)
    db.commit()
