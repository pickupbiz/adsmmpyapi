# Database Schema Documentation

## Overview

This document describes the database schema for the Aerospace Parts Material Management System with async PostgreSQL support using asyncpg.

## Database Configuration

- **Driver**: asyncpg (async) / psycopg2 (sync for migrations)
- **ORM**: SQLAlchemy 2.0 with async support
- **Migrations**: Alembic

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           USER & AUTHENTICATION                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐                                                               │
│  │    Users     │◄────────────────────┐                                         │
│  ├──────────────┤                     │ reports_to                              │
│  │ id           │─────────────────────┘                                         │
│  │ email        │                                                               │
│  │ role         │  (director, head_of_operations, store, purchase, qa,         │
│  │ department   │   engineer, technician, viewer)                               │
│  │ approval_limit│                                                              │
│  └──────┬───────┘                                                               │
│         │                                                                       │
│         ├──────────────────────────────────┐                                    │
│         │                                  │                                    │
│  ┌──────▼──────┐                   ┌───────▼───────┐                           │
│  │ LoginHistory│                   │   AuditLog    │                           │
│  └─────────────┘                   ├───────────────┤                           │
│                                    │ DataChangeLog │                           │
│                                    └───────────────┘                           │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                           MATERIAL MANAGEMENT                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────┐      ┌──────────────────┐                                │
│  │MaterialCategories│◄─────┤    Materials     │                                │
│  └──────────────────┘      ├──────────────────┤                                │
│         ▲                  │ part_number      │                                │
│         │ parent           │ material_type    │                                │
│         └──────────────────│ specifications   │                                │
│                            └────────┬─────────┘                                │
│                                     │                                          │
│         ┌───────────────────────────┼───────────────────────────┐              │
│         │                           │                           │              │
│         ▼                           ▼                           ▼              │
│  ┌──────────────┐           ┌──────────────┐           ┌──────────────────┐   │
│  │PartMaterials │           │  Inventory   │           │MaterialCertifica-│   │
│  │  (BOM link)  │           ├──────────────┤           │     tions        │   │
│  └──────────────┘           │ lot_number   │           └──────────────────┘   │
│         │                   │ quantity     │                    │              │
│         │                   │ location     │                    ▼              │
│         │                   └──────┬───────┘           ┌──────────────────┐   │
│         │                          │                   │  Certifications  │   │
│         │                          ▼                   │  (AS9100, NADCAP)│   │
│         │                   ┌──────────────┐           └──────────────────┘   │
│         │                   │  Inventory   │                                   │
│         │                   │ Transactions │                                   │
│         │                   └──────────────┘                                   │
│         │                                                                      │
│         ▼                                                                      │
│  ┌──────────────┐                                                              │
│  │    Parts     │◄─────────────────────────────────────┐                       │
│  ├──────────────┤                                      │ parent_part          │
│  │ part_number  │──────────────────────────────────────┘                       │
│  │ criticality  │                                                              │
│  └──────────────┘                                                              │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SUPPLIER & PROCUREMENT                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐           ┌──────────────┐           ┌──────────────┐        │
│  │  Suppliers   │◄──────────┤   Orders     │───────────►│  OrderItems  │        │
│  ├──────────────┤           ├──────────────┤           └──────────────┘        │
│  │ AS9100_cert  │           │ order_number │                    │               │
│  │ NADCAP_cert  │           │ status       │                    │               │
│  │ ITAR_compliant│          │ priority     │                    ▼               │
│  │ tier         │           │ workflow_id  │           ┌──────────────┐        │
│  └──────┬───────┘           └──────────────┘           │  Materials   │        │
│         │                                              └──────────────┘        │
│         ▼                                                                      │
│  ┌──────────────────┐                                                          │
│  │SupplierMaterials │                                                          │
│  │ (price, lead time)│                                                         │
│  └──────────────────┘                                                          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                           BARCODE TRACKING                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────┐           ┌──────────────────┐                           │
│  │  BarcodeLabels   │───────────►│ BarcodeScanLogs │                           │
│  ├──────────────────┤           ├──────────────────┤                           │
│  │ barcode_value    │           │ scan_timestamp   │                           │
│  │ barcode_type     │           │ scan_location    │                           │
│  │ entity_type      │           │ scan_action      │                           │
│  │ entity_id        │           │ is_successful    │                           │
│  │ lot_number       │           └──────────────────┘                           │
│  │ serial_number    │                                                          │
│  └──────────────────┘                                                          │
│         │                                                                      │
│         │ Links to: Materials, Inventory, Parts                                │
│         ▼                                                                      │
│  ┌─────────────────────────────────────────────────────┐                       │
│  │ entity_type = 'material' | 'inventory' | 'part'     │                       │
│  │ entity_id = ID of the linked entity                 │                       │
│  └─────────────────────────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                           WORKFLOW & APPROVALS                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────┐           ┌──────────────────┐                           │
│  │WorkflowTemplates │───────────►│  WorkflowSteps   │                           │
│  ├──────────────────┤           ├──────────────────┤                           │
│  │ workflow_type    │           │ step_order       │                           │
│  │ sla_hours        │           │ approver_role    │                           │
│  │ auto_approve_    │           │ amount_threshold │                           │
│  │   threshold      │           │ escalation_hours │                           │
│  └────────┬─────────┘           └──────────────────┘                           │
│           │                                                                    │
│           ▼                                                                    │
│  ┌──────────────────┐           ┌──────────────────┐                           │
│  │WorkflowInstances │───────────►│WorkflowApprovals │                           │
│  ├──────────────────┤           ├──────────────────┤                           │
│  │ reference_type   │           │ approver_id      │                           │
│  │ reference_id     │           │ status           │                           │
│  │ status           │           │ decision_at      │                           │
│  │ current_step     │           │ comments         │                           │
│  │ amount           │           │ signature_hash   │                           │
│  └──────────────────┘           └──────────────────┘                           │
│                                                                                │
│  Workflow Types:                                                               │
│  - purchase_order       - material_receipt    - quality_inspection             │
│  - material_requisition - material_issue      - scrap_request                  │
│  - inventory_adjustment - material_return     - bom_change                     │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PROJECTS & BOM                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐◄──────────────────────────┐                                  │
│  │   Projects   │                           │ parent_project                   │
│  ├──────────────┤───────────────────────────┘                                  │
│  │ project_number│                                                             │
│  │ customer_name │                                                             │
│  │ budget        │                                                             │
│  │ status        │                                                             │
│  └──────┬───────┘                                                              │
│         │                                                                      │
│         ├────────────────────────────────────┐                                 │
│         │                                    │                                 │
│         ▼                                    ▼                                 │
│  ┌──────────────────┐               ┌────────────────────┐                     │
│  │ BillOfMaterials  │               │MaterialRequisitions│                     │
│  ├──────────────────┤               ├────────────────────┤                     │
│  │ bom_number       │               │ requisition_number │                     │
│  │ revision         │               │ work_order         │                     │
│  │ bom_type         │               │ status             │                     │
│  │ status           │               └─────────┬──────────┘                     │
│  └────────┬─────────┘                         │                                │
│           │                                   ▼                                │
│           ▼                           ┌────────────────────┐                   │
│    ┌──────────────┐                   │MaterialRequisition │                   │
│    │   BOMItems   │                   │      Items         │                   │
│    ├──────────────┤                   └────────────────────┘                   │
│    │ item_number  │                                                            │
│    │ quantity     │                                                            │
│    │ scrap_factor │                                                            │
│    │ material_id  │──────────────────► Materials                               │
│    │ part_id      │──────────────────► Parts (sub-assemblies)                  │
│    │ child_bom_id │──────────────────► BillOfMaterials (nested BOMs)           │
│    └──────────────┘                                                            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Tables Summary

