"""Script to fix user roles with uppercase enum values."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import sync_engine

def fix_user_roles():
    """Fix users with uppercase ADMIN role to lowercase admin or director."""
    with sync_engine.connect() as conn:
        # Check for affected users
        result = conn.execute(text("SELECT id, email, role::text as role FROM users WHERE role::text = 'ADMIN'"))
        affected_users = result.fetchall()
        
        if not affected_users:
            print("No users with uppercase 'ADMIN' role found.")
            return
        
        print(f"Found {len(affected_users)} user(s) with uppercase 'ADMIN' role:")
        for user in affected_users:
            print(f"  - ID: {user[0]}, Email: {user[1]}, Role: {user[2]}")
        
        # Update to 'director' (the new equivalent of admin)
        conn.execute(text("UPDATE users SET role = 'director' WHERE role::text = 'ADMIN'"))
        conn.commit()
        
        print(f"\nUpdated {len(affected_users)} user(s) to 'director' role.")

if __name__ == "__main__":
    fix_user_roles()
