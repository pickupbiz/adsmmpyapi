# Team Update Notice - Material Schema Changes

**Date:** January 23, 2026  
**Priority:** 🔴 HIGH - Breaking Changes

---

## ⚠️ ACTION REQUIRED

All team members must update their code and run database migrations before using the updated API.

---

## Quick Start for Team Members

### Step 1: Pull Latest Code
```bash
git pull origin main
```

### Step 2: Run Database Migrations
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Run migrations
alembic upgrade head
```

### Step 3: Update Your Code

**Replace in all files:**
- `part_number` → `item_number`
- `name` (material) → `title`
- Material type: `metal`, `composite`, etc. → `raw`, `wip`, `finished`
- Material status: `active`, `discontinued`, etc. → `ordered`, `received`, `in_inspection`, etc.

### Step 4: Test Your Changes
```bash
pytest tests/ -v
```

---

## What Changed?

### Field Names
- ❌ `materials.name` → ✅ `materials.title`
- ❌ `materials.part_number` → ✅ `materials.item_number`

### Enum Values
- ❌ MaterialType: `metal`, `composite`, `polymer`, etc.
- ✅ MaterialType: `raw`, `wip`, `finished`

- ❌ MaterialStatus: `active`, `discontinued`, `pending_approval`, `restricted`
- ✅ MaterialStatus: `ordered`, `received`, `in_inspection`, `in_storage`, `issued`, `in_production`, `completed`, `rejected`

### New Required Fields
- `quantity` (default: 0)
- `min_stock_level` (default: 0)
- `unit_of_measure` (default: "units")

---

## Example Updates

### API Request - Before
```json
{
  "name": "Titanium Alloy",
  "part_number": "MAT-001",
  "material_type": "alloy",
  "status": "active"
}
```

### API Request - After
```json
{
  "item_number": "MAT-001",
  "title": "Titanium Alloy",
  "quantity": 100.0,
  "unit_of_measure": "kg",
  "min_stock_level": 10.0,
  "material_type": "raw",
  "status": "ordered"
}
```

---

## Documentation

- **Migration Guide:** [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)
- **API Examples:** [API_EXAMPLES.md](./API_EXAMPLES.md) (updated)
- **Changelog:** [CHANGELOG.md](./CHANGELOG.md)

---

## Need Help?

1. Check migration status: `alembic current`
2. Review [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)
3. Contact the development team

---

## Verification Checklist

After updating, verify:

- [ ] Migrations ran successfully (`alembic current` shows latest version)
- [ ] API endpoints work with new field names
- [ ] Enum values are correct
- [ ] No NULL values in required fields
- [ ] Tests pass
- [ ] Your custom scripts updated

---

**Last Updated:** January 23, 2026
