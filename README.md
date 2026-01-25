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
- **Purchase Order Management** - Complete PO lifecycle with approval workflows
- **Barcode & QR Code** - Generate and scan barcodes for material tracking
- **Workflow Management** - Configurable approval workflows for PO and material movements
- **Dashboard & Analytics** - Real-time dashboards with PO insights and supplier performance
- **Reporting** - PDF, Excel, and CSV export capabilities
- **WebSocket** - Real-time updates for PO status, materials, and alerts

> **⚠️ IMPORTANT:** If you're setting up this project for the first time or updating from an older version, please read the [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for database schema changes and migration instructions.

## User Roles

| Role              | Permissions                                                    |
|-------------------|----------------------------------------------------------------|
| Director          | Full system access, high-value approvals, user management      |
| Head of Operations| Operations approvals, workflow management                       |
| Purchase          | PO creation, supplier management, procurement                   |
| Store             | Material receipt, inventory management, GRN processing          |
| QA                | Quality inspections, material certifications                    |
| Engineer          | Material/parts management, BOM creation, technical specs        |
| Technician        | Inventory operations, material handling                         |
| Viewer            | Read-only access to all resources                              |

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

1. **Clone the repository and set up virtual environment:**

**Windows (PowerShell) - Recommended:**
```powershell
cd d:\source\Python\FastAPI\adsmmpyapi

# Run setup script (creates venv and installs dependencies)
powershell scripts/setup_venv.ps1
```

**Windows (Manual):**
```powershell
cd d:\source\Python\FastAPI\adsmmpyapi
python -m venv venv
.\venv\Scripts\activate.ps1
pip install -r requirements.txt
```

**Linux/Mac:**
```bash
cd /path/to/adsmmpyapi
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> **⚠️ Important:** Always activate the virtual environment before running the application!

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
# Apply all migrations (including latest schema updates)
alembic upgrade head
```

> **📋 Important:** If you're updating from an older version, see [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for breaking changes and migration steps.

5. **Create a superuser:**

```bash
python scripts/create_superuser.py admin@example.com your_password "Admin User"
```

6. **Run the application:**

**Windows (PowerShell) - Recommended:**
```powershell
# Use the run script (automatically activates venv)
powershell scripts/run_app.ps1
```

**Windows (Manual):**
```powershell
# Activate virtual environment first!
.\venv\Scripts\activate.ps1

# Then run the application
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 5055
```

**Linux/Mac:**
```bash
# Activate virtual environment first!
source venv/bin/activate

# Then run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 5055
```

> **⚠️ Common Error:** If you see `ModuleNotFoundError: No module named 'sqlalchemy'`, it means the virtual environment is not activated. Always activate the venv before running!

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

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_purchase_order_workflow.py

# Run specific test
pytest tests/test_purchase_order_workflow.py::TestPOCreation::test_create_po_as_purchase_user
```

### Test Coverage

```bash
# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run tests with coverage (terminal output)
pytest --cov=app --cov-report=term-missing

# Run tests with coverage (HTML report)
pytest --cov=app --cov-report=html

# Run tests with coverage (all reports)
pytest --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml --cov-branch

