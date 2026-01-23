# Database Migration Guide - Material Schema Updates

**Date:** January 23, 2026  
**Version:** 2.0.0  
**Status:** ✅ Applied

---

## Overview

This guide documents the database schema changes made to the Materials table and related enums. These changes align the database schema with the updated Material model that supports Purchase Order (PO) integration and improved material lifecycle tracking.

---

## Migration Files Applied

The following migrations have been applied in order:

1. **`20260123_040000_rename_material_columns.py`**
   - Renames `part_number` → `item_number`
   - Renames `name` → `title`
   - Adds new columns for PO integration
   - Updates indexes

2. **`20260123_050000_replace_material_enum.py`**
   - Replaces `materialtype` enum: `METAL`, `COMPOSITE`, etc. → `raw`, `wip`, `finished`
   - Replaces `materialstatus` enum: `ACTIVE`, `DISCONTINUED`, etc. → `ordered`, `received`, `in_inspection`, etc.
   - Migrates existing data to new enum values

3. **`20260123_060000_fix_material_defaults.py`**
   - Sets default values for `min_stock_level`, `quantity`, `unit_of_measure`
   - Ensures all existing records have valid values

---

## Breaking Changes

### 1. Field Name Changes

| Old Field Name | New Field Name | Description |
|---------------|----------------|-------------|
| `name` | `title` | Material name/title |
| `part_number` | `item_number` | Material item number (unique identifier) |

**Impact:**
- All API requests/responses now use `title` instead of `name`
- All API requests/responses now use `item_number` instead of `part_number`
- Database queries must use new column names
- Custom scripts must be updated

### 2. MaterialType Enum Changes

**Old Values:**
- `METAL`, `COMPOSITE`, `POLYMER`, `CERAMIC`, `ALLOY`, `COATING`, `ADHESIVE`, `OTHER`

**New Values:**
- `raw` - Raw materials from suppliers
- `wip` - Work-in-progress materials
- `finished` - Finished goods/assemblies

**Migration Mapping:**
- All old values (`METAL`, `COMPOSITE`, `POLYMER`, etc.) → `raw`
- Existing `RAW` → `raw`
- Existing `WIP` → `wip`
- Existing `FINISHED` → `finished`

**Impact:**
- API requests must use lowercase values: `raw`, `wip`, `finished`
- Database queries must use new enum values
- Existing data has been automatically migrated

### 3. MaterialStatus Enum Changes

**Old Values:**
- `ACTIVE`, `DISCONTINUED`, `PENDING_APPROVAL`, `RESTRICTED`

**New Values:**
- `ordered` - Material ordered via PO
- `received` - Material received at warehouse
- `in_inspection` - Material under QA inspection
- `in_storage` - Material in storage
- `issued` - Material issued to production
- `in_production` - Material in production process
- `completed` - Material/assembly completed
- `rejected` - Material rejected by QA

**Migration Mapping:**
- `ACTIVE` → `in_storage`
- `DISCONTINUED` → `rejected`
- `PENDING_APPROVAL` → `ordered`
- `RESTRICTED` → `in_inspection`
- Existing new values are preserved

**Impact:**
- API requests must use new status values
- Status filters in queries must be updated
- Existing data has been automatically migrated

---

## New Fields Added

### PO Integration Fields

| Field Name | Type | Nullable | Description |
|-----------|------|----------|-------------|
| `po_id` | Integer | Yes | Reference to Purchase Order |
| `po_line_item_id` | Integer | Yes | Reference to PO Line Item |
| `supplier_id` | Integer | Yes | Supplier reference |
| `supplier_batch_number` | String(100) | Yes | Supplier's batch number |

### Traceability Fields

| Field Name | Type | Nullable | Description |
|-----------|------|----------|-------------|
| `heat_number` | String(100) | Yes | Heat number for traceability |
| `batch_number` | String(100) | Yes | Batch number for traceability |
| `quantity` | Numeric(14,4) | No | Current quantity (default: 0) |
| `min_stock_level` | Numeric(14,4) | No | Minimum stock level (default: 0) |
| `max_stock_level` | Numeric(14,4) | Yes | Maximum stock level |

### Storage Fields

| Field Name | Type | Nullable | Description |
|-----------|------|----------|-------------|
| `location` | String(200) | Yes | Storage location |
| `storage_bin` | String(100) | Yes | Storage bin number |

### Lifecycle Date Fields

| Field Name | Type | Nullable | Description |
|-----------|------|----------|-------------|
| `received_date` | DateTime | Yes | Date material was received |
| `inspection_date` | DateTime | Yes | Date of QA inspection |
| `issued_date` | DateTime | Yes | Date material was issued |
| `production_start_date` | DateTime | Yes | Date production started |
| `completion_date` | DateTime | Yes | Date material/assembly completed |