### User & Authentication
| Table | Description |
|-------|-------------|
| `users` | User accounts with roles and approval limits |
| `login_history` | Login/logout tracking for security |
| `audit_logs` | System-wide audit trail |
| `data_change_logs` | Field-level change tracking |

### Material Management
| Table | Description |
|-------|-------------|
| `material_categories` | Hierarchical material classification |
| `materials` | Material master data with specifications |
| `inventory` | Stock tracking with lot/batch traceability |
| `inventory_transactions` | All inventory movements |
| `certifications` | Industry certifications (AS9100, NADCAP, etc.) |
| `material_certifications` | Material-certification links |

### Parts
| Table | Description |
|-------|-------------|
| `parts` | Aerospace parts/assemblies |
| `part_materials` | Bill of materials links |

### Suppliers & Procurement
| Table | Description |
|-------|-------------|
| `suppliers` | Supplier master data with certifications |
| `supplier_materials` | Supplier pricing and lead times |
| `orders` | Purchase orders |
| `order_items` | Order line items |

### Barcode Tracking
| Table | Description |
|-------|-------------|
| `barcode_labels` | Barcode master with entity links |
| `barcode_scan_logs` | Scan history for traceability |

### Workflow & Approvals
| Table | Description |
|-------|-------------|
| `workflow_templates` | Approval workflow definitions |
| `workflow_steps` | Steps in each workflow |
| `workflow_instances` | Active workflow instances |
| `workflow_approvals` | Individual approval records |

### Projects & BOM
| Table | Description |
|-------|-------------|
| `projects` | Project master data |
| `bill_of_materials` | BOM headers |
| `bom_items` | BOM line items |
| `material_requisitions` | Material requests for projects |
| `material_requisition_items` | Requisition line items |

## User Roles & Permissions

| Role | Description | Key Permissions |
|------|-------------|-----------------|
| `director` | Full access | All operations, final approvals |
| `head_of_operations` | Operations management | Approve workflows, manage operations |
| `store` | Inventory management | Receive, issue, transfer materials |
| `purchase` | Procurement | Create/manage orders, supplier management |
| `qa` | Quality assurance | Inspections, certifications, quarantine |
| `engineer` | Technical | Materials, parts, BOMs, specifications |
| `technician` | Floor operations | Inventory transactions, scanning |
| `viewer` | Read-only | View all data |

## Workflow Types

| Type | Description | Typical Approvers |
|------|-------------|-------------------|
| `purchase_order` | PO approval | Purchase → Head of Ops → Director |
| `material_requisition` | Material request | Store → Engineer |
| `material_receipt` | Goods receipt | Store → QA |
| `material_issue` | Stock issue | Store |
| `inventory_adjustment` | Stock adjustments | Store → Head of Ops |
| `quality_inspection` | QC approval | QA → Engineer |
| `material_return` | Return to supplier | Store → Purchase |
| `scrap_request` | Scrap approval | QA → Head of Ops |
| `project_approval` | New project | Engineer → Head of Ops → Director |
| `bom_change` | BOM modifications | Engineer → QA |

## Migration Commands

```bash
# Install new dependencies
pip install -r requirements.txt

# Generate migration for new models
alembic revision --autogenerate -m "Add workflow, barcode, project, and audit models"

# Apply migrations
alembic upgrade head

# Create superuser with new roles
python scripts/create_superuser.py admin@company.com password "Admin" director
```

## Async Usage Example

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_async_db
from app.models import Material

async def get_materials(db: AsyncSession):
    result = await db.execute(select(Material).limit(10))
    return result.scalars().all()
```
