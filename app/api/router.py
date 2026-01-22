"""API router aggregating all endpoints."""
from fastapi import APIRouter
from app.api.endpoints import (
    auth,
    users,
    materials,
    parts,
    suppliers,
    inventory,
    certifications,
    orders,
    purchase_orders,
    material_instances
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(materials.router)
api_router.include_router(parts.router)
api_router.include_router(suppliers.router)
api_router.include_router(inventory.router)
api_router.include_router(certifications.router)
api_router.include_router(orders.router)
api_router.include_router(purchase_orders.router)
api_router.include_router(material_instances.router)
