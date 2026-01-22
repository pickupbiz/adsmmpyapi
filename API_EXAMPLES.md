# Aerospace Parts Material Management API - Request Examples

Base URL: `http://localhost:5055/api/v1`

---

## Table of Contents
1. [Authentication](#authentication)
2. [Users](#users)
3. [Material Categories](#material-categories)
4. [Materials](#materials)
5. [Parts](#parts)
6. [Suppliers](#suppliers)
7. [Inventory](#inventory)
8. [Certifications](#certifications)
9. [Orders](#orders)

---

## Authentication

### Quick Reference - Auth Endpoints

| Action | Method | URL |
|--------|--------|-----|
| Login | `POST` | `/api/v1/auth/login` |
| Logout | `POST` | `/api/v1/auth/logout` |
| Refresh Token | `POST` | `/api/v1/auth/refresh` |
| Get Current User | `GET` | `/api/v1/auth/me` |
| Validate Token | `GET` | `/api/v1/auth/validate` |
| Get Permissions | `GET` | `/api/v1/auth/permissions` |
| Change Password | `POST` | `/api/v1/auth/change-password` |
| Login History | `GET` | `/api/v1/auth/login-history` |
| All Login History | `GET` | `/api/v1/auth/all-login-history` |
| Register User | `POST` | `/api/v1/auth/register` |

> ⚠️ **Note:** All auth endpoints are under `/api/v1/auth/` prefix. Don't forget the `/auth/` part!

---

### Login
Get JWT access and refresh tokens with role-based permissions.

```
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded
```

**Request Body (form-urlencoded):**
```
username=director@pickupbiz.com&password=12345
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**JWT Token Payload Contains:**
- `sub`: User ID
- `role`: User's role (director, head_of_operations, store, purchase, qa, engineer, technician, viewer)
- `exp`: Token expiration time
- `type`: "access" or "refresh"

---

### Refresh Token
Get new access token using refresh token.

```
POST /api/v1/auth/refresh?refresh_token=<your_refresh_token>
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### Get Current User
```
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "email": "director@pickupbiz.com",
  "full_name": "Admin User",
  "employee_id": null,
  "phone": null,
  "department": "ADMINISTRATION",
  "designation": null,
  "role": "director",
  "is_active": true,
  "is_superuser": true,
  "can_approve_workflows": true,
  "approval_limit": null,
  "last_login": "2026-01-22T10:30:00",
  "notes": null,
  "created_at": "2026-01-22T10:00:00",
  "updated_at": "2026-01-22T10:00:00"
}
```

---

### Validate Token
Check if the current JWT token is valid.

```
GET /api/v1/auth/validate
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "valid": true,
  "user_id": 1,
  "email": "director@pickupbiz.com",
  "role": "director",
  "is_superuser": true
}
```

---

### Get User Permissions
Get current user's role-based permissions.

```
GET /api/v1/auth/permissions
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "user_id": 1,
  "email": "director@pickupbiz.com",
  "role": "director",
  "role_description": "Full system access - can perform all operations",
  "is_superuser": true,
  "can_approve_workflows": true,
  "approval_limit": null,
  "permissions": ["ALL"]
}
```

**Permissions by Role:**

| Role | Permissions |
|------|-------------|
| **Director** | Full access: manage_users, manage_materials, manage_parts, manage_suppliers, manage_inventory, manage_orders, manage_certifications, approve_workflows, view_reports, manage_projects, manage_bom, manage_qa, view_audit_logs, system_settings |
| **Head of Operations** | view_materials, view_parts, view_suppliers, view_inventory, manage_orders, view_certifications, approve_workflows, view_reports, manage_projects, view_audit_logs |
| **Store** | view_materials, view_parts, manage_inventory, receive_materials, issue_materials, stocktake, view_orders, manage_barcodes |
| **Purchase** | view_materials, view_parts, manage_suppliers, manage_orders, view_inventory, create_requisitions, view_certifications |
| **QA** | view_materials, view_parts, manage_certifications, quality_checks, approve_materials, reject_materials, view_inventory, view_suppliers, manage_qa_workflows |
| **Engineer** | manage_materials, manage_parts, view_suppliers, view_inventory, manage_bom, view_certifications, technical_approvals |
| **Technician** | view_materials, view_parts, view_inventory, record_usage, scan_barcodes, view_work_orders |
| **Viewer** | view_materials, view_parts, view_suppliers, view_inventory, view_orders, view_certifications, view_reports |

---

### Logout
Logout current user (logs the session end).

```
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

**Note:** Since JWT tokens are stateless, the client should discard tokens after calling this endpoint. For complete session invalidation, implement a token blacklist.

---

### Get Login History
Get login history for current user (security auditing).

```
GET /api/v1/auth/login-history?limit=10
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "user_id": 1,
  "login_history": [
    {
      "login_at": "2026-01-22T15:30:00",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
      "success": true,
      "failure_reason": null,
      "is_logout": false
    },
    {
      "login_at": "2026-01-22T14:00:00",
      "ip_address": "192.168.1.100",
      "user_agent": "PostmanRuntime/7.32.0",
      "success": false,
      "failure_reason": "Invalid password",
      "is_logout": false
    }
  ]
}
```

---

### Get All Login History (Director Only)
Get login history for all users (security audit).

```
GET /api/v1/auth/all-login-history?user_id=2&success_only=false&limit=50
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `user_id` (optional): Filter by specific user
- `success_only` (optional): Only show successful logins
- `limit` (optional): Number of records to return (default: 50)

**Response:**
```json
{
  "total_records": 25,
  "login_history": [
    {
      "user_id": 2,
      "login_at": "2026-01-22T15:30:00",
      "ip_address": "192.168.1.105",
      "user_agent": "Mozilla/5.0...",
      "success": true,
      "failure_reason": null,
      "is_logout": false
    }
  ]
}
```

---

### Register New User (Director/Superuser Only)
```
POST /api/v1/auth/register
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "john.engineer@company.com",
  "password": "securePassword123",
  "full_name": "John Engineer",
  "employee_id": "EMP-001",
  "phone": "+1-555-0101",
  "department": "ENGINEERING",
  "designation": "Senior Materials Engineer",
  "role": "engineer",
  "is_active": true,
  "is_superuser": false,
  "can_approve_workflows": false,
  "approval_limit": 5000.00,
  "notes": "Senior Materials Engineer - Titanium specialist"
}
```

**Response:**
```json
{
  "id": 2,
  "email": "john.engineer@company.com",
  "full_name": "John Engineer",
  "employee_id": "EMP-001",
  "phone": "+1-555-0101",
  "department": "ENGINEERING",
  "designation": "Senior Materials Engineer",
  "role": "engineer",
  "is_active": true,
  "is_superuser": false,
  "can_approve_workflows": false,
  "approval_limit": 5000.00,
  "last_login": null,
  "notes": "Senior Materials Engineer - Titanium specialist",
  "created_at": "2026-01-22T10:45:00",
  "updated_at": "2026-01-22T10:45:00"
}
```

**Available Roles:**
| Role | Description |
|------|-------------|
| `director` | Full system access, final approvals |
| `head_of_operations` | Operations oversight and management |
| `store` | Inventory and material movements |
| `purchase` | Procurement and supplier management |
| `qa` | Quality assurance and certifications |
| `engineer` | Technical specifications and parts |
| `technician` | Floor operations |
| `viewer` | Read-only access |

**Available Departments:**
- `OPERATIONS`
- `PROCUREMENT`
- `QUALITY_ASSURANCE`
- `ENGINEERING`
- `PRODUCTION`
- `STORES`
- `FINANCE`
- `ADMINISTRATION`

---

### Change Password
```
POST /api/v1/auth/change-password?current_password=oldpass&new_password=newpass123
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Password changed successfully"
}
```

**Requirements:**
- New password must be at least 8 characters
- Current password must be verified

---

## Users

### List Users (Director Only)
```
GET /api/v1/users?page=1&page_size=20
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "email": "director@pickupbiz.com",
      "full_name": "Admin User",
      "employee_id": null,
      "phone": null,
      "department": "ADMINISTRATION",
      "designation": null,
      "role": "director",
      "is_active": true,
      "is_superuser": true,
      "can_approve_workflows": true,
      "approval_limit": null,
      "created_at": "2026-01-22T10:00:00",
      "updated_at": "2026-01-22T10:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

### Get User by ID
```
GET /api/v1/users/1
Authorization: Bearer <access_token>
```

---

### Update User (Director Only)
```
PUT /api/v1/users/2
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "full_name": "John Senior Engineer",
  "department": "ENGINEERING",
  "designation": "Principal Engineer",
  "role": "head_of_operations",
  "can_approve_workflows": true,
  "approval_limit": 25000.00,
  "phone": "+1-555-0102"
}
```

---

### Delete User (Director Only)
```
DELETE /api/v1/users/2
Authorization: Bearer <access_token>
```

**Note:** User deletion is soft-delete (sets `is_active: false`) to preserve audit trail.

---

## Material Categories

### List Categories
```
GET /api/v1/materials/categories?page=1&page_size=20
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Metals",
      "code": "MTL",
      "description": "Metal materials including alloys",
      "parent_id": null,
      "created_at": "2026-01-22T10:00:00",
      "updated_at": "2026-01-22T10:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

### Create Category
```
POST /api/v1/materials/categories
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Metals",
  "code": "MTL",
  "description": "Metal materials including alloys",
  "parent_id": null
}
```

**More Category Examples:**
```json
{
  "name": "Titanium Alloys",
  "code": "MTL-TI",
  "description": "Titanium-based alloys for aerospace",
  "parent_id": 1
}
```

```json
{
  "name": "Composites",
  "code": "CMP",
  "description": "Composite materials including carbon fiber"
}
```

```json
{
  "name": "Adhesives & Sealants",
  "code": "ADH",
  "description": "Structural adhesives and sealants"
}
```

---

### Update Category
```
PUT /api/v1/materials/categories/1
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Metals & Alloys",
  "description": "All metal and alloy materials"
}
```

---

## Materials

### List Materials
```
GET /api/v1/materials?page=1&page_size=20
Authorization: Bearer <access_token>
```

**With Filters:**
```
GET /api/v1/materials?material_type=metal&status=active&search=titanium
GET /api/v1/materials?category_id=1
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Titanium Alloy Ti-6Al-4V",
      "part_number": "MAT-TI-6AL4V-001",
      "specification": "AMS 4911",
      "material_type": "alloy",
      "category_id": 1,
      "status": "active",
      "density": 4.43,
      "tensile_strength": 950.0,
      "yield_strength": 880.0,
      "hardness": 36.0,
      "melting_point": 1660.0,
      "description": "Grade 5 titanium alloy",
      "mil_spec": "MIL-T-9046",
      "ams_spec": "AMS 4911",
      "is_hazardous": false,
      "shelf_life_days": null,
      "storage_requirements": "Store in dry conditions",
      "unit_cost": 85.50,
      "unit_of_measure": "kg",
      "minimum_order_quantity": 10.0,
      "created_at": "2026-01-22T10:00:00",
      "updated_at": "2026-01-22T10:00:00",
      "category": {
        "id": 1,
        "name": "Metals",
        "code": "MTL"
      }
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

### Get Material by ID
```
GET /api/v1/materials/1
Authorization: Bearer <access_token>
```

---

### Create Material
```
POST /api/v1/materials
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body - Titanium Alloy:**
```json
{
  "name": "Titanium Alloy Ti-6Al-4V",
  "part_number": "MAT-TI-6AL4V-001",
  "specification": "AMS 4911",
  "material_type": "alloy",
  "category_id": 1,
  "status": "active",
  "density": 4.43,
  "tensile_strength": 950.0,
  "yield_strength": 880.0,
  "hardness": 36.0,
  "melting_point": 1660.0,
  "description": "Grade 5 titanium alloy, excellent strength-to-weight ratio",
  "mil_spec": "MIL-T-9046",
  "ams_spec": "AMS 4911",
  "is_hazardous": false,
  "storage_requirements": "Store in dry conditions, avoid contact with steel",
  "unit_cost": 85.50,
  "unit_of_measure": "kg",
  "minimum_order_quantity": 10.0
}
```

**Request Body - Aluminum Alloy:**
```json
{
  "name": "Aluminum Alloy 7075-T6",
  "part_number": "MAT-AL-7075-001",
  "specification": "AMS 4045",
  "material_type": "alloy",
  "category_id": 1,
  "status": "active",
  "density": 2.81,
  "tensile_strength": 572.0,
  "yield_strength": 503.0,
  "hardness": 150.0,
  "melting_point": 635.0,
  "description": "High-strength aluminum alloy for structural applications",
  "mil_spec": "MIL-A-12545",
  "ams_spec": "AMS 4045",
  "is_hazardous": false,
  "unit_cost": 12.75,
  "unit_of_measure": "kg",
  "minimum_order_quantity": 25.0
}
```

**Request Body - Carbon Fiber Composite:**
```json
{
  "name": "Carbon Fiber Prepreg T800",
  "part_number": "MAT-CF-T800-001",
  "specification": "Toray T800S",
  "material_type": "composite",
  "status": "active",
  "description": "Intermediate modulus carbon fiber prepreg",
  "is_hazardous": false,
  "shelf_life_days": 365,
  "storage_requirements": "Store at -18°C, sealed in original packaging",
  "unit_cost": 125.00,
  "unit_of_measure": "sqm",
  "minimum_order_quantity": 50.0
}
```

**Request Body - Structural Adhesive:**
```json
{
  "name": "Epoxy Film Adhesive FM 300-2",
  "part_number": "MAT-ADH-FM300-001",
  "specification": "Cytec FM 300-2",
  "material_type": "adhesive",
  "status": "active",
  "description": "Modified epoxy film adhesive for metal-to-metal bonding",
  "is_hazardous": true,
  "shelf_life_days": 180,
  "storage_requirements": "Store at -18°C in sealed container",
  "unit_cost": 450.00,
  "unit_of_measure": "sqm",
  "minimum_order_quantity": 10.0
}
```

**Material Types:** `metal`, `composite`, `polymer`, `ceramic`, `alloy`, `coating`, `adhesive`, `other`

**Material Status:** `active`, `discontinued`, `pending_approval`, `restricted`

---

### Update Material
```
PUT /api/v1/materials/1
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "unit_cost": 92.00,
  "status": "active",
  "storage_requirements": "Updated storage requirements"
}
```

---

### Delete Material
```
DELETE /api/v1/materials/1
Authorization: Bearer <access_token>
```

---

## Parts

### List Parts
```
GET /api/v1/parts?page=1&page_size=20
Authorization: Bearer <access_token>
```

**With Filters:**
```
GET /api/v1/parts?status=production&criticality=critical&search=bracket
```

---

### Create Part
```
POST /api/v1/parts
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body - Critical Flight Component:**
```json
{
  "name": "Main Landing Gear Strut",
  "part_number": "MLG-STRUT-001",
  "revision": "C",
  "status": "production",
  "criticality": "critical",
  "description": "Main landing gear strut assembly",
  "drawing_number": "DWG-MLG-001",
  "weight": 125.5,
  "weight_unit": "kg",
  "is_serialized": true,
  "requires_inspection": true,
  "inspection_interval_hours": 500,
  "unit_cost": 45000.00,
  "lead_time_days": 90
}
```

**Request Body - Structural Bracket:**
```json
{
  "name": "Wing Spar Attachment Bracket",
  "part_number": "WS-BKT-001",
  "revision": "A",
  "status": "production",
  "criticality": "major",
  "description": "Titanium bracket for wing spar attachment",
  "drawing_number": "DWG-WSB-001",
  "weight": 2.3,
  "weight_unit": "kg",
  "is_serialized": false,
  "requires_inspection": true,
  "unit_cost": 850.00,
  "lead_time_days": 30
}
```

**Request Body - Standard Part:**
```json
{
  "name": "Avionics Bay Access Panel",
  "part_number": "AV-PNL-001",
  "revision": "B",
  "status": "production",
  "criticality": "minor",
  "description": "Composite access panel for avionics bay",
  "drawing_number": "DWG-AVP-001",
  "weight": 0.8,
  "weight_unit": "kg",
  "is_serialized": false,
  "requires_inspection": false,
  "unit_cost": 125.00,
  "lead_time_days": 14
}
```

**Part Status:** `design`, `prototype`, `production`, `obsolete`, `restricted`

**Part Criticality:** `critical`, `major`, `minor`, `standard`

---

### Get Part by ID
```
GET /api/v1/parts/1
Authorization: Bearer <access_token>
```

---

### Update Part
```
PUT /api/v1/parts/1
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "revision": "D",
  "status": "production",
  "unit_cost": 47500.00
}
```

---

### Add Material to Part (Bill of Materials)
```
POST /api/v1/parts/1/materials
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "part_id": 1,
  "material_id": 1,
  "quantity_required": 15.5,
  "unit_of_measure": "kg",
  "is_primary": true,
  "notes": "Primary structural material"
}
```

---

### List Part Materials
```
GET /api/v1/parts/1/materials
Authorization: Bearer <access_token>
```

---

### Remove Material from Part
```
DELETE /api/v1/parts/1/materials/1
Authorization: Bearer <access_token>
```

---

## Suppliers

### List Suppliers
```
GET /api/v1/suppliers?page=1&page_size=20
Authorization: Bearer <access_token>
```

**With Filters:**
```
GET /api/v1/suppliers?status=active&tier=tier_1&search=aerospace
```

---

### Create Supplier
```
POST /api/v1/suppliers
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body - Tier 1 Certified Supplier:**
```json
{
  "name": "Aerospace Materials Corp",
  "code": "AMC-001",
  "status": "active",
  "tier": "tier_1",
  "contact_name": "John Smith",
  "contact_email": "john.smith@aeromaterials.com",
  "contact_phone": "+1-555-0100",
  "address_line_1": "1234 Aviation Blvd",
  "address_line_2": "Suite 500",
  "city": "Los Angeles",
  "state": "California",
  "postal_code": "90045",
  "country": "USA",
  "is_as9100_certified": true,
  "is_nadcap_certified": true,
  "is_itar_compliant": true,
  "cage_code": "1ABC2",
  "quality_rating": 4.8,
  "delivery_rating": 4.5,
  "notes": "Primary titanium supplier, 10+ year relationship"
}
```

**Request Body - Secondary Supplier:**
```json
{
  "name": "Global Composites Ltd",
  "code": "GCL-001",
  "status": "active",
  "tier": "tier_2",
  "contact_name": "Sarah Johnson",
  "contact_email": "s.johnson@globalcomposites.com",
  "contact_phone": "+1-555-0200",
  "address_line_1": "5678 Industrial Park",
  "city": "Seattle",
  "state": "Washington",
  "postal_code": "98108",
  "country": "USA",
  "is_as9100_certified": true,
  "is_nadcap_certified": false,
  "is_itar_compliant": true,
  "cage_code": "2DEF3",
  "quality_rating": 4.2,
  "delivery_rating": 4.0,
  "notes": "Carbon fiber and prepreg supplier"
}
```

**Supplier Status:** `active`, `inactive`, `pending_approval`, `suspended`, `blacklisted`

**Supplier Tier:** `tier_1`, `tier_2`, `tier_3`

---

### Get Supplier by ID
```
GET /api/v1/suppliers/1
Authorization: Bearer <access_token>
```

---

### Update Supplier
```
PUT /api/v1/suppliers/1
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "quality_rating": 4.9,
  "delivery_rating": 4.7,
  "notes": "Updated: Excellent performance in Q4 2025"
}
```

---

### Add Material to Supplier Catalog
```
POST /api/v1/suppliers/1/materials
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "supplier_id": 1,
  "material_id": 1,
  "supplier_part_number": "AMC-TI64-SHEET",
  "unit_price": 82.50,
  "currency": "USD",
  "minimum_order_quantity": 10.0,
  "lead_time_days": 21,
  "is_preferred": true,
  "notes": "Standard lead time, expedited available"
}
```

---

### List Supplier Materials
```
GET /api/v1/suppliers/1/materials
Authorization: Bearer <access_token>
```

---

## Inventory

### List Inventory
```
GET /api/v1/inventory?page=1&page_size=20
Authorization: Bearer <access_token>
```

**With Filters:**
```
GET /api/v1/inventory?material_id=1&status=available&location=Warehouse-A
GET /api/v1/inventory?lot_number=LOT-2026-001&expired_only=true
```

---

### Create Inventory (Receive Material)
```
POST /api/v1/inventory
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "material_id": 1,
  "lot_number": "LOT-2026-001",
  "batch_number": "BATCH-001",
  "serial_number": null,
  "quantity": 100.0,
  "reserved_quantity": 0,
  "unit_of_measure": "kg",
  "status": "available",
  "location": "Warehouse-A",
  "bin_number": "A-12-03",
  "received_date": "2026-01-22",
  "manufacture_date": "2026-01-10",
  "expiration_date": "2028-01-10",
  "certificate_of_conformance": "COC-2026-00123",
  "heat_number": "HT-45678",
  "mill_test_report": "MTR-2026-00456",
  "unit_cost": 85.50,
  "notes": "Received from AMC, PO-2026-001"
}
```

**Inventory Status:** `available`, `reserved`, `quarantine`, `expired`, `consumed`

---

### Get Inventory by ID
```
GET /api/v1/inventory/1
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "material_id": 1,
  "lot_number": "LOT-2026-001",
  "batch_number": "BATCH-001",
  "quantity": 100.0,
  "reserved_quantity": 15.0,
  "available_quantity": 85.0,
  "is_expired": false,
  "status": "available",
  "location": "Warehouse-A",
  "bin_number": "A-12-03",
  "received_date": "2026-01-22",
  "expiration_date": "2028-01-10",
  "created_at": "2026-01-22T10:00:00",
  "updated_at": "2026-01-22T10:00:00"
}
```

---

### Update Inventory
```
PUT /api/v1/inventory/1
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "location": "Warehouse-B",
  "bin_number": "B-05-01",
  "status": "available"
}
```

---

### Create Inventory Transaction
```
POST /api/v1/inventory/1/transactions
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Issue Material:**
```json
{
  "inventory_id": 1,
  "transaction_type": "issue",
  "quantity": 25.0,
  "unit_of_measure": "kg",
  "reference_number": "REF-2026-001",
  "work_order": "WO-MLG-001",
  "from_location": "Warehouse-A",
  "reason": "Issued for MLG Strut production",
  "notes": "Issued to production floor"
}
```

**Transfer Material:**
```json
{
  "inventory_id": 1,
  "transaction_type": "transfer",
  "quantity": 50.0,
  "unit_of_measure": "kg",
  "from_location": "Warehouse-A",
  "to_location": "Warehouse-B",
  "reason": "Relocating to climate-controlled storage"
}
```

**Adjustment:**
```json
{
  "inventory_id": 1,
  "transaction_type": "adjustment",
  "quantity": 98.5,
  "unit_of_measure": "kg",
  "reason": "Physical inventory count adjustment",
  "notes": "Variance: -1.5 kg"
}
```

**Quarantine Material:**
```json
{
  "inventory_id": 1,
  "transaction_type": "quarantine",
  "quantity": 100.0,
  "unit_of_measure": "kg",
  "reason": "Quality hold pending investigation",
  "notes": "Surface contamination suspected"
}
```

**Release from Quarantine:**
```json
{
  "inventory_id": 1,
  "transaction_type": "release",
  "quantity": 100.0,
  "unit_of_measure": "kg",
  "reason": "QC inspection passed",
  "notes": "Released by QA-John Smith"
}
```

**Scrap Material:**
```json
{
  "inventory_id": 1,
  "transaction_type": "scrap",
  "quantity": 5.0,
  "unit_of_measure": "kg",
  "reason": "Material damaged during handling",
  "notes": "Scrap report SR-2026-001"
}
```

**Transaction Types:** `receipt`, `issue`, `transfer`, `adjustment`, `return`, `scrap`, `quarantine`, `release`

---

### List Inventory Transactions
```
GET /api/v1/inventory/1/transactions
Authorization: Bearer <access_token>
```

---

## Certifications

### List Certifications
```
GET /api/v1/certifications?page=1&page_size=20
Authorization: Bearer <access_token>
```

**With Filters:**
```
GET /api/v1/certifications?certification_type=as9100&status=active
```

---

### Create Certification
```
POST /api/v1/certifications
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body - AS9100:**
```json
{
  "name": "AS9100 Rev D Quality Management",
  "code": "AS9100-D",
  "certification_type": "as9100",
  "status": "active",
  "issuing_authority": "SAE International",
  "certificate_number": "AS9100-2025-12345",
  "issue_date": "2025-06-15",
  "expiration_date": "2028-06-14",
  "last_audit_date": "2025-06-10",
  "next_audit_date": "2026-06-10",
  "description": "Aerospace Quality Management System certification",
  "scope": "Design, manufacture, and repair of aerospace components",
  "document_url": "https://docs.company.com/certs/as9100-d.pdf",
  "notes": "Annual surveillance audit required"
}
```

**Request Body - NADCAP:**
```json
{
  "name": "NADCAP Non-Destructive Testing",
  "code": "NADCAP-NDT",
  "certification_type": "nadcap",
  "status": "active",
  "issuing_authority": "Performance Review Institute",
  "certificate_number": "NDT-2025-67890",
  "issue_date": "2025-03-01",
  "expiration_date": "2027-02-28",
  "description": "NADCAP accreditation for NDT processes",
  "scope": "Radiographic, ultrasonic, and penetrant inspection"
}
```

**Request Body - MIL-SPEC:**
```json
{
  "name": "MIL-T-9046 Titanium Sheet Compliance",
  "code": "MIL-T-9046",
  "certification_type": "mil_spec",
  "status": "active",
  "issuing_authority": "U.S. Department of Defense",
  "issue_date": "2024-01-01",
  "description": "Military specification for titanium alloy sheet",
  "scope": "Ti-6Al-4V sheet and plate products"
}
```

**Certification Types:** `as9100`, `nadcap`, `iso9001`, `mil_spec`, `ams`, `astm`, `faa`, `easa`, `other`

**Certification Status:** `active`, `expired`, `pending`, `revoked`, `suspended`

---

### Get Certification by ID
```
GET /api/v1/certifications/1
Authorization: Bearer <access_token>
```

---

### Update Certification
```
PUT /api/v1/certifications/1
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "last_audit_date": "2026-01-15",
  "next_audit_date": "2027-01-15",
  "notes": "Surveillance audit completed successfully"
}
```

---

### Link Certification to Material
```
POST /api/v1/certifications/materials
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "material_id": 1,
  "certification_id": 1,
  "is_mandatory": true,
  "is_verified": true,
  "verified_date": "2026-01-20",
  "verified_by": "QA Engineer - John Doe",
  "verification_document": "https://docs.company.com/verification/mat-001-cert-001.pdf",
  "notes": "Material meets all AS9100 requirements"
}
```

---

### Update Material Certification
```
PUT /api/v1/certifications/materials/1
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "is_verified": true,
  "verified_date": "2026-01-22",
  "verified_by": "QA Manager - Jane Smith"
}
```

---

## Orders

### List Orders
```
GET /api/v1/orders?page=1&page_size=20
Authorization: Bearer <access_token>
```

**With Filters:**
```
GET /api/v1/orders?status=pending_approval&priority=high&supplier_id=1
```

---

### Create Order
```
POST /api/v1/orders
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "supplier_id": 1,
  "status": "draft",
  "priority": "high",
  "expected_delivery_date": "2026-02-15",
  "shipping_method": "Air Freight",
  "purchase_order_number": "PO-2026-00001",
  "work_order_reference": "WO-MLG-001",
  "requires_certification": true,
  "notes": "Urgent order for MLG production",
  "items": [
    {
      "material_id": 1,
      "quantity_ordered": 50.0,
      "unit_of_measure": "kg",
      "unit_price": 85.50,
      "expected_delivery_date": "2026-02-15",
      "specification_notes": "AMS 4911, Heat treated condition",
      "notes": "Split shipment acceptable"
    },
    {
      "material_id": 2,
      "quantity_ordered": 100.0,
      "unit_of_measure": "kg",
      "unit_price": 12.75,
      "expected_delivery_date": "2026-02-10",
      "specification_notes": "AMS 4045 T6 condition"
    }
  ]
}
```

**Order Status:** `draft`, `pending_approval`, `approved`, `ordered`, `shipped`, `partially_received`, `received`, `cancelled`, `on_hold`

**Order Priority:** `low`, `normal`, `high`, `critical`, `aog` (Aircraft on Ground - highest)

---

### Get Order by ID
```
GET /api/v1/orders/1
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "order_number": "PO-20260122-A1B2C3",
  "supplier_id": 1,
  "created_by": 1,
  "status": "draft",
  "priority": "high",
  "order_date": null,
  "expected_delivery_date": "2026-02-15",
  "actual_delivery_date": null,
  "subtotal": 5550.00,
  "tax": 0,
  "shipping_cost": 0,
  "total": 5550.00,
  "currency": "USD",
  "items": [
    {
      "id": 1,
      "order_id": 1,
      "material_id": 1,
      "quantity_ordered": 50.0,
      "quantity_received": 0,
      "unit_of_measure": "kg",
      "unit_price": 85.50,
      "total_price": 4275.00,
      "is_fully_received": false
    },
    {
      "id": 2,
      "order_id": 1,
      "material_id": 2,
      "quantity_ordered": 100.0,
      "quantity_received": 0,
      "unit_of_measure": "kg",
      "unit_price": 12.75,
      "total_price": 1275.00,
      "is_fully_received": false
    }
  ],
  "created_at": "2026-01-22T10:00:00",
  "updated_at": "2026-01-22T10:00:00"
}
```

---

### Update Order
```
PUT /api/v1/orders/1
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "priority": "critical",
  "expected_delivery_date": "2026-02-10",
  "tax": 450.00,
  "shipping_cost": 250.00,
  "notes": "Expedited due to production schedule"
}
```

---

### Submit Order for Approval
```
POST /api/v1/orders/1/submit
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "order_number": "PO-20260122-A1B2C3",
  "status": "pending_approval",
  ...
}
```

---

### Approve Order
```
POST /api/v1/orders/1/approve
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "order_number": "PO-20260122-A1B2C3",
  "status": "approved",
  "order_date": "2026-01-22",
  ...
}
```

---

### Add Item to Order
```
POST /api/v1/orders/1/items
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "material_id": 3,
  "quantity_ordered": 25.0,
  "unit_of_measure": "sqm",
  "unit_price": 125.00,
  "expected_delivery_date": "2026-02-20",
  "specification_notes": "Toray T800S prepreg",
  "notes": "Store at -18°C upon receipt"
}
```

---

### Update Order Item
```
PUT /api/v1/orders/1/items/1
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "quantity_ordered": 75.0,
  "quantity_received": 50.0,
  "notes": "Partial shipment received"
}
```

---

### Delete Order Item
```
DELETE /api/v1/orders/1/items/2
Authorization: Bearer <access_token>
```

---

### Delete Order (Draft Only)
```
DELETE /api/v1/orders/1
Authorization: Bearer <access_token>
```

---

## Quick Reference - Status Values

| Entity | Status Values |
|--------|---------------|
| **User Roles** | `director`, `head_of_operations`, `store`, `purchase`, `qa`, `engineer`, `technician`, `viewer` |
| **Departments** | `OPERATIONS`, `PROCUREMENT`, `QUALITY_ASSURANCE`, `ENGINEERING`, `PRODUCTION`, `STORES`, `FINANCE`, `ADMINISTRATION` |
| Material Type | `metal`, `composite`, `polymer`, `ceramic`, `alloy`, `coating`, `adhesive`, `other` |
| Material Status | `active`, `discontinued`, `pending_approval`, `restricted` |
| Part Status | `design`, `prototype`, `production`, `obsolete`, `restricted` |
| Part Criticality | `critical`, `major`, `minor`, `standard` |
| Supplier Status | `active`, `inactive`, `pending_approval`, `suspended`, `blacklisted` |
| Supplier Tier | `tier_1`, `tier_2`, `tier_3` |
| Inventory Status | `available`, `reserved`, `quarantine`, `expired`, `consumed` |
| Transaction Type | `receipt`, `issue`, `transfer`, `adjustment`, `return`, `scrap`, `quarantine`, `release` |
| Certification Type | `as9100`, `nadcap`, `iso9001`, `mil_spec`, `ams`, `astm`, `faa`, `easa`, `other` |
| Certification Status | `active`, `expired`, `pending`, `revoked`, `suspended` |
| Order Status | `draft`, `pending_approval`, `approved`, `ordered`, `shipped`, `partially_received`, `received`, `cancelled`, `on_hold` |
| Order Priority | `low`, `normal`, `high`, `critical`, `aog` |

---

## Role-Based Access Control (RBAC)

### Permission Matrix

| Endpoint Category | Director | Head of Ops | Store | Purchase | QA | Engineer | Technician | Viewer |
|-------------------|----------|-------------|-------|----------|-----|----------|------------|--------|
| **Users** | Full | View | - | - | - | - | - | - |
| **Materials** | Full | View | View | View | View | Full | View | View |
| **Parts** | Full | View | View | View | View | Full | View | View |
| **Suppliers** | Full | View | - | Full | View | View | - | View |
| **Inventory** | Full | View | Full | View | View | View | View | View |
| **Orders** | Full | Full | View | Full | - | - | - | View |
| **Certifications** | Full | View | - | View | Full | View | - | View |
| **Workflows** | Approve | Approve | - | - | Approve | - | - | - |
| **Projects** | Full | Full | - | - | - | View | - | View |
| **Audit Logs** | Full | View | - | - | - | - | - | - |

### Authentication Flow

```
1. POST /auth/login (username, password)
   ↓
2. Receive access_token + refresh_token
   ↓
3. Include token in Authorization header: "Bearer <token>"
   ↓
4. Token expires → POST /auth/refresh with refresh_token
   ↓
5. POST /auth/logout to end session
```

### Security Features

- **Password Hashing**: bcrypt with automatic salt
- **JWT Tokens**: RS256/HS256 signed tokens
- **Token Expiry**: Access tokens expire (configurable, default 30 min)
- **Refresh Tokens**: Long-lived tokens for session renewal
- **Login History**: All login attempts logged with IP and user agent
- **Role Validation**: Every protected endpoint validates user role

---

## Postman Collection Import

To quickly import all these requests into Postman:

1. Create a new Collection called "Aerospace Materials API"
2. Set a Collection Variable: `base_url` = `http://localhost:5055/api/v1`
3. Set a Collection Variable: `token` = (your access token after login)
4. Use `{{base_url}}` in request URLs
5. Use `Bearer {{token}}` in Authorization headers

### Auto-save Token Script (Add to Login request Tests tab):
```javascript
var jsonData = pm.response.json();
pm.collectionVariables.set("token", jsonData.access_token);
pm.collectionVariables.set("refresh_token", jsonData.refresh_token);
```

---

## Complete API Endpoint Reference

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/auth/login` | Login with username/password | No |
| `POST` | `/auth/logout` | Logout current session | Yes |
| `POST` | `/auth/refresh` | Refresh access token | No (needs refresh_token) |
| `POST` | `/auth/register` | Register new user | Yes (Director) |
| `POST` | `/auth/change-password` | Change password | Yes |
| `GET` | `/auth/me` | Get current user | Yes |
| `GET` | `/auth/validate` | Validate token | Yes |
| `GET` | `/auth/permissions` | Get user permissions | Yes |
| `GET` | `/auth/login-history` | Get own login history | Yes |
| `GET` | `/auth/all-login-history` | Get all login history | Yes (Director) |

### Users (`/api/v1/users`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/users` | List all users | Yes (Director) |
| `GET` | `/users/{id}` | Get user by ID | Yes |
| `PUT` | `/users/{id}` | Update user | Yes (Director) |
| `DELETE` | `/users/{id}` | Delete user | Yes (Director) |

### Materials (`/api/v1/materials`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/materials` | List materials | Yes |
| `GET` | `/materials/{id}` | Get material by ID | Yes |
| `POST` | `/materials` | Create material | Yes (Engineer+) |
| `PUT` | `/materials/{id}` | Update material | Yes (Engineer+) |
| `DELETE` | `/materials/{id}` | Delete material | Yes (Engineer+) |
| `GET` | `/materials/categories` | List categories | Yes |
| `POST` | `/materials/categories` | Create category | Yes (Engineer+) |
| `PUT` | `/materials/categories/{id}` | Update category | Yes (Engineer+) |
| `DELETE` | `/materials/categories/{id}` | Delete category | Yes (Engineer+) |

### Parts (`/api/v1/parts`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/parts` | List parts | Yes |
| `GET` | `/parts/{id}` | Get part by ID | Yes |
| `POST` | `/parts` | Create part | Yes (Engineer+) |
| `PUT` | `/parts/{id}` | Update part | Yes (Engineer+) |
| `DELETE` | `/parts/{id}` | Delete part | Yes (Engineer+) |
| `GET` | `/parts/{id}/materials` | List part materials | Yes |
| `POST` | `/parts/{id}/materials` | Add material to part | Yes (Engineer+) |
| `DELETE` | `/parts/{id}/materials/{mat_id}` | Remove material | Yes (Engineer+) |

### Suppliers (`/api/v1/suppliers`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/suppliers` | List suppliers | Yes |
| `GET` | `/suppliers/{id}` | Get supplier by ID | Yes |
| `POST` | `/suppliers` | Create supplier | Yes (Purchase+) |
| `PUT` | `/suppliers/{id}` | Update supplier | Yes (Purchase+) |
| `DELETE` | `/suppliers/{id}` | Delete supplier | Yes (Purchase+) |
| `GET` | `/suppliers/{id}/materials` | List supplier materials | Yes |
| `POST` | `/suppliers/{id}/materials` | Add supplier material | Yes (Purchase+) |

### Inventory (`/api/v1/inventory`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/inventory` | List inventory | Yes |
| `GET` | `/inventory/{id}` | Get inventory by ID | Yes |
| `POST` | `/inventory` | Create inventory | Yes (Store+) |
| `PUT` | `/inventory/{id}` | Update inventory | Yes (Store+) |
| `DELETE` | `/inventory/{id}` | Delete inventory | Yes (Store+) |
| `GET` | `/inventory/{id}/transactions` | List transactions | Yes |
| `POST` | `/inventory/{id}/transactions` | Create transaction | Yes (Store+) |

### Certifications (`/api/v1/certifications`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/certifications` | List certifications | Yes |
| `GET` | `/certifications/{id}` | Get certification by ID | Yes |
| `POST` | `/certifications` | Create certification | Yes (QA+) |
| `PUT` | `/certifications/{id}` | Update certification | Yes (QA+) |
| `DELETE` | `/certifications/{id}` | Delete certification | Yes (QA+) |
| `POST` | `/certifications/materials` | Link cert to material | Yes (QA+) |
| `PUT` | `/certifications/materials/{id}` | Update material cert | Yes (QA+) |

### Orders (`/api/v1/orders`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/orders` | List orders | Yes |
| `GET` | `/orders/{id}` | Get order by ID | Yes |
| `POST` | `/orders` | Create order | Yes (Purchase+) |
| `PUT` | `/orders/{id}` | Update order | Yes (Purchase+) |
| `DELETE` | `/orders/{id}` | Delete order (draft) | Yes (Purchase+) |
| `POST` | `/orders/{id}/submit` | Submit for approval | Yes (Purchase+) |
| `POST` | `/orders/{id}/approve` | Approve order | Yes (Head of Ops+) |
| `POST` | `/orders/{id}/items` | Add order item | Yes (Purchase+) |
| `PUT` | `/orders/{id}/items/{item_id}` | Update order item | Yes (Purchase+) |
| `DELETE` | `/orders/{id}/items/{item_id}` | Delete order item | Yes (Purchase+) |

---

## Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `404 Not Found` | Wrong URL path | Check the endpoint URL - don't forget prefixes like `/auth/` |
| `401 Unauthorized` | Missing or invalid token | Login again to get a fresh token |
| `403 Forbidden` | Insufficient permissions | Use an account with appropriate role |
| `422 Unprocessable Entity` | Invalid request data | Check request body format and required fields |
| `500 Internal Server Error` | Server-side error | Check server logs for details |

---

## Troubleshooting

### Token Issues
```
# Token expired? Refresh it:
POST /api/v1/auth/refresh?refresh_token=<your_refresh_token>

# Token invalid? Login again:
POST /api/v1/auth/login
```

### Permission Denied
Check your role has access to the endpoint. Use:
```
GET /api/v1/auth/permissions
```

### 404 Not Found on Auth Endpoints
Make sure you include `/auth/` in the URL:
- ❌ Wrong: `POST /api/v1/logout`
- ✅ Correct: `POST /api/v1/auth/logout`
