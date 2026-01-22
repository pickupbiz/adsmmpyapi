"""Script to create a superuser for the application."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.user import User, UserRole, Department
from app.core.security import get_password_hash


def create_superuser(
    email: str,
    password: str,
    full_name: str = "Administrator",
    role: str = "director"
) -> None:
    """Create a superuser account."""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"User with email {email} already exists!")
            return
        
        # Map role string to enum
        role_map = {
            "director": UserRole.DIRECTOR,
            "head_of_operations": UserRole.HEAD_OF_OPERATIONS,
            "store": UserRole.STORE,
            "purchase": UserRole.PURCHASE,
            "qa": UserRole.QA,
            "engineer": UserRole.ENGINEER,
            "technician": UserRole.TECHNICIAN,
            "viewer": UserRole.VIEWER,
        }
        user_role = role_map.get(role.lower(), UserRole.DIRECTOR)
        
        # Create superuser
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=user_role,
            department=Department.ADMINISTRATION,
            is_active=True,
            is_superuser=True,
            can_approve_workflows=True
        )
        
        db.add(user)
        db.commit()
        print(f"Superuser '{email}' created successfully with role '{user_role.value}'!")
        
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_superuser.py <email> <password> [full_name] [role]")
        print("Roles: director, head_of_operations, store, purchase, qa, engineer, technician, viewer")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    full_name = sys.argv[3] if len(sys.argv) > 3 else "Administrator"
    role = sys.argv[4] if len(sys.argv) > 4 else "director"
    
    create_superuser(email, password, full_name, role)
