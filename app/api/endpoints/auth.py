"""Authentication endpoints with JWT-based authentication and session management."""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.db.session import get_db
from app.models.user import User, UserRole, Department
from app.models.audit import LoginHistory
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    Token,
    TokenPayload
)
from app.api.dependencies import get_current_user, get_current_superuser, require_director

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def log_login_attempt(
    db: Session,
    user_id: Optional[int],
    ip_address: str,
    user_agent: str,
    success: bool,
    failure_reason: Optional[str] = None
) -> None:
    """Log login attempt to database for security auditing."""
    if user_id is None:
        return  # Can't log without user_id due to FK constraint
    try:
        login_record = LoginHistory(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            is_successful=success,
            failure_reason=failure_reason
        )
        db.add(login_record)
        db.commit()
    except Exception:
        db.rollback()  # Don't fail login if logging fails


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    
    ## Authentication Flow
    1. Validate email and password
    2. Check if user account is active
    3. Generate access token (short-lived) and refresh token (long-lived)
    4. Log the login attempt for security auditing
    
    ## Request
    - **username**: User's email address
    - **password**: User's password
    
    ## Response
    Returns JWT access token and refresh token for session management.
    
    ## Role-Based Access
    After login, the token contains the user's role which determines API access:
    - **Director**: Full system access
    - **Head of Operations**: Operations oversight + view access
    - **Store**: Material movements, inventory management
    - **Purchase**: Purchase orders, supplier management
    - **QA**: Quality checks, approvals
    - **Engineer**: Technical specifications
    - **Technician**: Floor operations
    - **Viewer**: Read-only access
    """
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user:
        log_login_attempt(db, None, ip_address, user_agent, False, "User not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        log_login_attempt(db, user.id, ip_address, user_agent, False, "Invalid password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        log_login_attempt(db, user.id, ip_address, user_agent, False, "Account inactive")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Log successful login
    log_login_attempt(db, user.id, ip_address, user_agent, True)
    
    # Create tokens with role information
    access_token = create_access_token(
        subject=user.id,
        role=user.role.value
    )
    refresh_token = create_refresh_token(subject=user.id)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    """
    payload = decode_token(refresh_token)
    
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    new_access_token = create_access_token(
        subject=user.id,
        role=user.role.value
    )
    new_refresh_token = create_refresh_token(subject=user.id)
    
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    Register a new user (superuser only).
    
    Only superusers can create new user accounts.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if user_in.employee_id:
        existing_employee = db.query(User).filter(
            User.employee_id == user_in.employee_id
        ).first()
        if existing_employee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee ID already exists"
            )
    
    # Create new user
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        employee_id=user_in.employee_id,
        department=user_in.department,
        role=user_in.role,
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser,
        notes=user_in.notes
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return current_user


