# Database Migration Notes

This document tracks important database schema changes and migration instructions for the team.

---

## 2026-01-22: User Role Enum Updates

### Changes Made

1. **New User Roles Added**
   - `director` - Full system access, final approvals
   - `head_of_operations` - Operations oversight
   - `store` - Inventory management
   - `purchase` - Procurement and orders
   - `qa` - Quality assurance
   - `engineer` - Technical specifications (existing)
   - `technician` - Floor operations (existing)
   - `viewer` - Read-only access (existing)
   - `admin` - Legacy role (mapped to director privileges)

2. **Case Sensitivity Fix**
   - Fixed issue where uppercase enum values (e.g., `ADMIN`) caused errors
   - All role values are now lowercase in the database

### Migration Instructions

**For Developers:**

1. Pull the latest code
2. Activate your virtual environment:
   ```bash
   # Windows
   .\venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. Run migrations:
   ```bash
   alembic upgrade head
   ```

4. If you encounter any errors, check:
   - Database connection in `.env` or `app/core/config.py`
   - PostgreSQL service is running

### Role Mapping

| Old Role | New Role | Permissions |
|----------|----------|-------------|
| `ADMIN` | `director` | Full system access |
| `admin` | `admin` (legacy) | Same as director |
| `manager` | `head_of_operations` | Operations + view |
| - | `store` | Material movements, inventory |
| - | `purchase` | Purchase orders, supplier management |
| - | `qa` | Quality checks, approvals |

### Troubleshooting

**Error: `'ADMIN' is not among the defined enum values`**

This means you have existing user data with uppercase role values. The migration `20260122_220000_fix_userrole_case_sensitivity.py` should fix this automatically. If not:

```sql
-- Run this in PostgreSQL to check affected users
SELECT id, email, role::text FROM users WHERE role::text = UPPER(role::text);

-- Manually fix if needed (run in psql)
ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(50) USING role::text;
UPDATE users SET role = LOWER(role);
ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole;
```

**Error: `enum value already exists`**

This is safe to ignore. The migration uses `IF NOT EXISTS` to handle this.

---

## Best Practices

1. **Always run migrations** after pulling new code
2. **Never modify** existing migration files that have been committed
3. **Create new migrations** for schema changes
4. **Test migrations** on a local database before deploying

---

## Migration Commands Cheat Sheet

```bash
# Apply all pending migrations
alembic upgrade head

# Check current migration version
alembic current

# View migration history
alembic history

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Rollback last migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```
