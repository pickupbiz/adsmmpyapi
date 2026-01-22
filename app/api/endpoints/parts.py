"""Part management endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.part import Part, PartMaterial, PartStatus, PartCriticality
from app.schemas.part import (
    PartCreate, PartUpdate, PartResponse,
    PartMaterialCreate, PartMaterialUpdate, PartMaterialResponse
)
from app.schemas.common import PaginatedResponse
from app.api.dependencies import (
    require_engineer,
    require_any_role,
    PaginationParams
)

router = APIRouter(prefix="/parts", tags=["Parts"])


@router.get("", response_model=PaginatedResponse[PartResponse])
def list_parts(
    pagination: PaginationParams = Depends(),
    status: Optional[PartStatus] = Query(None),
    criticality: Optional[PartCriticality] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """
    List all parts with optional filtering.
    """
    query = db.query(Part)
    
    if status:
        query = query.filter(Part.status == status)
    if criticality:
        query = query.filter(Part.criticality == criticality)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Part.name.ilike(search_term)) |
            (Part.part_number.ilike(search_term))
        )
    
    total = query.count()
    parts = query.offset(pagination.offset).limit(pagination.limit).all()
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return PaginatedResponse(
        items=parts,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages
    )


@router.get("/{part_id}", response_model=PartResponse)
def get_part(
    part_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get part by ID."""
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Part not found"
        )
    return part


@router.post("", response_model=PartResponse, status_code=status.HTTP_201_CREATED)
def create_part(
    part_in: PartCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Create a new part."""
    existing = db.query(Part).filter(Part.part_number == part_in.part_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Part number already exists"
        )
    
    part = Part(**part_in.model_dump())
    db.add(part)
    db.commit()
    db.refresh(part)
    return part


@router.put("/{part_id}", response_model=PartResponse)
def update_part(
    part_id: int,
    part_in: PartUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Update a part."""
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Part not found"
        )
    
    update_data = part_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(part, field, value)
    
    db.commit()
    db.refresh(part)
    return part


@router.delete("/{part_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_part(
    part_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Delete a part."""
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Part not found"
        )
    
    db.delete(part)
    db.commit()


# Part Materials endpoints
@router.get("/{part_id}/materials", response_model=list[PartMaterialResponse])
def list_part_materials(
    part_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """List all materials for a part."""
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Part not found"
        )
    return part.part_materials


@router.post("/{part_id}/materials", response_model=PartMaterialResponse, status_code=status.HTTP_201_CREATED)
def add_part_material(
    part_id: int,
    material_in: PartMaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Add a material to a part."""
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Part not found"
        )
    
    part_material = PartMaterial(
        part_id=part_id,
        **material_in.model_dump(exclude={"part_id"})
    )
    db.add(part_material)
    db.commit()
    db.refresh(part_material)
    return part_material


@router.delete("/{part_id}/materials/{material_link_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_part_material(
    part_id: int,
    material_link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Remove a material from a part."""
    link = db.query(PartMaterial).filter(
        PartMaterial.id == material_link_id,
        PartMaterial.part_id == part_id
    ).first()
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Part material link not found"
        )
    
    db.delete(link)
    db.commit()
