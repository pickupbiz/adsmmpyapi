"""Pydantic schemas for request/response validation."""
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserLogin,
    Token, TokenPayload, UserRole
)
from app.schemas.material import (
    MaterialCreate, MaterialUpdate, MaterialResponse,
    MaterialCategoryCreate, MaterialCategoryUpdate, MaterialCategoryResponse,
    MaterialType, MaterialStatus
)
from app.schemas.part import (
    PartCreate, PartUpdate, PartResponse,
    PartMaterialCreate, PartMaterialUpdate, PartMaterialResponse,
    PartStatus, PartCriticality
)
from app.schemas.supplier import (
    SupplierCreate, SupplierUpdate, SupplierResponse,
    SupplierMaterialCreate, SupplierMaterialUpdate, SupplierMaterialResponse,
    SupplierStatus, SupplierTier
)
from app.schemas.inventory import (
    InventoryCreate, InventoryUpdate, InventoryResponse,
    InventoryTransactionCreate, InventoryTransactionResponse,
    InventoryStatus, TransactionType
)
from app.schemas.certification import (
    CertificationCreate, CertificationUpdate, CertificationResponse,
    MaterialCertificationCreate, MaterialCertificationUpdate, MaterialCertificationResponse,
    CertificationType, CertificationStatus
)
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse,
    OrderItemCreate, OrderItemUpdate, OrderItemResponse,
    OrderStatus, OrderPriority
)
from app.schemas.common import PaginatedResponse, Message

__all__ = [
    # User
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin",
    "Token", "TokenPayload", "UserRole",
    # Material
    "MaterialCreate", "MaterialUpdate", "MaterialResponse",
    "MaterialCategoryCreate", "MaterialCategoryUpdate", "MaterialCategoryResponse",
    "MaterialType", "MaterialStatus",
    # Part
    "PartCreate", "PartUpdate", "PartResponse",
    "PartMaterialCreate", "PartMaterialUpdate", "PartMaterialResponse",
    "PartStatus", "PartCriticality",
    # Supplier
    "SupplierCreate", "SupplierUpdate", "SupplierResponse",
    "SupplierMaterialCreate", "SupplierMaterialUpdate", "SupplierMaterialResponse",
    "SupplierStatus", "SupplierTier",
    # Inventory
    "InventoryCreate", "InventoryUpdate", "InventoryResponse",
    "InventoryTransactionCreate", "InventoryTransactionResponse",
    "InventoryStatus", "TransactionType",
    # Certification
    "CertificationCreate", "CertificationUpdate", "CertificationResponse",
    "MaterialCertificationCreate", "MaterialCertificationUpdate", "MaterialCertificationResponse",
    "CertificationType", "CertificationStatus",
    # Order
    "OrderCreate", "OrderUpdate", "OrderResponse",
    "OrderItemCreate", "OrderItemUpdate", "OrderItemResponse",
    "OrderStatus", "OrderPriority",
    # Common
    "PaginatedResponse", "Message",
]
