# Aerospace Parts Material Management API

A comprehensive FastAPI application for managing aerospace parts, materials, suppliers, inventory, certifications, and procurement orders with PostgreSQL database.

## Features

- **JWT Authentication** with role-based access control (RBAC)
- **Material Management** - Track materials with specifications, physical properties, and compliance info
- **Parts Management** - Manage aerospace parts with bill of materials and criticality levels
- **Supplier Management** - Maintain supplier info with aerospace certifications (AS9100, NADCAP, ITAR)
- **Inventory Tracking** - Full lot/batch traceability with transaction history
- **Certification Management** - Track industry certifications and material compliance
- **Order Management** - Procurement workflow with approval process

## User Roles

| Role       | Permissions                                           |
|------------|-------------------------------------------------------|
| Admin      | Full system access, user management                   |
| Manager    | Manage suppliers, orders, approve transactions        |
| Engineer   | Manage materials, parts, certifications               |
| Technician | Manage inventory, receive materials                   |
| Viewer     | Read-only access to all resources                     |

## Project Structure

```
app/
├── __init__.py
├── main.py                 # Application entry point
├── api/
│   ├── __init__.py
│   ├── dependencies.py     # API dependencies (auth, pagination)
│   ├── router.py           # API router aggregation
│   └── endpoints/          # API endpoint modules
│       ├── auth.py
│       ├── users.py
│       ├── materials.py
│       ├── parts.py
│       ├── suppliers.py
│       ├── inventory.py
│       ├── certifications.py
│       └── orders.py
├── core/
│   ├── __init__.py
│   ├── config.py           # Application settings
│   └── security.py         # JWT and password utilities
├── crud/
│   ├── __init__.py
│   ├── base.py             # Base CRUD operations
│   └── user.py             # User-specific CRUD
├── db/
│   ├── __init__.py
│   ├── base.py             # SQLAlchemy base class
│   └── session.py          # Database session management
├── models/                 # SQLAlchemy models
│   ├── __init__.py
│   ├── base.py
│   ├── user.py
│   ├── material.py
│   ├── part.py
│   ├── supplier.py
│   ├── inventory.py
│   ├── certification.py
│   └── order.py
└── schemas/                # Pydantic schemas
    ├── __init__.py
    ├── common.py
    ├── user.py
    ├── material.py
    ├── part.py
    ├── supplier.py
    ├── inventory.py
    ├── certification.py
    └── order.py
alembic/                    # Database migrations
├── env.py
├── script.py.mako
└── versions/
scripts/
└── create_superuser.py     # Utility to create admin user
```

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 13+

### Setup

1. **Clone the repository and install dependencies:**

```bash
cd adsmmpyapi
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

2. **Configure environment variables:**

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/aerospace_parts
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=True
```

3. **Create the PostgreSQL database:**

```sql
CREATE DATABASE aerospace_parts;
```

4. **Run database migrations:**

```bash
# Generate initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

5. **Create a superuser:**

```bash
python scripts/create_superuser.py admin@example.com your_password "Admin User"
```

6. **Run the application:**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 5055
```

## API Documentation

Once the application is running, access:

- **Swagger UI**: http://localhost:5055/api/v1/docs
- **ReDoc**: http://localhost:5055/api/v1/redoc
- **OpenAPI JSON**: http://localhost:5055/api/v1/openapi.json

## Authentication

### Login

```bash
curl -X POST "http://localhost:5055/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=your_password"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using the token

Include the access token in the Authorization header:

```bash
curl -X GET "http://localhost:5055/api/v1/materials" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/register` - Register new user (admin only)
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/change-password` - Change password

### Users
- `GET /api/v1/users` - List users (admin only)
- `GET /api/v1/users/{id}` - Get user by ID
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

### Materials
- `GET /api/v1/materials` - List materials (with filtering)
- `POST /api/v1/materials` - Create material
- `GET /api/v1/materials/{id}` - Get material
- `PUT /api/v1/materials/{id}` - Update material
- `DELETE /api/v1/materials/{id}` - Delete material
- `GET /api/v1/materials/categories` - List categories
- `POST /api/v1/materials/categories` - Create category

### Parts
- `GET /api/v1/parts` - List parts
- `POST /api/v1/parts` - Create part
- `GET /api/v1/parts/{id}` - Get part
- `PUT /api/v1/parts/{id}` - Update part
- `DELETE /api/v1/parts/{id}` - Delete part
- `GET /api/v1/parts/{id}/materials` - List part materials
- `POST /api/v1/parts/{id}/materials` - Add material to part

### Suppliers
- `GET /api/v1/suppliers` - List suppliers
- `POST /api/v1/suppliers` - Create supplier
- `GET /api/v1/suppliers/{id}` - Get supplier
- `PUT /api/v1/suppliers/{id}` - Update supplier
- `DELETE /api/v1/suppliers/{id}` - Delete supplier

### Inventory
- `GET /api/v1/inventory` - List inventory items
- `POST /api/v1/inventory` - Create inventory (receive material)
- `GET /api/v1/inventory/{id}` - Get inventory item
- `PUT /api/v1/inventory/{id}` - Update inventory
- `POST /api/v1/inventory/{id}/transactions` - Create transaction

### Certifications
- `GET /api/v1/certifications` - List certifications
- `POST /api/v1/certifications` - Create certification
- `GET /api/v1/certifications/{id}` - Get certification
- `PUT /api/v1/certifications/{id}` - Update certification
- `DELETE /api/v1/certifications/{id}` - Delete certification

### Orders
- `GET /api/v1/orders` - List orders
- `POST /api/v1/orders` - Create order
- `GET /api/v1/orders/{id}` - Get order
- `PUT /api/v1/orders/{id}` - Update order
- `DELETE /api/v1/orders/{id}` - Delete order (draft only)
- `POST /api/v1/orders/{id}/submit` - Submit for approval
- `POST /api/v1/orders/{id}/approve` - Approve order

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## License

MIT License