# View HTML report
# Open htmlcov/index.html in your browser
```

**Using Helper Scripts:**
- **Linux/Mac:** `bash scripts/run_tests_with_coverage.sh`
- **Windows:** `powershell scripts/run_tests_with_coverage.ps1`

**Coverage Configuration:**
- Coverage settings: `.coveragerc`
- HTML reports: `htmlcov/` directory
- XML reports: `coverage.xml`
- Includes branch coverage analysis

For more details, see [tests/README.md](./tests/README.md).
- `POST /api/v1/orders/{id}/submit` - Submit for approval
- `POST /api/v1/orders/{id}/approve` - Approve order

### Purchase Orders (Enhanced)
- `GET /api/v1/purchase-orders` - List POs with filtering
- `POST /api/v1/purchase-orders` - Create PO
- `GET /api/v1/purchase-orders/{id}` - Get PO details
- `PUT /api/v1/purchase-orders/{id}` - Update PO
- `POST /api/v1/purchase-orders/{id}/submit` - Submit for approval
- `POST /api/v1/purchase-orders/{id}/approve` - Approve PO
- `POST /api/v1/purchase-orders/{id}/reject` - Reject PO
- `POST /api/v1/purchase-orders/{id}/grn` - Create Goods Receipt Note

### Dashboard & Analytics
- `GET /api/v1/dashboard/overview` - Complete dashboard overview
- `GET /api/v1/dashboard/po-summary` - PO status summary
- `GET /api/v1/dashboard/material-summary` - Material status summary
- `GET /api/v1/dashboard/inventory-summary` - Inventory status
- `GET /api/v1/dashboard/po-vs-received` - PO vs received comparison
- `GET /api/v1/dashboard/delivery-analytics` - Delivery performance
- `GET /api/v1/dashboard/lead-time` - PO-to-production lead time
- `GET /api/v1/dashboard/supplier-performance` - Supplier analytics
- `GET /api/v1/dashboard/project-consumption` - Project-wise consumption
- `GET /api/v1/dashboard/material-movement` - Material movement history
- `GET /api/v1/dashboard/stock-analysis` - Fast-moving & low stock analysis
- `GET /api/v1/dashboard/alerts` - Active alerts

### Reports (PDF, Excel, CSV)
- `POST /api/v1/reports/po` - Generate PO report
- `POST /api/v1/reports/materials` - Generate material report
- `POST /api/v1/reports/inventory` - Generate inventory report
- `POST /api/v1/reports/suppliers` - Generate supplier performance report
- `POST /api/v1/reports/project-consumption` - Generate project consumption report
- `GET /api/v1/reports/download/{filename}` - Download generated report
- `GET /api/v1/reports/export/po-csv` - Quick PO CSV export
- `GET /api/v1/reports/export/inventory-csv` - Quick inventory CSV export
- `GET /api/v1/reports/export/materials-csv` - Quick materials CSV export

### WebSocket (Real-time Updates)
- `WS /api/v1/ws?token=<jwt>` - WebSocket connection for real-time updates

### Barcodes
- `POST /api/v1/barcodes/generate` - Generate barcode
- `POST /api/v1/barcodes/scan` - Process barcode scan
- `POST /api/v1/barcodes/scan-to-receive` - Scan to receive material
- `GET /api/v1/barcodes/{id}/traceability` - Get material traceability

### Workflows
- `GET /api/v1/workflows/templates` - List workflow templates
- `POST /api/v1/workflows/templates` - Create workflow template
- `GET /api/v1/workflows/pending` - Get pending approvals
- `POST /api/v1/workflows/instances/{id}/approve` - Approve workflow step
- `POST /api/v1/workflows/instances/{id}/reject` - Reject workflow

## WebSocket Real-time Updates

Connect to the WebSocket endpoint for real-time notifications:

```javascript
// Connect with authentication token
const ws = new WebSocket('ws://localhost:5055/api/v1/ws?token=YOUR_JWT_TOKEN');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message.type, message.data);
};

// Subscribe to specific entity updates
ws.send(JSON.stringify({
  type: 'subscribe',
  entity_type: 'purchase_order',
  entity_id: 123
}));

// Ping to keep connection alive
ws.send(JSON.stringify({ type: 'ping' }));
```

### Message Types Received:
- `po_status_change` - PO status updates
- `material_status_change` - Material lifecycle changes
- `new_alert` - New system alerts
- `inventory_update` - Stock level changes
- `approval_required` - New approval requests
- `grn_received` - Goods receipt notifications
- `inspection_complete` - Inspection results

## Report Generation

Generate reports in PDF, Excel, or CSV format:

```bash
# Generate PO Report (PDF)
curl -X POST "http://localhost:5055/api/v1/reports/po" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"date_range": "last_30_days", "format": "pdf"}'

# Generate Inventory Report (Excel)
curl -X POST "http://localhost:5055/api/v1/reports/inventory?format=excel" \
  -H "Authorization: Bearer $TOKEN"

# Quick CSV Export
curl -X GET "http://localhost:5055/api/v1/reports/export/inventory-csv" \
  -H "Authorization: Bearer $TOKEN" \
  -o inventory_export.csv
```

## Alert Types

The system generates the following alerts:
- **PO Pending Approval** - POs waiting for approval
- **Quantity Mismatch** - PO vs received quantity variance
- **Delayed Delivery** - Overdue POs
- **Fast-Moving Material** - Materials with low stock days
- **Low Stock** - Items below reorder level
- **Inspection Pending** - Materials awaiting QA inspection

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

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/aerospace_parts

# Security
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=True

# Email Notifications (optional)
EMAIL_ENABLED=False
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@aerospace-materials.com

# Workflow Thresholds (USD)
PO_AUTO_APPROVE_THRESHOLD=5000.0
PO_STANDARD_APPROVAL_THRESHOLD=25000.0
PO_HIGH_VALUE_THRESHOLD=100000.0
```

## License

MIT License
