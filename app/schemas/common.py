"""Common Pydantic schemas."""
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel

T = TypeVar("T")


class Message(BaseModel):
    """Generic message response."""
    message: str


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        from_attributes = True
