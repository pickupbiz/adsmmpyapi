"""Part Pydantic schemas."""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class PartStatus(str, Enum):
    """Part status enumeration."""
    DESIGN = "design"
    PROTOTYPE = "prototype"
    PRODUCTION = "production"
    OBSOLETE = "obsolete"
    RESTRICTED = "restricted"


class PartCriticality(str, Enum):
    """Part criticality enumeration."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    STANDARD = "standard"


# Part Schemas
class PartBase(BaseModel):
    """Base part schema."""
    name: str = Field(..., min_length=1, max_length=200)
    part_number: str = Field(..., min_length=1, max_length=100)
    revision: str = Field("A", max_length=10)
    status: PartStatus = PartStatus.DESIGN
    criticality: PartCriticality = PartCriticality.STANDARD
    description: Optional[str] = None
    drawing_number: Optional[str] = Field(None, max_length=100)
    weight: Optional[float] = Field(None, ge=0)
    weight_unit: str = Field("kg", max_length=10)
    parent_part_id: Optional[int] = None
    is_serialized: bool = False
    requires_inspection: bool = True
    inspection_interval_hours: Optional[int] = Field(None, ge=0)
    unit_cost: Optional[float] = Field(None, ge=0)
    lead_time_days: Optional[int] = Field(None, ge=0)


class PartCreate(PartBase):
    """Schema for creating a part."""
    pass


class PartUpdate(BaseModel):
    """Schema for updating a part."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    part_number: Optional[str] = Field(None, min_length=1, max_length=100)
    revision: Optional[str] = Field(None, max_length=10)
    status: Optional[PartStatus] = None
    criticality: Optional[PartCriticality] = None
    description: Optional[str] = None
    drawing_number: Optional[str] = Field(None, max_length=100)
    weight: Optional[float] = Field(None, ge=0)
    weight_unit: Optional[str] = Field(None, max_length=10)
    parent_part_id: Optional[int] = None
    is_serialized: Optional[bool] = None
    requires_inspection: Optional[bool] = None
    inspection_interval_hours: Optional[int] = Field(None, ge=0)
    unit_cost: Optional[float] = Field(None, ge=0)
    lead_time_days: Optional[int] = Field(None, ge=0)


class PartResponse(PartBase):
    """Schema for part response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Part Material Schemas
class PartMaterialBase(BaseModel):
    """Base part material schema."""
    part_id: int
    material_id: int
    quantity_required: float = Field(..., gt=0)
    unit_of_measure: str = Field(..., max_length=20)
    is_primary: bool = False
    notes: Optional[str] = None


class PartMaterialCreate(PartMaterialBase):
    """Schema for creating a part material link."""
    pass


class PartMaterialUpdate(BaseModel):
    """Schema for updating a part material link."""
    quantity_required: Optional[float] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    is_primary: Optional[bool] = None
    notes: Optional[str] = None


class PartMaterialResponse(PartMaterialBase):
    """Schema for part material response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
