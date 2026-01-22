"""Material Pydantic schemas."""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class MaterialType(str, Enum):
    """Material type enumeration."""
    RAW = "raw"
    WIP = "wip"
    FINISHED = "finished"


class MaterialStatus(str, Enum):
    """Material status enumeration."""
    ORDERED = "ordered"
    RECEIVED = "received"
    IN_INSPECTION = "in_inspection"
    IN_STORAGE = "in_storage"
    ISSUED = "issued"
    IN_PRODUCTION = "in_production"
    COMPLETED = "completed"
    REJECTED = "rejected"


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
    item_number: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    specification: Optional[str] = Field(None, max_length=200)
    heat_number: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    quantity: float = Field(..., ge=0)
    unit_of_measure: str = Field("units", max_length=20)
    min_stock_level: float = Field(0, ge=0)
    max_stock_level: Optional[float] = Field(None, ge=0)
    material_type: MaterialType = MaterialType.RAW
    category_id: Optional[int] = None
    status: MaterialStatus = MaterialStatus.ORDERED
    
    # PO Reference
    po_id: Optional[int] = None
    po_line_item_id: Optional[int] = None
    
    # Supplier info
    supplier_id: Optional[int] = None
    supplier_batch_number: Optional[str] = Field(None, max_length=100)
    
    # Project reference
    project_id: Optional[int] = None
    
    # Location and storage
    location: Optional[str] = Field(None, max_length=200)
    storage_bin: Optional[str] = Field(None, max_length=100)
    
    # Dates
    received_date: Optional[datetime] = None
    inspection_date: Optional[datetime] = None
    issued_date: Optional[datetime] = None
    production_start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    
    # Quality
    qa_status: Optional[str] = Field(None, max_length=50)
    qa_inspected_by: Optional[int] = None
    certificate_number: Optional[str] = Field(None, max_length=100)
    
    # Barcode
    barcode_id: Optional[int] = None
    
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
    minimum_order_quantity: Optional[float] = Field(None, ge=0)


class MaterialCreate(MaterialBase):
    """Schema for creating a material."""
    pass


class MaterialUpdate(BaseModel):
    """Schema for updating a material."""
    item_number: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    specification: Optional[str] = Field(None, max_length=200)
    heat_number: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    quantity: Optional[float] = Field(None, ge=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    min_stock_level: Optional[float] = Field(None, ge=0)
    max_stock_level: Optional[float] = Field(None, ge=0)
    material_type: Optional[MaterialType] = None
    category_id: Optional[int] = None
    status: Optional[MaterialStatus] = None
    po_id: Optional[int] = None
    po_line_item_id: Optional[int] = None
    supplier_id: Optional[int] = None
    supplier_batch_number: Optional[str] = Field(None, max_length=100)
    project_id: Optional[int] = None
    location: Optional[str] = Field(None, max_length=200)
    storage_bin: Optional[str] = Field(None, max_length=100)
    received_date: Optional[datetime] = None
    inspection_date: Optional[datetime] = None
    issued_date: Optional[datetime] = None
    production_start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    qa_status: Optional[str] = Field(None, max_length=50)
    qa_inspected_by: Optional[int] = None
    certificate_number: Optional[str] = Field(None, max_length=100)
    barcode_id: Optional[int] = None
    # Physical properties (if still needed)
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
    minimum_order_quantity: Optional[float] = Field(None, ge=0)


class MaterialResponse(MaterialBase):
    """Schema for material response."""
    id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[MaterialCategoryResponse] = None
    
    model_config = ConfigDict(from_attributes=True)
