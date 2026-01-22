"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.router import api_router
from app.db.session import engine
from app.db.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Create tables if they don't exist (for development)
    # In production, use Alembic migrations instead
    # Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    pass


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
## Aerospace Parts Material Management API

A comprehensive API for managing aerospace parts, materials, suppliers, 
inventory, certifications, and procurement orders.

### Features

- **Authentication**: JWT-based authentication with role-based access control
- **Materials Management**: Track materials with specifications, certifications, and compliance
- **Parts Management**: Manage aerospace parts with bill of materials
- **Supplier Management**: Maintain supplier information with certifications (AS9100, NADCAP)
- **Inventory Tracking**: Full lot/batch traceability with transaction history
- **Certification Management**: Track industry certifications and compliance
- **Order Management**: Procurement workflow with approval process

### User Roles

| Role | Description |
|------|-------------|
| Admin | Full system access |
| Manager | Manage suppliers, orders, approve transactions |
| Engineer | Manage materials, parts, certifications |
| Technician | Manage inventory, receive materials |
| Viewer | Read-only access |
        """,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    def health_check():
        """Check if the API is running."""
        return {"status": "healthy", "version": settings.APP_VERSION}
    
    return app


# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
