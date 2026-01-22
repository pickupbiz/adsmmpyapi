"""Project and BOM Pydantic schemas."""
from datetime import datetime, date
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class ProjectStatus(str, Enum):
    """Project status enumeration."""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class ProjectPriority(str, Enum):
    """Project priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class BOMStatus(str, Enum):
    """BOM status enumeration."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    RELEASED = "released"
    OBSOLETE = "obsolete"


class BOMType(str, Enum):
    """BOM type enumeration."""
    ENGINEERING = "engineering"
    MANUFACTURING = "manufacturing"
    SERVICE = "service"
    SALES = "sales"


# Project Schemas
class ProjectBase(BaseModel):
    """Base project schema."""
    project_number: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=20)
    status: ProjectStatus = ProjectStatus.PLANNING
    priority: ProjectPriority = ProjectPriority.NORMAL
    description: Optional[str] = None
    customer_name: Optional[str] = Field(None, max_length=200)
    contract_number: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    budget: Optional[float] = Field(None, ge=0)
    currency: str = Field("USD", max_length=3)
    project_manager_id: Optional[int] = None
    parent_project_id: Optional[int] = None
    notes: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[ProjectStatus] = None
    priority: Optional[ProjectPriority] = None
    description: Optional[str] = None
    customer_name: Optional[str] = Field(None, max_length=200)
    contract_number: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    budget: Optional[float] = Field(None, ge=0)
    actual_cost: Optional[float] = Field(None, ge=0)
    project_manager_id: Optional[int] = None
    notes: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    id: int
    actual_end_date: Optional[date]
    actual_cost: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# BOM Schemas
class BOMBase(BaseModel):
    """Base BOM schema."""
    bom_number: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    revision: str = Field("A", max_length=10)
    bom_type: BOMType = BOMType.MANUFACTURING
    status: BOMStatus = BOMStatus.DRAFT
    project_id: Optional[int] = None
    part_id: Optional[int] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    base_quantity: float = Field(1, ge=0)
    unit_of_measure: str = Field("EA", max_length=20)
    description: Optional[str] = None
    notes: Optional[str] = None


class BOMCreate(BOMBase):
    """Schema for creating a BOM."""
    pass


class BOMUpdate(BaseModel):
    """Schema for updating a BOM."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    revision: Optional[str] = Field(None, max_length=10)
    bom_type: Optional[BOMType] = None
    status: Optional[BOMStatus] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    base_quantity: Optional[float] = Field(None, ge=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    notes: Optional[str] = None


class BOMResponse(BOMBase):
    """Schema for BOM response."""
    id: int
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    released_by: Optional[int]
    released_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# BOM Item Schemas
class BOMItemBase(BaseModel):
    """Base BOM item schema."""
    bom_id: int
    item_number: int
    material_id: Optional[int] = None
    part_id: Optional[int] = None
    child_bom_id: Optional[int] = None
    quantity: float = Field(..., gt=0)
    unit_of_measure: str = Field(..., max_length=20)
    scrap_factor: float = Field(1.0, ge=1.0)
    reference_designator: Optional[str] = Field(None, max_length=100)
    find_number: Optional[str] = Field(None, max_length=20)
    substitutes_allowed: bool = False
    operation_sequence: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


class BOMItemCreate(BOMItemBase):
    """Schema for creating a BOM item."""
    pass


class BOMItemUpdate(BaseModel):
    """Schema for updating a BOM item."""
    item_number: Optional[int] = None
    material_id: Optional[int] = None
    part_id: Optional[int] = None
    child_bom_id: Optional[int] = None
    quantity: Optional[float] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    scrap_factor: Optional[float] = Field(None, ge=1.0)
    reference_designator: Optional[str] = Field(None, max_length=100)
    find_number: Optional[str] = Field(None, max_length=20)
    substitutes_allowed: Optional[bool] = None
    operation_sequence: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


class BOMItemResponse(BOMItemBase):
    """Schema for BOM item response."""
    id: int
    extended_quantity: float
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Material Requisition Schemas
class MaterialRequisitionBase(BaseModel):
    """Base material requisition schema."""
    requisition_number: str = Field(..., min_length=1, max_length=50)
    project_id: Optional[int] = None
    bom_id: Optional[int] = None
    work_order: Optional[str] = Field(None, max_length=100)
    requested_date: date
    required_date: Optional[date] = None
    status: str = Field("draft", max_length=50)
    priority: str = Field("normal", max_length=20)
    notes: Optional[str] = None


class MaterialRequisitionCreate(MaterialRequisitionBase):
    """Schema for creating a material requisition."""
    pass


class MaterialRequisitionUpdate(BaseModel):
    """Schema for updating a material requisition."""
    work_order: Optional[str] = Field(None, max_length=100)
    required_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=50)
    priority: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class MaterialRequisitionResponse(MaterialRequisitionBase):
    """Schema for material requisition response."""
    id: int
    requested_by: int
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    issued_by: Optional[int]
    issued_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Material Requisition Item Schemas
class MaterialRequisitionItemBase(BaseModel):
    """Base material requisition item schema."""
    requisition_id: int
    material_id: int
    quantity_requested: float = Field(..., gt=0)
    unit_of_measure: str = Field(..., max_length=20)
    notes: Optional[str] = None


class MaterialRequisitionItemCreate(MaterialRequisitionItemBase):
    """Schema for creating a material requisition item."""
    pass


class MaterialRequisitionItemUpdate(BaseModel):
    """Schema for updating a material requisition item."""
    quantity_approved: Optional[float] = Field(None, ge=0)
    quantity_issued: Optional[float] = Field(None, ge=0)
    inventory_id: Optional[int] = None
    lot_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class MaterialRequisitionItemResponse(MaterialRequisitionItemBase):
    """Schema for material requisition item response."""
    id: int
    quantity_approved: Optional[float]
    quantity_issued: float
    inventory_id: Optional[int]
    lot_number: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
