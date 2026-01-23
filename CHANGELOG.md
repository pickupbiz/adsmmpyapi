# Changelog - Material Schema Updates

**Version:** 2.0.0  
**Date:** January 23, 2026

---

## Summary

This update introduces significant changes to the Material model and database schema to support Purchase Order (PO) integration and improved material lifecycle tracking. All changes are backward-compatible through database migrations.

---

## Breaking Changes

### 1. Field Name Changes

| Old Field | New Field | Type | Required |
|-----------|-----------|------|----------|
| `name` | `title` | String(200) | Yes |
| `part_number` | `item_number` | String(100) | Yes (unique) |

**Action Required:**
- Update all API requests/responses to use new field names
- Update database queries
- Update test fixtures
- Update documentation references

### 2. MaterialType Enum

**Old Values (REMOVED):**
- `METAL`, `COMPOSITE`, `POLYMER`, `CERAMIC`, `ALLOY`, `COATING`, `ADHESIVE`, `OTHER`

**New Values:**
- `raw` - Raw materials from suppliers
- `wip` - Work-in-progress materials  
- `finished` - Finished goods/assemblies

**Migration:**
- All old values automatically mapped to `raw`
- Existing `RAW` → `raw`
- Existing `WIP` → `wip`
- Existing `FINISHED` → `finished`

**Action Required:**
- Update API requests to use: `raw`, `wip`, or `finished`
- Update filters and queries

### 3. MaterialStatus Enum

**Old Values (REMOVED):**
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

**Migration:**
- `ACTIVE` → `in_storage`
- `DISCONTINUED` → `rejected`
- `PENDING_APPROVAL` → `ordered`
- `RESTRICTED` → `in_inspection`

**Action Required:**
- Update API requests to use new status values
- Update status filters in queries
- Review migrated data for accuracy

---

## New Features

### PO Integration Fields

Materials can now be linked to Purchase Orders:

- `po_id` - Reference to Purchase Order
- `po_line_item_id` - Reference to PO Line Item
- `supplier_id` - Supplier reference
- `supplier_batch_number` - Supplier's batch number

### Traceability Fields

Enhanced traceability with:

- `heat_number` - Heat number for material traceability
- `batch_number` - Batch number for material traceability
- `quantity` - Current quantity (required, default: 0)
- `min_stock_level` - Minimum stock level (required, default: 0)
- `max_stock_level` - Maximum stock level (optional)

### Storage Management

- `location` - Storage location (e.g., "Warehouse A")
- `storage_bin` - Storage bin number (e.g., "A-12-34")

### Lifecycle Tracking

Date fields for material lifecycle:

- `received_date` - When material was received
- `inspection_date` - When QA inspection occurred
- `issued_date` - When material was issued to production
- `production_start_date` - When production started
- `completion_date` - When material/assembly was completed

### Quality Assurance

- `qa_status` - QA status (Pass, Fail, Hold)
- `qa_inspected_by` - User ID of QA inspector
- `certificate_number` - Certificate/MTR number

### Barcode Integration

- `barcode_id` - Reference to barcode label for scanning

---

## Migration Steps

### For New Installations

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run all migrations
alembic upgrade head

# 3. Verify
alembic current
# Should show: c2d3e4f5a6b7
```

### For Existing Installations

```bash
# 1. Backup database
pg_dump -U user -d database > backup.sql

# 2. Run migrations
alembic upgrade head

# 3. Verify data
# Check that enum values are correct
# Check that field names are updated
# Check that defaults are set
```

See [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for detailed instructions.

---

## API Examples

### Create Material (New Schema)

```json
{
  "item_number": "MAT-001",
  "title": "Titanium Alloy Ti-6Al-4V",
  "specification": "AMS 4911",
  "quantity": 100.0,
  "unit_of_measure": "kg",
  "min_stock_level": 10.0,
  "material_type": "raw",
  "status": "ordered",
  "po_id": 1,
  "po_line_item_id": 1
}
```

### List Materials (Updated Response)

```json
{
  "items": [
    {
      "id": 1,
      "item_number": "MAT-001",
      "title": "Titanium Alloy",
      "material_type": "raw",
      "status": "ordered",
      "quantity": 100.0,
      "min_stock_level": 10.0,
      "po_id": 1
    }
  ]
}
```

---

## Testing

All tests have been updated to use new field names and enum values. Run:

```bash
pytest tests/ -v
```

---

## Rollback

If needed, rollback to previous version:

```bash
alembic downgrade -1
```

**⚠️ Warning:** Rollback will revert all changes and may cause data loss.

---

## Support

For questions or issues:
1. Check [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)
2. Review [API_EXAMPLES.md](./API_EXAMPLES.md)
3. Contact the development team

---

## Files Modified

- `app/models/material.py` - Updated model with new fields and enums
- `app/schemas/material.py` - Updated schemas with new field names
- `app/api/endpoints/materials.py` - Updated endpoints for new fields
- `alembic/versions/20260123_040000_rename_material_columns.py` - Column rename migration
- `alembic/versions/20260123_050000_replace_material_enum.py` - Enum replacement migration
- `alembic/versions/20260123_060000_fix_material_defaults.py` - Default values migration
- `tests/` - All test files updated
- `API_EXAMPLES.md` - Updated examples
- `MIGRATION_GUIDE.md` - New migration guide
- `CHANGELOG.md` - This file
