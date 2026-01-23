"""Pytest configuration and shared fixtures."""
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole, Department
from app.models.supplier import Supplier, SupplierStatus, SupplierTier
from app.models.material import Material, MaterialType, MaterialStatus, MaterialCategory
from app.models.purchase_order import PurchaseOrder, POLineItem, POStatus, POPriority
from app.core.security import get_password_hash


# Test database URL (in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db_session = TestingSessionLocal()
    
    try:
        yield db_session
    finally:
        db_session.close()
        # Drop all tables
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        role=UserRole.PURCHASE,
        department=Department.PROCUREMENT,
        is_active=True,
        is_superuser=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_director(db: Session) -> User:
    """Create a test director user."""
    user = User(
        email="director@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test Director",
        role=UserRole.DIRECTOR,
        department=Department.ADMINISTRATION,
        is_active=True,
        is_superuser=True,
        can_approve_workflows=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_head_ops(db: Session) -> User:
    """Create a test head of operations user."""
    user = User(
        email="headops@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test Head Ops",
        role=UserRole.HEAD_OF_OPERATIONS,
        department=Department.OPERATIONS,
        is_active=True,
        is_superuser=False,
        can_approve_workflows=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_store_user(db: Session) -> User:
    """Create a test store user."""
    user = User(
        email="store@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test Store User",
        role=UserRole.STORE,
        department=Department.STORES,
        is_active=True,
        is_superuser=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_qa_user(db: Session) -> User:
    """Create a test QA user."""
    user = User(
        email="qa@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test QA User",
        role=UserRole.QA,
        department=Department.QUALITY_ASSURANCE,
        is_active=True,
        is_superuser=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_supplier(db: Session) -> Supplier:
    """Create a test supplier."""
    supplier = Supplier(
        name="Test Supplier Inc",
        code="SUP001",
        status=SupplierStatus.ACTIVE,
        tier=SupplierTier.TIER_1,
        contact_name="John Doe",
        contact_email="john@supplier.com",
        contact_phone="+1234567890",
        address_line_1="123 Supplier St",
        city="Supplier City",
        state="CA",
        country="USA",
        postal_code="12345"
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@pytest.fixture
def test_material_category(db: Session) -> MaterialCategory:
    """Create a test material category."""
    category = MaterialCategory(
        name="Test Category",
        code="CAT001",
        description="Test category for materials"
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture
def test_material(db: Session, test_material_category: MaterialCategory) -> Material:
    """Create a test material."""
    material = Material(
        item_number="MAT001",
        title="Test Material",
        specification="AMS 4911",
        material_type=MaterialType.RAW,
        category_id=test_material_category.id,
        status=MaterialStatus.ORDERED,  # Updated to match new enum
        quantity=100.0,
        unit_of_measure="kg",
        min_stock_level=10.0,
        max_stock_level=500.0,
        unit_cost=50.0
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@pytest.fixture
def auth_headers(client: TestClient, test_user: User) -> dict:
    """Get authentication headers for test user."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def director_headers(client: TestClient, test_director: User) -> dict:
    """Get authentication headers for director user."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_director.email,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def head_ops_headers(client: TestClient, test_head_ops: User) -> dict:
    """Get authentication headers for head of operations user."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_head_ops.email,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def store_headers(client: TestClient, test_store_user: User) -> dict:
    """Get authentication headers for store user."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_store_user.email,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def qa_headers(client: TestClient, test_qa_user: User) -> dict:
    """Get authentication headers for QA user."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_qa_user.email,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_purchase_order(
    db: Session,
    test_user: User,
    test_supplier: Supplier
) -> PurchaseOrder:
    """Create a test purchase order."""
    from datetime import date
    
    po = PurchaseOrder(
        po_number="PO-TEST-001",
        supplier_id=test_supplier.id,
        created_by_id=test_user.id,
        status=POStatus.DRAFT,
        priority=POPriority.NORMAL,
        po_date=date.today(),
        subtotal=1000.0,
        tax_amount=100.0,
        shipping_cost=50.0,
        total_amount=1150.0,
        currency="USD"
    )
    db.add(po)
    db.commit()
    db.refresh(po)
    return po


@pytest.fixture
def test_po_with_line_items(
    db: Session,
    test_purchase_order: PurchaseOrder,
    test_material: Material
) -> PurchaseOrder:
    """Create a purchase order with line items."""
    line_item = POLineItem(
        purchase_order_id=test_purchase_order.id,
        material_id=test_material.id,
        line_number=1,
        quantity_ordered=100.0,
        unit_of_measure="kg",
        unit_price=10.0,
        total_price=1000.0
    )
    db.add(line_item)
    db.commit()
    db.refresh(test_purchase_order)
    return test_purchase_order
