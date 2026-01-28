# FUNCTIONAL SPECIFICATION DOCUMENT
## Aerospace Parts Material Management System

**Version:** 1.0.0  
**Date:** January 25, 2026  
**Prepared By:** PickupBiz Software Pvt Ltd  
**Prepared For:** ADS Innotech

---

## DOCUMENT CONTROL

| **Item** | **Details** |
|----------|-------------|
| **Document Title** | Functional Specification Document - Aerospace Parts Material Management System |
| **Version** | 1.0.0 |
| **Date** | January 25, 2026 |
| **Author** | PickupBiz Software Pvt Ltd |
| **Client** | ADS Innotech |
| **Status** | Final |
| **Classification** | Confidential |

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Introduction](#2-introduction)
3. [System Overview](#3-system-overview)
4. [Functional Requirements](#4-functional-requirements)
5. [User Roles and Permissions](#5-user-roles-and-permissions)
6. [API Specifications](#6-api-specifications)
7. [Technical Architecture](#7-technical-architecture)
8. [Non-Functional Requirements](#8-non-functional-requirements)
9. [Data Models](#9-data-models)
10. [Appendices](#10-appendices)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Purpose
This Functional Specification Document (FSD) describes the functional requirements, features, and specifications for the **Aerospace Parts Material Management System** developed by PickupBiz Software Pvt Ltd for ADS Innotech.

### 1.2 Scope
The system is a comprehensive web-based application designed to manage aerospace parts, materials, suppliers, inventory, certifications, and procurement orders. It provides end-to-end traceability, role-based access control, workflow management, and real-time monitoring capabilities.

### 1.3 Key Features
- **JWT Authentication** with role-based access control (RBAC)
- **Material Management** with specifications and compliance tracking
- **Parts Management** with Bill of Materials (BOM)
- **Supplier Management** with aerospace certifications
- **Inventory Tracking** with full lot/batch traceability
- **Purchase Order Management** with approval workflows
- **Barcode & QR Code** generation and scanning
- **Real-time Dashboard** and analytics
- **Reporting** in PDF, Excel, and CSV formats
- **WebSocket** support for real-time updates

---

## 2. INTRODUCTION

### 2.1 Background
ADS Innotech requires a comprehensive material management system to track aerospace parts and materials throughout their lifecycle, from procurement to production, ensuring compliance with industry standards and maintaining full traceability.

### 2.2 Objectives
- Streamline material procurement and inventory management
- Ensure compliance with aerospace industry standards (AS9100, NADCAP, ITAR)
- Provide complete traceability of materials and parts
- Automate approval workflows for purchase orders
- Enable real-time monitoring and reporting
- Support barcode-based material tracking

### 2.3 Document Conventions
- **Bold** text indicates important terms or concepts
- *Italic* text indicates emphasis
- Code blocks indicate technical specifications
- Tables provide structured information

---

## 3. SYSTEM OVERVIEW

### 3.1 System Architecture
The system is built using:
- **Backend:** FastAPI (Python 3.10+)
- **Database:** PostgreSQL 13+
- **Authentication:** JWT (JSON Web Tokens)
- **API Style:** RESTful API with WebSocket support
- **Frontend:** React (separate application)

### 3.2 System Components

#### 3.2.1 Core Modules
1. **Authentication & Authorization Module**
2. **User Management Module**
3. **Material Management Module**
4. **Parts Management Module**
5. **Supplier Management Module**
6. **Inventory Management Module**
7. **Purchase Order Management Module**
8. **Certification Management Module**
9. **Barcode Management Module**
10. **Workflow Management Module**
11. **Dashboard & Analytics Module**
12. **Reporting Module**
13. **Notification Module**

### 3.3 System Interfaces
- **REST API:** `/api/v1/*` endpoints
- **WebSocket:** `/api/v1/ws` for real-time updates
- **Swagger UI:** `/api/v1/docs` for API documentation
- **ReDoc:** `/api/v1/redoc` for alternative API documentation

---

## 4. FUNCTIONAL REQUIREMENTS

### 4.1 Authentication & Authorization Module

#### 4.1.1 User Authentication
- **FR-AUTH-001:** System shall provide user login functionality using email and password
- **FR-AUTH-002:** System shall generate JWT access tokens (90 minutes expiry) and refresh tokens (7 days expiry)
- **FR-AUTH-003:** System shall support token refresh mechanism
- **FR-AUTH-004:** System shall log all login attempts for security auditing
- **FR-AUTH-005:** System shall track last login timestamp for each user
- **FR-AUTH-006:** System shall support password change functionality
- **FR-AUTH-007:** System shall support user logout (token invalidation)

#### 4.1.2 User Registration
- **FR-AUTH-008:** System shall allow user registration (admin only)
- **FR-AUTH-009:** System shall validate email uniqueness
- **FR-AUTH-010:** System shall assign roles during registration

#### 4.1.3 Token Management
- **FR-AUTH-011:** System shall validate JWT tokens on each protected request
- **FR-AUTH-012:** System shall return 401 Unauthorized for invalid/expired tokens
- **FR-AUTH-013:** System shall support token validation endpoint

### 4.2 User Management Module

#### 4.2.1 User CRUD Operations
- **FR-USER-001:** System shall allow listing all users (paginated)
- **FR-USER-002:** System shall allow viewing user details by ID
- **FR-USER-003:** System shall allow updating user information
- **FR-USER-004:** System shall allow deleting users (soft delete)
- **FR-USER-005:** System shall support user activation/deactivation

#### 4.2.2 User Profile
- **FR-USER-006:** System shall provide endpoint to get current user information (`/auth/me`)
- **FR-USER-007:** System shall track user permissions based on role
- **FR-USER-008:** System shall maintain user login history

### 4.3 Material Management Module

#### 4.3.1 Material CRUD Operations
- **FR-MAT-001:** System shall allow creating materials with specifications
- **FR-MAT-002:** System shall allow listing materials with pagination and filtering
- **FR-MAT-003:** System shall allow viewing material details by ID
- **FR-MAT-004:** System shall allow updating material information
- **FR-MAT-005:** System shall allow deleting materials
- **FR-MAT-006:** System shall enforce unique item numbers

#### 4.3.2 Material Attributes
- **FR-MAT-007:** System shall track material item number, title, and specification
- **FR-MAT-008:** System shall track heat number and batch number
- **FR-MAT-009:** System shall track quantity and unit of measure
- **FR-MAT-010:** System shall track minimum and maximum stock levels
- **FR-MAT-011:** System shall categorize materials by type (Raw, WIP, Finished)
- **FR-MAT-012:** System shall track material status (Active, Inactive, Obsolete)
- **FR-MAT-013:** System shall link materials to purchase orders
- **FR-MAT-014:** System shall link materials to suppliers
- **FR-MAT-015:** System shall link materials to projects

#### 4.3.3 Material Categories
- **FR-MAT-016:** System shall support hierarchical material categories
- **FR-MAT-017:** System shall allow creating, updating, and deleting categories
- **FR-MAT-018:** System shall allow filtering materials by category

#### 4.3.4 Material Search
- **FR-MAT-019:** System shall support searching materials by title or item number
- **FR-MAT-020:** System shall support filtering by material type, status, and category

### 4.4 Parts Management Module

#### 4.4.1 Part CRUD Operations
- **FR-PART-001:** System shall allow creating parts with specifications
- **FR-PART-002:** System shall allow listing parts with pagination
- **FR-PART-003:** System shall allow viewing part details by ID
- **FR-PART-004:** System shall allow updating part information
- **FR-PART-005:** System shall allow deleting parts

#### 4.4.2 Part Attributes
- **FR-PART-006:** System shall track part number, title, and description
- **FR-PART-007:** System shall track part status (Active, Inactive, Obsolete)
- **FR-PART-008:** System shall track part criticality level (Low, Medium, High, Critical)
- **FR-PART-009:** System shall track revision number and drawing number

#### 4.4.3 Bill of Materials (BOM)
- **FR-PART-010:** System shall allow adding materials to parts (BOM)
- **FR-PART-011:** System shall allow viewing all materials for a part
- **FR-PART-012:** System shall allow updating BOM entries
- **FR-PART-013:** System shall allow removing materials from BOM
- **FR-PART-014:** System shall track quantity per part for each material

### 4.5 Supplier Management Module

#### 4.5.1 Supplier CRUD Operations
- **FR-SUP-001:** System shall allow creating supplier records
- **FR-SUP-002:** System shall allow listing suppliers with pagination
- **FR-SUP-003:** System shall allow viewing supplier details by ID
- **FR-SUP-004:** System shall allow updating supplier information
- **FR-SUP-005:** System shall allow deleting suppliers

#### 4.5.2 Supplier Attributes
- **FR-SUP-006:** System shall track supplier name, code, and contact information
- **FR-SUP-007:** System shall track supplier status (Active, Inactive, Suspended)
- **FR-SUP-008:** System shall track supplier tier (Tier 1, Tier 2, Tier 3)
- **FR-SUP-009:** System shall track supplier address and tax information
- **FR-SUP-010:** System shall link suppliers to materials

#### 4.5.3 Supplier Certifications
- **FR-SUP-011:** System shall track aerospace certifications (AS9100, NADCAP, ITAR)
- **FR-SUP-012:** System shall track certification expiry dates
- **FR-SUP-013:** System shall alert on certification expiry

### 4.6 Inventory Management Module

#### 4.6.1 Inventory Tracking
- **FR-INV-001:** System shall allow creating inventory records
- **FR-INV-002:** System shall allow listing inventory items with pagination
- **FR-INV-003:** System shall allow viewing inventory details by ID
- **FR-INV-004:** System shall allow updating inventory information
- **FR-INV-005:** System shall track inventory status (Available, Reserved, Allocated, Consumed)

#### 4.6.2 Inventory Transactions
- **FR-INV-006:** System shall record all inventory transactions
- **FR-INV-007:** System shall support transaction types (Receive, Issue, Return, Adjust, Transfer)
- **FR-INV-008:** System shall maintain transaction history for each inventory item
- **FR-INV-009:** System shall track lot/batch numbers for traceability

#### 4.6.3 Material Instances
- **FR-INV-010:** System shall track individual material instances
- **FR-INV-011:** System shall support material instance status lifecycle
- **FR-INV-012:** System shall track material allocations to projects/work orders
- **FR-INV-013:** System shall support material receipt from Goods Receipt Notes (GRN)
- **FR-INV-014:** System shall support bulk material receipt

### 4.7 Purchase Order Management Module

#### 4.7.1 Purchase Order CRUD Operations
- **FR-PO-001:** System shall allow creating purchase orders
- **FR-PO-002:** System shall allow listing purchase orders with pagination and filtering
- **FR-PO-003:** System shall allow viewing purchase order details by ID
- **FR-PO-004:** System shall allow updating purchase orders (draft status only)
- **FR-PO-005:** System shall allow deleting purchase orders (draft status only)

#### 4.7.2 Purchase Order Attributes
- **FR-PO-006:** System shall track PO number, supplier, and order date
- **FR-PO-007:** System shall track PO status (Draft, Submitted, Approved, Rejected, Ordered, Received, Completed, Cancelled)
- **FR-PO-008:** System shall track expected delivery date
- **FR-PO-009:** System shall track total PO value
- **FR-PO-010:** System shall link POs to projects

#### 4.7.3 Purchase Order Line Items
- **FR-PO-011:** System shall allow adding line items to purchase orders
- **FR-PO-012:** System shall allow updating line items
- **FR-PO-013:** System shall allow deleting line items
- **FR-PO-014:** System shall track quantity ordered, unit price, and total for each line item
- **FR-PO-015:** System shall track quantity received for each line item
- **FR-PO-016:** System shall track line item status (Pending, Partially Received, Received, Rejected)

#### 4.7.4 Purchase Order Workflow
- **FR-PO-017:** System shall support PO submission for approval
- **FR-PO-018:** System shall support PO approval workflow based on value thresholds
- **FR-PO-019:** System shall support auto-approval for POs below threshold ($5,000)
- **FR-PO-020:** System shall require standard approval for POs between $5,000 and $25,000
- **FR-PO-021:** System shall require high-value approval for POs above $25,000
- **FR-PO-022:** System shall require director approval for POs above $100,000
- **FR-PO-023:** System shall support PO rejection with comments
- **FR-PO-024:** System shall maintain approval history
- **FR-PO-025:** System shall support PO ordering (sending to supplier)
- **FR-PO-026:** System shall support PO cancellation

#### 4.7.5 Goods Receipt Note (GRN)
- **FR-PO-027:** System shall allow creating GRN from purchase orders
- **FR-PO-028:** System shall track GRN status (Received, Inspected, Accepted, Rejected)
- **FR-PO-029:** System shall allow viewing all GRNs for a PO
- **FR-PO-030:** System shall support GRN inspection workflow
- **FR-PO-031:** System shall support GRN acceptance/rejection
- **FR-PO-032:** System shall track quantity received vs. quantity ordered

### 4.8 Certification Management Module

#### 4.8.1 Certification CRUD Operations
- **FR-CERT-001:** System shall allow creating certifications
- **FR-CERT-002:** System shall allow listing certifications with pagination
- **FR-CERT-003:** System shall allow viewing certification details by ID
- **FR-CERT-004:** System shall allow updating certification information
- **FR-CERT-005:** System shall allow deleting certifications

#### 4.8.2 Certification Attributes
- **FR-CERT-006:** System shall track certification name, type, and issuing authority
- **FR-CERT-007:** System shall track certification number and expiry date
- **FR-CERT-008:** System shall track certification status (Active, Expired, Revoked)
- **FR-CERT-009:** System shall link certifications to materials

#### 4.8.3 Material Certifications
- **FR-CERT-010:** System shall allow linking certifications to materials
- **FR-CERT-011:** System shall allow updating material-certification links
- **FR-CERT-012:** System shall allow removing certification links from materials

### 4.9 Barcode Management Module

#### 4.9.1 Barcode Generation
- **FR-BAR-001:** System shall generate barcodes (Code128, QR Code) for materials
- **FR-BAR-002:** System shall support barcode templates with configurable patterns
- **FR-BAR-003:** System shall generate barcodes from purchase orders
- **FR-BAR-004:** System shall generate WIP (Work in Progress) barcodes
- **FR-BAR-005:** System shall generate finished goods barcodes
- **FR-BAR-006:** System shall support barcode image generation (PNG)
- **FR-BAR-007:** System shall support QR code image generation

#### 4.9.2 Barcode Scanning
- **FR-BAR-008:** System shall process barcode scans
- **FR-BAR-009:** System shall support scan-to-receive functionality
- **FR-BAR-010:** System shall validate barcode format
- **FR-BAR-011:** System shall maintain scan history
- **FR-BAR-012:** System shall track scan location and timestamp

#### 4.9.3 Barcode Lookup
- **FR-BAR-013:** System shall allow looking up materials by barcode value
- **FR-BAR-014:** System shall provide barcode traceability chain
- **FR-BAR-015:** System shall display barcode scan history

### 4.10 Workflow Management Module

#### 4.10.1 Workflow Templates
- **FR-WF-001:** System shall support configurable workflow templates
- **FR-WF-002:** System shall allow creating workflow templates
- **FR-WF-003:** System shall allow listing workflow templates
- **FR-WF-004:** System shall support multi-step approval workflows

#### 4.10.2 Workflow Instances
- **FR-WF-005:** System shall create workflow instances for POs and material movements
- **FR-WF-006:** System shall track workflow status and current step
- **FR-WF-007:** System shall allow approving workflow steps
- **FR-WF-008:** System shall allow rejecting workflows
- **FR-WF-009:** System shall maintain workflow history

#### 4.10.3 Pending Approvals
- **FR-WF-010:** System shall provide endpoint to list pending approvals
- **FR-WF-011:** System shall filter approvals by user role

### 4.11 Dashboard & Analytics Module

#### 4.11.1 Dashboard Overview
- **FR-DASH-001:** System shall provide comprehensive dashboard overview
- **FR-DASH-002:** System shall display PO status summary
- **FR-DASH-003:** System shall display material status summary
- **FR-DASH-004:** System shall display inventory status
- **FR-DASH-005:** System shall display active alerts

#### 4.11.2 Analytics
- **FR-DASH-006:** System shall provide PO vs. received comparison
- **FR-DASH-007:** System shall provide delivery performance analytics
- **FR-DASH-008:** System shall provide PO-to-production lead time analysis
- **FR-DASH-009:** System shall provide supplier performance metrics
- **FR-DASH-010:** System shall provide project-wise consumption analysis
- **FR-DASH-011:** System shall provide material movement history
- **FR-DASH-012:** System shall provide stock analysis (fast-moving, low stock)

### 4.12 Reporting Module

#### 4.12.1 Report Generation
- **FR-REP-001:** System shall generate PO reports in PDF, Excel, and CSV formats
- **FR-REP-002:** System shall generate material reports
- **FR-REP-003:** System shall generate inventory reports
- **FR-REP-004:** System shall generate supplier performance reports
- **FR-REP-005:** System shall generate project consumption reports
- **FR-REP-006:** System shall support date range filtering for reports
- **FR-REP-007:** System shall provide report download endpoints

#### 4.12.2 Quick Exports
- **FR-REP-008:** System shall provide quick CSV export for POs
- **FR-REP-009:** System shall provide quick CSV export for inventory
- **FR-REP-010:** System shall provide quick CSV export for materials

### 4.13 Notification Module

#### 4.13.1 Real-time Notifications
- **FR-NOT-001:** System shall send real-time notifications via WebSocket
- **FR-NOT-002:** System shall notify on PO status changes
- **FR-NOT-003:** System shall notify on material status changes
- **FR-NOT-004:** System shall notify on new alerts
- **FR-NOT-005:** System shall notify on inventory updates
- **FR-NOT-006:** System shall notify on approval requirements
- **FR-NOT-007:** System shall notify on GRN receipt
- **FR-NOT-008:** System shall notify on inspection completion

#### 4.13.2 Alert Types
- **FR-NOT-009:** System shall generate PO pending approval alerts
- **FR-NOT-010:** System shall generate quantity mismatch alerts
- **FR-NOT-011:** System shall generate delayed delivery alerts
- **FR-NOT-012:** System shall generate fast-moving material alerts
- **FR-NOT-013:** System shall generate low stock alerts
- **FR-NOT-014:** System shall generate inspection pending alerts

---

## 5. USER ROLES AND PERMISSIONS

### 5.1 Role-Based Access Control (RBAC)
The system implements role-based access control with the following roles:

### 5.2 Director Role
- **Full system access**
- **High-value PO approvals** (above $100,000)
- **User management** (create, update, delete users)
- **View all login history**
- **All permissions of other roles**

### 5.3 Head of Operations Role
- **Operations approvals**
- **Workflow management**
- **PO approvals** (standard and high-value)
- **Material and inventory management**
- **View operational dashboards**

### 5.4 Purchase Role
- **PO creation and management**
- **Supplier management**
- **Procurement operations**
- **View purchase-related reports**

### 5.5 Store Role
- **Material receipt**
- **Inventory management**
- **GRN processing**
- **Barcode scanning**
- **Material instance management**

### 5.6 QA Role
- **Quality inspections**
- **Material certifications**
- **GRN inspection and approval**
- **Certification management**

### 5.7 Engineer Role
- **Material management** (create, update, delete)
- **Parts management** (create, update, delete)
- **BOM creation and management**
- **Technical specifications management**
- **Certification management**

### 5.8 Technician Role
- **Inventory operations**
- **Material handling**
- **Barcode scanning**
- **View inventory and materials**

### 5.9 Viewer Role
- **Read-only access** to all resources
- **View dashboards and reports**
- **No create, update, or delete permissions**

### 5.10 Permission Matrix

| Feature | Director | Head of Ops | Purchase | Store | QA | Engineer | Technician | Viewer |
|---------|----------|-------------|----------|-------|----|----------|-----------|--------|
| User Management | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Material CRUD | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | View |
| Parts CRUD | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | View |
| Supplier CRUD | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | View |
| PO Creation | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | View |
| PO Approval | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | View |
| GRN Processing | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | View |
| Inventory Management | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✓ | View |
| Certification Management | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | ✗ | View |
| Barcode Operations | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✓ | View |
| Reports | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## 6. API SPECIFICATIONS

### 6.1 API Base URL
- **Base URL:** `http://localhost:5055/api/v1`
- **API Version:** v1
- **API Style:** RESTful

### 6.2 Authentication
- **Method:** JWT (JSON Web Tokens)
- **Token Type:** Bearer
- **Access Token Expiry:** 90 minutes
- **Refresh Token Expiry:** 7 days

### 6.3 API Endpoints Summary

#### 6.3.1 Authentication Endpoints
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/register` - Register new user (admin only)
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/change-password` - Change password
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/validate` - Validate token
- `GET /api/v1/auth/permissions` - Get user permissions
- `GET /api/v1/auth/login-history` - Get login history
- `GET /api/v1/auth/all-login-history` - Get all users' login history (director only)

#### 6.3.2 User Management Endpoints
- `GET /api/v1/users` - List users (paginated)
- `GET /api/v1/users/{id}` - Get user by ID
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

#### 6.3.3 Material Management Endpoints
- `GET /api/v1/materials` - List materials (with filtering)
- `POST /api/v1/materials` - Create material
- `GET /api/v1/materials/{id}` - Get material
- `PUT /api/v1/materials/{id}` - Update material
- `DELETE /api/v1/materials/{id}` - Delete material
- `GET /api/v1/materials/categories` - List categories
- `POST /api/v1/materials/categories` - Create category
- `PUT /api/v1/materials/categories/{id}` - Update category

#### 6.3.4 Parts Management Endpoints
- `GET /api/v1/parts` - List parts
- `POST /api/v1/parts` - Create part
- `GET /api/v1/parts/{id}` - Get part
- `PUT /api/v1/parts/{id}` - Update part
- `DELETE /api/v1/parts/{id}` - Delete part
- `GET /api/v1/parts/{id}/materials` - List part materials (BOM)
- `POST /api/v1/parts/{id}/materials` - Add material to part
- `PUT /api/v1/parts/{id}/materials/{link_id}` - Update BOM entry
- `DELETE /api/v1/parts/{id}/materials/{link_id}` - Remove material from BOM

#### 6.3.5 Supplier Management Endpoints
- `GET /api/v1/suppliers` - List suppliers
- `POST /api/v1/suppliers` - Create supplier
- `GET /api/v1/suppliers/{id}` - Get supplier
- `PUT /api/v1/suppliers/{id}` - Update supplier
- `DELETE /api/v1/suppliers/{id}` - Delete supplier

#### 6.3.6 Inventory Management Endpoints
- `GET /api/v1/inventory` - List inventory items
- `POST /api/v1/inventory` - Create inventory record
- `GET /api/v1/inventory/{id}` - Get inventory item
- `PUT /api/v1/inventory/{id}` - Update inventory
- `POST /api/v1/inventory/{id}/transactions` - Create transaction
- `GET /api/v1/inventory/{id}/transactions` - Get transaction history

#### 6.3.7 Material Instance Endpoints
- `GET /api/v1/material-instances` - List material instances
- `POST /api/v1/material-instances` - Create material instance
- `GET /api/v1/material-instances/{id}` - Get material instance
- `PUT /api/v1/material-instances/{id}` - Update material instance
- `DELETE /api/v1/material-instances/{id}` - Delete material instance
- `POST /api/v1/material-instances/receive-from-grn` - Receive from GRN
- `POST /api/v1/material-instances/bulk-receive` - Bulk receive
- `POST /api/v1/material-instances/{id}/change-status` - Change status
- `POST /api/v1/material-instances/{id}/inspect` - Inspect material
- `GET /api/v1/material-instances/{id}/history` - Get status history
- `POST /api/v1/material-instances/allocations` - Create allocation
- `GET /api/v1/material-instances/allocations` - List allocations
- `POST /api/v1/material-instances/allocations/{id}/issue` - Issue allocation
- `POST /api/v1/material-instances/allocations/{id}/return` - Return allocation
- `GET /api/v1/material-instances/summary/by-status` - Status summary
- `GET /api/v1/material-instances/summary/project/{id}` - Project summary

#### 6.3.8 Purchase Order Endpoints
- `GET /api/v1/purchase-orders` - List purchase orders
- `POST /api/v1/purchase-orders` - Create purchase order
- `GET /api/v1/purchase-orders/{id}` - Get purchase order
- `PUT /api/v1/purchase-orders/{id}` - Update purchase order
- `DELETE /api/v1/purchase-orders/{id}` - Delete purchase order
- `POST /api/v1/purchase-orders/{id}/items` - Add line item
- `PUT /api/v1/purchase-orders/{id}/items/{item_id}` - Update line item
- `DELETE /api/v1/purchase-orders/{id}/items/{item_id}` - Delete line item
- `POST /api/v1/purchase-orders/{id}/submit` - Submit for approval
- `POST /api/v1/purchase-orders/{id}/approve` - Approve PO
- `POST /api/v1/purchase-orders/{id}/order` - Send to supplier
- `POST /api/v1/purchase-orders/{id}/cancel` - Cancel PO
- `GET /api/v1/purchase-orders/{id}/history` - Get approval history
- `POST /api/v1/purchase-orders/{id}/receive` - Create GRN
- `GET /api/v1/purchase-orders/{id}/receipts` - List GRNs
- `GET /api/v1/purchase-orders/grn/{grn_id}` - Get GRN
- `POST /api/v1/purchase-orders/grn/{grn_id}/inspect` - Inspect GRN
- `POST /api/v1/purchase-orders/grn/{grn_id}/accept` - Accept GRN

#### 6.3.9 Certification Endpoints
- `GET /api/v1/certifications` - List certifications
- `POST /api/v1/certifications` - Create certification
- `GET /api/v1/certifications/{id}` - Get certification
- `PUT /api/v1/certifications/{id}` - Update certification
- `DELETE /api/v1/certifications/{id}` - Delete certification
- `POST /api/v1/certifications/materials` - Link certification to material
- `PUT /api/v1/certifications/materials/{link_id}` - Update link
- `DELETE /api/v1/certifications/materials/{link_id}` - Remove link

#### 6.3.10 Barcode Endpoints
- `GET /api/v1/barcodes` - List barcodes
- `POST /api/v1/barcodes` - Create barcode
- `GET /api/v1/barcodes/{id}` - Get barcode details
- `GET /api/v1/barcodes/lookup/{value}` - Lookup by barcode value
- `PUT /api/v1/barcodes/{id}` - Update barcode
- `DELETE /api/v1/barcodes/{id}` - Delete barcode
- `POST /api/v1/barcodes/generate` - Generate barcode
- `POST /api/v1/barcodes/generate-from-po` - Generate from PO
- `POST /api/v1/barcodes/scan` - Process scan
- `POST /api/v1/barcodes/scan-to-receive` - Scan to receive
- `POST /api/v1/barcodes/validate` - Validate barcode
- `POST /api/v1/barcodes/create-wip` - Create WIP barcode
- `POST /api/v1/barcodes/create-finished-goods` - Create finished goods barcode
- `GET /api/v1/barcodes/{id}/traceability` - Get traceability chain
- `GET /api/v1/barcodes/{id}/scan-history` - Get scan history
- `GET /api/v1/barcodes/{id}/image` - Get barcode image
- `GET /api/v1/barcodes/{id}/qr` - Get QR code image
- `GET /api/v1/barcodes/summary/by-stage` - Summary by stage
- `GET /api/v1/barcodes/summary/by-po/{po_id}` - Summary by PO

#### 6.3.11 Workflow Endpoints
- `GET /api/v1/workflows/templates` - List workflow templates
- `POST /api/v1/workflows/templates` - Create workflow template
- `GET /api/v1/workflows/pending` - Get pending approvals

#### 6.3.12 Dashboard Endpoints
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
- `GET /api/v1/dashboard/stock-analysis` - Stock analysis
- `GET /api/v1/dashboard/alerts` - Active alerts

#### 6.3.13 Reporting Endpoints
- `POST /api/v1/reports/po` - Generate PO report
- `POST /api/v1/reports/materials` - Generate material report
- `POST /api/v1/reports/inventory` - Generate inventory report
- `POST /api/v1/reports/suppliers` - Generate supplier report
- `POST /api/v1/reports/project-consumption` - Generate project consumption report
- `GET /api/v1/reports/download/{filename}` - Download report
- `GET /api/v1/reports/export/po-csv` - Quick PO CSV export
- `GET /api/v1/reports/export/inventory-csv` - Quick inventory CSV export
- `GET /api/v1/reports/export/materials-csv` - Quick materials CSV export

#### 6.3.14 WebSocket Endpoint
- `WS /api/v1/ws?token={jwt}` - WebSocket connection for real-time updates

### 6.4 API Response Formats

#### 6.4.1 Success Response
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

#### 6.4.2 Error Response
```json
{
  "detail": "Error message"
}
```

### 6.5 Pagination
- **Default Page Size:** 20
- **Maximum Page Size:** 100
- **Query Parameters:** `page`, `page_size`

---

## 7. TECHNICAL ARCHITECTURE

### 7.1 Technology Stack

#### 7.1.1 Backend
- **Framework:** FastAPI (Python 3.10+)
- **Database:** PostgreSQL 13+
- **ORM:** SQLAlchemy (async support)
- **Migrations:** Alembic
- **Authentication:** JWT (PyJWT)
- **Password Hashing:** bcrypt

#### 7.1.2 API Documentation
- **Swagger UI:** Available at `/api/v1/docs`
- **ReDoc:** Available at `/api/v1/redoc`
- **OpenAPI Schema:** Available at `/api/v1/openapi.json`

#### 7.1.3 Real-time Communication
- **WebSocket:** Native FastAPI WebSocket support

#### 7.1.4 Reporting
- **PDF Generation:** ReportLab or similar
- **Excel Generation:** openpyxl or similar
- **CSV Export:** Built-in Python CSV module

### 7.2 Database Schema

#### 7.2.1 Core Tables
- `users` - User accounts and authentication
- `materials` - Material master data
- `material_categories` - Material categorization
- `parts` - Part master data
- `part_materials` - Bill of Materials (BOM)
- `suppliers` - Supplier master data
- `inventory` - Inventory records
- `inventory_transactions` - Transaction history
- `material_instances` - Individual material instances
- `material_allocations` - Material allocations
- `purchase_orders` - Purchase order headers
- `po_line_items` - Purchase order line items
- `goods_receipt_notes` - GRN records
- `certifications` - Certification master data
- `material_certifications` - Material-certification links
- `barcode_labels` - Barcode records
- `barcode_scan_logs` - Scan history
- `workflow_templates` - Workflow definitions
- `workflow_instances` - Active workflows
- `login_history` - Security audit log
- `audit_logs` - System audit trail

### 7.3 Security

#### 7.3.1 Authentication
- JWT-based authentication
- Password hashing using bcrypt
- Token expiry and refresh mechanism
- Login attempt logging

#### 7.3.2 Authorization
- Role-based access control (RBAC)
- Endpoint-level permission checks
- Resource-level access control

#### 7.3.3 Data Security
- SQL injection prevention (ORM)
- XSS prevention (input validation)
- CORS configuration
- Secure password storage

### 7.4 Performance Requirements
- **API Response Time:** < 500ms for standard queries
- **Database Queries:** Optimized with indexes
- **Pagination:** Implemented for all list endpoints
- **Caching:** Can be implemented for frequently accessed data

---

## 8. NON-FUNCTIONAL REQUIREMENTS

### 8.1 Performance Requirements
- **NFR-001:** System shall respond to API requests within 500ms for 95% of requests
- **NFR-002:** System shall support concurrent users (minimum 50)
- **NFR-003:** System shall support pagination for all list endpoints
- **NFR-004:** System shall optimize database queries with proper indexing

### 8.2 Scalability Requirements
- **NFR-005:** System architecture shall support horizontal scaling
- **NFR-006:** Database shall support large datasets (millions of records)
- **NFR-007:** System shall support async operations where applicable

### 8.3 Security Requirements
- **NFR-008:** System shall encrypt passwords using bcrypt
- **NFR-009:** System shall use HTTPS in production
- **NFR-010:** System shall log all authentication attempts
- **NFR-011:** System shall implement CORS policies
- **NFR-012:** System shall validate all user inputs

### 8.4 Reliability Requirements
- **NFR-013:** System shall have 99.5% uptime
- **NFR-014:** System shall handle errors gracefully
- **NFR-015:** System shall provide meaningful error messages
- **NFR-016:** System shall maintain data integrity with transactions

### 8.5 Usability Requirements
- **NFR-017:** API shall provide comprehensive documentation (Swagger/ReDoc)
- **NFR-018:** API responses shall be in JSON format
- **NFR-019:** API shall provide consistent error response format
- **NFR-020:** System shall support internationalization (future)

### 8.6 Maintainability Requirements
- **NFR-021:** Code shall follow Python PEP 8 standards
- **NFR-022:** System shall use database migrations (Alembic)
- **NFR-023:** System shall have comprehensive logging
- **NFR-024:** System shall have unit and integration tests

### 8.7 Compatibility Requirements
- **NFR-025:** System shall support Python 3.10+
- **NFR-026:** System shall support PostgreSQL 13+
- **NFR-027:** API shall support standard HTTP methods (GET, POST, PUT, DELETE)
- **NFR-028:** API shall support JSON request/response format

---

## 9. DATA MODELS

### 9.1 User Model
- `id` - Primary key
- `email` - Unique email address
- `hashed_password` - Encrypted password
- `full_name` - User's full name
- `role` - User role (enum)
- `department` - Department (enum)
- `is_active` - Active status
- `is_superuser` - Superuser flag
- `last_login` - Last login timestamp
- `created_at` - Creation timestamp
- `updated_at` - Update timestamp

### 9.2 Material Model
- `id` - Primary key
- `item_number` - Unique item number
- `title` - Material title
- `specification` - Material specification
- `heat_number` - Heat number
- `batch_number` - Batch number
- `quantity` - Quantity
- `unit_of_measure` - Unit of measure
- `min_stock_level` - Minimum stock level
- `max_stock_level` - Maximum stock level
- `material_type` - Type (Raw, WIP, Finished)
- `status` - Status (Active, Inactive, Obsolete)
- `category_id` - Category reference
- `supplier_id` - Supplier reference
- `po_id` - Purchase order reference
- `project_id` - Project reference
- `created_at` - Creation timestamp
- `updated_at` - Update timestamp

### 9.3 Purchase Order Model
- `id` - Primary key
- `po_number` - Unique PO number
- `supplier_id` - Supplier reference
- `order_date` - Order date
- `expected_delivery_date` - Expected delivery date
- `status` - PO status (enum)
- `total_value` - Total PO value
- `project_id` - Project reference
- `created_by` - Creator user ID
- `approved_by` - Approver user ID
- `created_at` - Creation timestamp
- `updated_at` - Update timestamp

### 9.4 Inventory Model
- `id` - Primary key
- `material_id` - Material reference
- `lot_number` - Lot number
- `batch_number` - Batch number
- `quantity` - Available quantity
- `unit_of_measure` - Unit of measure
- `status` - Inventory status (enum)
- `location` - Storage location
- `expiry_date` - Expiry date (if applicable)
- `created_at` - Creation timestamp
- `updated_at` - Update timestamp

---

## 10. APPENDICES

### 10.1 Glossary

| Term | Definition |
|------|------------|
| **BOM** | Bill of Materials - List of materials required for a part |
| **GRN** | Goods Receipt Note - Document for receiving materials |
| **JWT** | JSON Web Token - Authentication token format |
| **PO** | Purchase Order - Document for ordering materials |
| **RBAC** | Role-Based Access Control - Authorization model |
| **WIP** | Work in Progress - Materials in production |
| **AS9100** | Aerospace quality management standard |
| **NADCAP** | National Aerospace and Defense Contractors Accreditation Program |
| **ITAR** | International Traffic in Arms Regulations |

### 10.2 Acronyms
- **API:** Application Programming Interface
- **CRUD:** Create, Read, Update, Delete
- **CSV:** Comma-Separated Values
- **PDF:** Portable Document Format
- **REST:** Representational State Transfer
- **SQL:** Structured Query Language
- **UI:** User Interface
- **WS:** WebSocket

### 10.3 References
- FastAPI Documentation: https://fastapi.tiangolo.com/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- JWT Specification: https://jwt.io/
- AS9100 Standard: Aerospace quality management
- NADCAP: Aerospace accreditation program

### 10.4 Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | January 25, 2026 | PickupBiz Software Pvt Ltd | Initial release |

### 10.5 Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Prepared By** | PickupBiz Software Pvt Ltd | | |
| **Reviewed By** | | | |
| **Approved By** | ADS Innotech | | |

---

## DOCUMENT END

**Prepared By:** PickupBiz Software Pvt Ltd  
**For:** ADS Innotech  
**Version:** 1.0.0  
**Date:** January 25, 2026

---

*This document is confidential and proprietary to ADS Innotech. Unauthorized distribution is prohibited.*
