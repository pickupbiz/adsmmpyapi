"""Material management endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.material import Material, MaterialCategory, MaterialType, MaterialStatus
from app.schemas.material import (
    MaterialCreate, MaterialUpdate, MaterialResponse,
    MaterialCategoryCreate, MaterialCategoryUpdate, MaterialCategoryResponse
)
from app.schemas.common import PaginatedResponse
from app.api.dependencies import (
    get_current_user,
    require_engineer,
    require_any_role,
    PaginationParams
)

router = APIRouter(prefix="/materials", tags=["Materials"])


# Material Category endpoints
@router.get("/categories", response_model=PaginatedResponse[MaterialCategoryResponse])
def list_categories(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """List all material categories."""
    query = db.query(MaterialCategory)
    total = query.count()
    categories = query.offset(pagination.offset).limit(pagination.limit).all()
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return PaginatedResponse(
        items=categories,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages
    )


@router.post("/categories", response_model=MaterialCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: MaterialCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Create a new material category."""
    # Check for unique code
    existing = db.query(MaterialCategory).filter(
        MaterialCategory.code == category_in.code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category code already exists"
        )
    
    category = MaterialCategory(**category_in.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=MaterialCategoryResponse)
def update_category(
    category_id: int,
    category_in: MaterialCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Update a material category."""
    category = db.query(MaterialCategory).filter(MaterialCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    update_data = category_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    return category


# Material endpoints
@router.get("", response_model=PaginatedResponse[MaterialResponse])
def list_materials(
    pagination: PaginationParams = Depends(),
    material_type: Optional[MaterialType] = Query(None),
    status: Optional[MaterialStatus] = Query(None),
    category_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """
    List all materials with optional filtering.
    
    - **material_type**: Filter by material type
    - **status**: Filter by material status
    - **category_id**: Filter by category
    - **search**: Search in name or part number
    """
    query = db.query(Material)
    
    if material_type:
        query = query.filter(Material.material_type == material_type)
    if status:
        query = query.filter(Material.status == status)
    if category_id:
        query = query.filter(Material.category_id == category_id)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Material.name.ilike(search_term)) |
            (Material.part_number.ilike(search_term))
        )
    
    total = query.count()
    materials = query.offset(pagination.offset).limit(pagination.limit).all()
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return PaginatedResponse(
        items=materials,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages
    )


@router.get("/{material_id}", response_model=MaterialResponse)
def get_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get material by ID."""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    return material


@router.post("", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
def create_material(
    material_in: MaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Create a new material."""
    # Check for unique part number
    existing = db.query(Material).filter(
        Material.part_number == material_in.part_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Part number already exists"
        )
    
    # Convert category_id=0 to None (no category)
    material_data = material_in.model_dump()
    if material_data.get("category_id") == 0:
        material_data["category_id"] = None
    
    material = Material(**material_data)
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(
    material_id: int,
    material_in: MaterialUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Update a material."""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    update_data = material_in.model_dump(exclude_unset=True)
    # Convert category_id=0 to None (no category)
    if update_data.get("category_id") == 0:
        update_data["category_id"] = None
    
    for field, value in update_data.items():
        setattr(material, field, value)
    
    db.commit()
    db.refresh(material)
    return material


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Delete a material."""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    db.delete(material)
    db.commit()
