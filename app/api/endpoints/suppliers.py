"""Supplier management endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.supplier import Supplier, SupplierMaterial, SupplierStatus, SupplierTier
from app.schemas.supplier import (
    SupplierCreate, SupplierUpdate, SupplierResponse,
    SupplierMaterialCreate, SupplierMaterialUpdate, SupplierMaterialResponse
)
from app.schemas.common import PaginatedResponse
from app.api.dependencies import (
    require_manager,
    require_any_role,
    PaginationParams
)

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("", response_model=PaginatedResponse[SupplierResponse])
def list_suppliers(
    pagination: PaginationParams = Depends(),
    status: Optional[SupplierStatus] = Query(None),
    tier: Optional[SupplierTier] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """
    List all suppliers with optional filtering.
    """
    query = db.query(Supplier)
    
    if status:
        query = query.filter(Supplier.status == status)
    if tier:
        query = query.filter(Supplier.tier == tier)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Supplier.name.ilike(search_term)) |
            (Supplier.code.ilike(search_term))
        )
    
    total = query.count()
    suppliers = query.offset(pagination.offset).limit(pagination.limit).all()
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return PaginatedResponse(
        items=suppliers,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages
    )


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get supplier by ID."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    return supplier


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    supplier_in: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Create a new supplier."""
    existing = db.query(Supplier).filter(Supplier.code == supplier_in.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supplier code already exists"
        )
    
    supplier = Supplier(**supplier_in.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    supplier_in: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Update a supplier."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    update_data = supplier_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)
    
    db.commit()
    db.refresh(supplier)
    return supplier


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Delete a supplier."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    db.delete(supplier)
    db.commit()


# Supplier Materials endpoints
@router.get("/{supplier_id}/materials", response_model=list[SupplierMaterialResponse])
def list_supplier_materials(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """List all materials provided by a supplier."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    return supplier.supplier_materials


@router.post("/{supplier_id}/materials", response_model=SupplierMaterialResponse, status_code=status.HTTP_201_CREATED)
def add_supplier_material(
    supplier_id: int,
    material_in: SupplierMaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Add a material to a supplier's catalog."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    supplier_material = SupplierMaterial(
        supplier_id=supplier_id,
        **material_in.model_dump(exclude={"supplier_id"})
    )
    db.add(supplier_material)
    db.commit()
    db.refresh(supplier_material)
    return supplier_material


@router.delete("/{supplier_id}/materials/{material_link_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_supplier_material(
    supplier_id: int,
    material_link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Remove a material from a supplier's catalog."""
    link = db.query(SupplierMaterial).filter(
        SupplierMaterial.id == material_link_id,
        SupplierMaterial.supplier_id == supplier_id
    ).first()
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier material link not found"
        )
    
    db.delete(link)
    db.commit()
