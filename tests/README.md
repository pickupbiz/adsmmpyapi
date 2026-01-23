# Test Suite for Aerospace Parts Material Management API

This directory contains comprehensive tests for the Purchase Order (PO) integration and material management system.

## Test Structure

### Test Files

1. **`conftest.py`** - Shared fixtures and test configuration
2. **`test_purchase_order_workflow.py`** - PO creation and approval workflow tests
3. **`test_material_receipt.py`** - Material receipt against PO validation tests
4. **`test_po_status_transitions.py`** - PO status transition tests
5. **`test_material_traceability.py`** - Material traceability from PO to Finished Goods tests
6. **`test_po_role_based_access.py`** - Role-based access control tests for PO operations
7. **`test_po_dashboard.py`** - PO dashboard and reporting tests
8. **`test_po_integration.py`** - Integration tests for complete PO→Material flow

## Running Tests

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_purchase_order_workflow.py
```

### Run Specific Test Class

```bash
pytest tests/test_purchase_order_workflow.py::TestPOCreation
```

### Run Specific Test

```bash
pytest tests/test_purchase_order_workflow.py::TestPOCreation::test_create_po_as_purchase_user
```

### Run with Coverage

```bash
# Install coverage dependencies first
pip install -r requirements.txt

# Run tests with coverage (terminal output)
pytest --cov=app --cov-report=term-missing

# Run tests with coverage (HTML report)
pytest --cov=app --cov-report=html

# Run tests with coverage (all reports)
pytest --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml

# View HTML report (after running with --cov-report=html)
# Open htmlcov/index.html in your browser
```

**Coverage Configuration:**
- Coverage settings are in `.coveragerc`
- HTML reports are generated in `htmlcov/` directory
- XML reports are generated as `coverage.xml`
- Coverage includes branch coverage analysis

### Run with Verbose Output

```bash
pytest -v
```

## Test Coverage

### PO Creation and Approval Workflow
- ✅ PO creation by purchase users
- ✅ PO submission for approval
- ✅ PO approval by director/head of operations
- ✅ PO rejection workflow
- ✅ PO return for revision
- ✅ PO ordering workflow

### Material Receipt Validation
- ✅ GRN creation for ordered POs
- ✅ Quantity validation against ordered amounts
- ✅ GRN inspection by QA
- ✅ GRN acceptance to inventory
- ✅ Material instance creation from GRN

### PO Status Transitions
- ✅ Valid status transitions (draft → pending → approved → ordered → received)
- ✅ Invalid status transitions (prevented)
- ✅ Status history tracking

### Material Traceability
- ✅ Material instances linked to PO
- ✅ Trace material back to PO
- ✅ Complete lifecycle tracking (PO → Received → Inspection → Storage → Production → Finished)
- ✅ Barcode-based traceability

### Role-Based Access Control
- ✅ Purchase users can create POs
- ✅ Directors/Head Ops can approve POs
- ✅ Store users can create GRNs
- ✅ QA users can inspect GRNs
- ✅ Unauthorized access prevented

### Dashboard and Reporting
- ✅ PO summary and status breakdown
- ✅ Pending approvals list
- ✅ PO vs received comparison
- ✅ Supplier performance analytics
- ✅ Delivery analytics
- ✅ PO report export (PDF, Excel, CSV)
- ✅ Alert generation

### Integration Tests
- ✅ Complete PO→Material flow
- ✅ Partial receipt scenarios
- ✅ Material lifecycle from PO to production

## Test Fixtures

The `conftest.py` file provides the following fixtures:

- `db` - Database session for each test
- `client` - FastAPI test client
- `test_user` - Purchase user
- `test_director` - Director user
- `test_head_ops` - Head of Operations user
- `test_store_user` - Store user
- `test_qa_user` - QA user
- `test_supplier` - Test supplier
- `test_material` - Test material
- `test_purchase_order` - Test purchase order
- `test_po_with_line_items` - PO with line items
- `auth_headers` - Authentication headers for purchase user
- `director_headers` - Authentication headers for director
- `head_ops_headers` - Authentication headers for head of operations
- `store_headers` - Authentication headers for store user
- `qa_headers` - Authentication headers for QA user

## Notes

- Tests use an in-memory SQLite database for fast execution
- Each test gets a fresh database instance
- All tests are isolated and can run in any order
- Authentication is handled via JWT tokens in test fixtures
