"""User CRUD operations."""
from typing import Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD operations for User model."""
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()
    
    def get_by_employee_id(self, db: Session, *, employee_id: str) -> Optional[User]:
        """Get user by employee ID."""
        return db.query(User).filter(User.employee_id == employee_id).first()
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """Create a new user with hashed password."""
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            employee_id=obj_in.employee_id,
            department=obj_in.department,
            role=obj_in.role,
            is_active=obj_in.is_active,
            is_superuser=obj_in.is_superuser,
            notes=obj_in.notes
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, *, db_obj: User, obj_in: UserUpdate) -> User:
        """Update user, handling password hashing if needed."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


crud_user = CRUDUser(User)
