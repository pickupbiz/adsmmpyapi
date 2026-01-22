"""API dependencies for authentication and authorization."""
from typing import Generator, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
)


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    if payload.get("type") != "access":
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user


class RoleChecker:
    """Dependency class for role-based access control."""
    
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser:
            return current_user
        
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.value}' is not authorized for this action"
            )
        return current_user


# Pre-configured role checkers
require_admin = RoleChecker([UserRole.ADMIN])
require_manager = RoleChecker([UserRole.ADMIN, UserRole.MANAGER])
require_engineer = RoleChecker([UserRole.ADMIN, UserRole.MANAGER, UserRole.ENGINEER])
require_technician = RoleChecker([UserRole.ADMIN, UserRole.MANAGER, UserRole.ENGINEER, UserRole.TECHNICIAN])
require_any_role = RoleChecker([UserRole.ADMIN, UserRole.MANAGER, UserRole.ENGINEER, UserRole.TECHNICIAN, UserRole.VIEWER])


# Pagination dependency
class PaginationParams:
    """Pagination parameters dependency."""
    
    def __init__(
        self,
        page: int = 1,
        page_size: int = settings.DEFAULT_PAGE_SIZE
    ):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), settings.MAX_PAGE_SIZE)
        self.offset = (self.page - 1) * self.page_size
        self.limit = self.page_size
