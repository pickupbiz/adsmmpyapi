# Test Fixes Applied

## Summary of Fixes

### 1. Endpoint Path Corrections

**Fixed:**
- `/purchase-orders/{po_id}/mark-ordered` → `/purchase-orders/{po_id}/order`
- `/purchase-orders/grn` → `/purchase-orders/{po_id}/receive`
- `/purchase-orders/{po_id}/reject` → `/purchase-orders/{po_id}/approve` (with action="rejected")
- `/purchase-orders/{po_id}/return` → `/purchase-orders/{po_id}/approve` (with action="returned")
- `/dashboard/purchase-orders/summary` → `/dashboard/po-summary`
- `/dashboard/purchase-orders/status-breakdown` → `/dashboard/po-summary`
- `/dashboard/purchase-orders/pending-approvals` → `/dashboard/po-summary`
- `/dashboard/purchase-orders/po-vs-received` → `/dashboard/po-vs-received`
- `/dashboard/purchase-orders/delivery-analytics` → `/dashboard/delivery-analytics`
- `/reports/purchase-orders/{po_id}` → `/reports/po` (POST with request body)

### 2. Approval Request Format

**Fixed:**
- Changed from separate approve/reject/return endpoints to single `/approve` endpoint
- Now uses `POApprovalRequest` schema with `action` field:
  - `{"action": "approved", "comments": "..."}`
  - `{"action": "rejected", "comments": "..."}`
  - `{"action": "returned", "comments": "..."}`

### 3. GRN Inspection Format

**Fixed:**
- Changed from JSON body with `inspection_status` and `line_items` to:
  - Query parameter: `inspection_passed: bool`
  - JSON body: `{"inspection_notes": "..."}`
- Example: `POST /purchase-orders/grn/{grn_id}/inspect?inspection_passed=true`

### 4. MaterialStatus Enum

**Fixed:**
- Changed `MaterialStatus.ACTIVE` → `MaterialStatus.ORDERED` (to match new enum values)

### 5. GRN Status Expectations

**Fixed:**
- GRN is created in `DRAFT` status, not `PENDING_INSPECTION`
- Updated assertions to check for `["draft", "pending_inspection"]` or appropriate status

### 6. Report Generation Format

**Fixed:**
- Changed from GET with query params to POST with request body
- Format: `POST /reports/po` with JSON body containing `po_ids`, `format`, `date_range`

## Common Issues to Watch For

1. **Database Relationships**: Some tests create objects directly in DB - ensure all foreign keys are valid
2. **Status Transitions**: GRN must be inspected before acceptance
3. **Authentication**: All endpoints require valid JWT tokens
4. **Role Permissions**: Some operations require specific roles (Director, Head Ops, Store, QA)

## Running Tests After Fixes

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_purchase_order_workflow.py -v

# Run with output
pytest -v -s

# Run with coverage
pytest --cov=app --cov-report=term-missing
```

## Known Test Limitations

1. **SQLite vs PostgreSQL**: Tests use SQLite in-memory DB, which may behave differently than PostgreSQL for:
   - Enum handling
   - Foreign key constraints
   - Date/time functions

2. **Async Operations**: Some endpoints may be async but tests use sync TestClient

3. **File Generation**: Report generation tests may need actual file system access