@router.post("/change-password")
def change_password(
    current_password: str,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Change current user's password.
    
    - **current_password**: Current password for verification
    - **new_password**: New password (minimum 8 characters)
    """
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters"
        )
    
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Logout current user.
    
    Note: Since JWT tokens are stateless, this endpoint primarily logs the 
    logout action. Client should discard tokens after calling this endpoint.
    
    For true session invalidation, implement a token blacklist in Redis.
    """
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    
    # Log logout (using login_history with a special marker)
    try:
        logout_record = LoginHistory(
            user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            success=True,
            failure_reason="LOGOUT"  # Mark as logout event
        )
        db.add(logout_record)
        db.commit()
    except Exception:
        db.rollback()
    
    return {"message": "Successfully logged out"}


@router.get("/validate")
def validate_token(
    current_user: User = Depends(get_current_user)
):
    """
    Validate current JWT token.
    
    Returns user info if token is valid, 401 if invalid.
    Use this endpoint to check if a session is still active.
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role.value,
        "is_superuser": current_user.is_superuser
    }


@router.get("/permissions")
def get_user_permissions(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's role-based permissions.
    
    Returns the list of actions the user is authorized to perform
    based on their role.
    """
    # Define permissions for each role
    role_permissions = {
        UserRole.DIRECTOR: {
            "description": "Full system access - can perform all operations",
            "permissions": [
                "manage_users", "manage_materials", "manage_parts",
                "manage_suppliers", "manage_inventory", "manage_orders",
                "manage_certifications", "approve_workflows", "view_reports",
                "manage_projects", "manage_bom", "manage_qa",
                "view_audit_logs", "system_settings"
            ]
        },
        UserRole.HEAD_OF_OPERATIONS: {
            "description": "Operations oversight with view and approval capabilities",
            "permissions": [
                "view_materials", "view_parts", "view_suppliers",
                "view_inventory", "manage_orders", "view_certifications",
                "approve_workflows", "view_reports", "manage_projects",
                "view_audit_logs"
            ]
        },
        UserRole.STORE: {
            "description": "Material movements and inventory management",
            "permissions": [
                "view_materials", "view_parts", "manage_inventory",
                "receive_materials", "issue_materials", "stocktake",
                "view_orders", "manage_barcodes"
            ]
        },
        UserRole.PURCHASE: {
            "description": "Purchase orders and supplier management",
            "permissions": [
                "view_materials", "view_parts", "manage_suppliers",
                "manage_orders", "view_inventory", "create_requisitions",
                "view_certifications"
            ]
        },
        UserRole.QA: {
            "description": "Quality assurance checks and approvals",
            "permissions": [
                "view_materials", "view_parts", "manage_certifications",
                "quality_checks", "approve_materials", "reject_materials",
                "view_inventory", "view_suppliers", "manage_qa_workflows"
            ]
        },
        UserRole.ENGINEER: {
            "description": "Technical specifications and part management",
            "permissions": [
                "manage_materials", "manage_parts", "view_suppliers",
                "view_inventory", "manage_bom", "view_certifications",
                "technical_approvals"
            ]
        },
        UserRole.TECHNICIAN: {
            "description": "Floor operations and basic inventory tasks",
            "permissions": [
                "view_materials", "view_parts", "view_inventory",
                "record_usage", "scan_barcodes", "view_work_orders"
            ]
        },
        UserRole.VIEWER: {
            "description": "Read-only access to system data",
            "permissions": [
                "view_materials", "view_parts", "view_suppliers",
                "view_inventory", "view_orders", "view_certifications",
                "view_reports"
            ]
        }
    }
    
    user_role_info = role_permissions.get(current_user.role, {
        "description": "Unknown role",
        "permissions": []
    })
    
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role.value,
        "role_description": user_role_info["description"],
        "is_superuser": current_user.is_superuser,
        "can_approve_workflows": current_user.can_approve_workflows,
        "approval_limit": current_user.approval_limit,
        "permissions": user_role_info["permissions"] if not current_user.is_superuser else ["ALL"]
    }


@router.get("/login-history")
def get_login_history(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get login history for current user.
    
    Returns recent login attempts for security review.
    """
    history = db.query(LoginHistory).filter(
        LoginHistory.user_id == current_user.id
    ).order_by(LoginHistory.login_at.desc()).limit(limit).all()
    
    return {
        "user_id": current_user.id,
        "login_history": [
            {
                "login_at": record.login_at.isoformat() if record.login_at else None,
                "ip_address": record.ip_address,
                "user_agent": record.user_agent,
                "success": record.is_successful,
                "failure_reason": record.failure_reason if record.failure_reason != "LOGOUT" else None,
                "is_logout": record.failure_reason == "LOGOUT"
            }
            for record in history
        ]
    }


@router.get("/all-login-history")
def get_all_login_history(
    user_id: Optional[int] = None,
    success_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_director)
):
    """
    Get login history for all users (Director only).
    
    Security audit endpoint for reviewing login activity across the system.
    """
    query = db.query(LoginHistory)
    
    if user_id:
        query = query.filter(LoginHistory.user_id == user_id)
    
    if success_only:
        query = query.filter(LoginHistory.is_successful == True)
    
    history = query.order_by(LoginHistory.login_at.desc()).limit(limit).all()
    
    return {
        "total_records": len(history),
        "login_history": [
            {
                "user_id": record.user_id,
                "login_at": record.login_at.isoformat() if record.login_at else None,
                "ip_address": record.ip_address,
                "user_agent": record.user_agent,
                "success": record.is_successful,
                "failure_reason": record.failure_reason if record.failure_reason != "LOGOUT" else None,
                "is_logout": record.failure_reason == "LOGOUT"
            }
            for record in history
        ]
    }