### Quality Assurance Fields

| Field Name | Type | Nullable | Description |
|-----------|------|----------|-------------|
| `qa_status` | String(50) | Yes | QA status (Pass, Fail, Hold) |
| `qa_inspected_by` | Integer | Yes | User ID of QA inspector |
| `certificate_number` | String(100) | Yes | Certificate/MTR number |

### Barcode Field

| Field Name | Type | Nullable | Description |
|-----------|------|----------|-------------|
| `barcode_id` | Integer | Yes | Reference to barcode label |

---

## Migration Steps for Team Members

### Step 1: Backup Database

```bash
# PostgreSQL backup
pg_dump -U your_user -d your_database > backup_before_migration.sql
```

### Step 2: Run Migrations

```bash
# Navigate to project directory
cd /path/to/adsmmpyapi

# Activate virtual environment (if using one)
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Run migrations
alembic upgrade head
```

### Step 3: Verify Migration

```bash
# Check current migration version
alembic current

# Should show: c2d3e4f5a6b7 (head)
```

### Step 4: Verify Data

```sql
-- Check enum values
SELECT enumlabel FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'materialtype')
ORDER BY enumsortorder;

-- Should return: raw, wip, finished

SELECT enumlabel FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'materialstatus')
ORDER BY enumsortorder;

-- Should return: ordered, received, in_inspection, in_storage, issued, in_production, completed, rejected

-- Check column names
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'materials' 
AND column_name IN ('item_number', 'title', 'part_number', 'name');

-- Should return: item_number, title (not part_number or name)

-- Check for NULL values in required fields
SELECT COUNT(*) FROM materials 
WHERE min_stock_level IS NULL OR quantity IS NULL OR unit_of_measure IS NULL;

-- Should return: 0
```

### Step 5: Update Application Code

1. **Update API Client Code:**
   - Replace `part_number` with `item_number`
   - Replace `name` with `title`
   - Update enum values in requests

2. **Update Database Queries:**
   - Update column names in SQL queries
   - Update enum values in WHERE clauses

3. **Update Tests:**
   - Update test fixtures to use new field names
   - Update test assertions for new enum values

---

## API Request/Response Examples

### Before (Old Schema)

```json
{
  "name": "Titanium Alloy",
  "part_number": "MAT-001",
  "material_type": "alloy",
  "status": "active"
}
```

### After (New Schema)

```json
{
  "item_number": "MAT-001",
  "title": "Titanium Alloy",
  "material_type": "raw",
  "status": "ordered",
  "quantity": 100.0,
  "unit_of_measure": "kg",
  "min_stock_level": 10.0,
  "po_id": 1,
  "po_line_item_id": 1
}
```

---

## Rollback Instructions

If you need to rollback the migrations:

```bash
# Rollback to previous version
alembic downgrade -1

# Or rollback to specific revision
alembic downgrade a0b1c2d3e4f5
```

**⚠️ Warning:** Rolling back will:
- Revert enum values to old ones
- Revert column names to old ones
- May cause data loss if new fields had data

---

## Common Issues and Solutions

### Issue 1: "column materials.item_number does not exist"

**Solution:** Run migrations:
```bash
alembic upgrade head
```

### Issue 2: "'OTHER' is not among the defined enum values"

**Solution:** The enum has been replaced. Use `raw`, `wip`, or `finished` instead.

### Issue 3: "min_stock_level is None" validation error

**Solution:** Migration should have set defaults. If still occurring:
```sql
UPDATE materials SET min_stock_level = 0 WHERE min_stock_level IS NULL;
UPDATE materials SET quantity = 0 WHERE quantity IS NULL;
UPDATE materials SET unit_of_measure = 'units' WHERE unit_of_measure IS NULL OR unit_of_measure = '';
```

### Issue 4: API returns old field names

**Solution:** Clear API cache and restart the server. Ensure you're using the latest code.

---

## Testing Checklist

After migration, verify:

- [ ] Materials can be listed via API
- [ ] Materials can be created with new field names
- [ ] Materials can be updated
- [ ] Enum values work correctly (`raw`, `wip`, `finished`)
- [ ] Status values work correctly (`ordered`, `received`, etc.)
- [ ] Search by `item_number` and `title` works
- [ ] PO integration fields are accessible
- [ ] No NULL values in required fields

---

## Support

If you encounter issues:

1. Check migration status: `alembic current`
2. Check migration history: `alembic history`
3. Review migration logs
4. Contact the development team

---

## Related Documentation

- [API_EXAMPLES.md](./API_EXAMPLES.md) - Updated API examples
- [README.md](./README.md) - Project overview
- [tests/README.md](./tests/README.md) - Test documentation
