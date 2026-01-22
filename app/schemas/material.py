"""Material Pydantic schemas."""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class MaterialType(str, Enum):
    """Material type enumeration."""
    METAL = "metal"
    COMPOSITE = "composite"
    POLYMER = "polymer"
    CERAMIC = "ceramic"
    ALLOY = "alloy"
    COATING = "coating"
    ADHESIVE = "adhesive"
    OTHER = "other"


class MaterialStatus(str, Enum):
    """Material status enumeration."""
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    PENDING_APPROVAL = "pending_approval"
    RESTRICTED = "restricted"


# Material Category Schemas
class MaterialCategoryBase(BaseModel):
    """Base material category schema."""
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None
    parent_id: Optional[int] = None


class MaterialCategoryCreate(MaterialCategoryBase):
    """Schema for creating a material category."""
    pass


class MaterialCategoryUpdate(BaseModel):
    """Schema for updating a material category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = None
    parent_id: Optional[int] = None


class MaterialCategoryResponse(MaterialCategoryBase):
    """Schema for material category response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Material Schemas
class MaterialBase(BaseModel):
    """Base material schema."""
    name: str = Field(..., min_length=1, max_length=200)
    part_number: str = Field(..., min_length=1, max_length=100)
    specification: Optional[str] = Field(None, max_length=200)
    material_type: MaterialType = MaterialType.OTHER
    category_id: Optional[int] = None
    status: MaterialStatus = MaterialStatus.ACTIVE
    
    # Physical properties
    density: Optional[float] = Field(None, ge=0)
    tensile_strength: Optional[float] = Field(None, ge=0)
    yield_strength: Optional[float] = Field(None, ge=0)
    hardness: Optional[float] = Field(None, ge=0)
    melting_point: Optional[float] = None
    
    # Documentation
    description: Optional[str] = None
    mil_spec: Optional[str] = Field(None, max_length=100)
    ams_spec: Optional[str] = Field(None, max_length=100)
    is_hazardous: bool = False
    shelf_life_days: Optional[int] = Field(None, ge=0)
    storage_requirements: Optional[str] = None
    
    # Cost
    unit_cost: Optional[float] = Field(None, ge=0)
    unit_of_measure: str = Field("kg", max_length=20)
    minimum_order_quantity: Optional[float] = Field(None, ge=0)


class MaterialCreate(MaterialBase):
    """Schema for creating a material."""
    pass


class MaterialUpdate(BaseModel):
    """Schema for updating a material."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    part_number: Optional[str] = Field(None, min_length=1, max_length=100)
    specification: Optional[str] = Field(None, max_length=200)
    material_type: Optional[MaterialType] = None
    category_id: Optional[int] = None
    status: Optional[MaterialStatus] = None
    density: Optional[float] = Field(None, ge=0)
    tensile_strength: Optional[float] = Field(None, ge=0)
    yield_strength: Optional[float] = Field(None, ge=0)
    hardness: Optional[float] = Field(None, ge=0)
    melting_point: Optional[float] = None
    description: Optional[str] = None
    mil_spec: Optional[str] = Field(None, max_length=100)
    ams_spec: Optional[str] = Field(None, max_length=100)
    is_hazardous: Optional[bool] = None
    shelf_life_days: Optional[int] = Field(None, ge=0)
    storage_requirements: Optional[str] = None
    unit_cost: Optional[float] = Field(None, ge=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    minimum_order_quantity: Optional[float] = Field(None, ge=0)


class MaterialResponse(MaterialBase):
    """Schema for material response."""
    id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[MaterialCategoryResponse] = None
    
    model_config = ConfigDict(from_attributes=True)
