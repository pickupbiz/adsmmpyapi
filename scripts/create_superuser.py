"""Script to create a superuser for the application."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash


def create_superuser(
    email: str,
    password: str,
    full_name: str = "Administrator"
) -> None:
    """Create a superuser account."""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"User with email {email} already exists!")
            return
        
        # Create superuser
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=UserRole.ADMIN,
            is_active=True,
            is_superuser=True
        )
        
        db.add(user)
        db.commit()
        print(f"Superuser '{email}' created successfully!")
        
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_superuser.py <email> <password> [full_name]")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    full_name = sys.argv[3] if len(sys.argv) > 3 else "Administrator"
    
    create_superuser(email, password, full_name)
