"""Inventory management endpoints."""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.inventory import Inventory, InventoryTransaction, InventoryStatus, TransactionType
from app.schemas.inventory import (
    InventoryCreate, InventoryUpdate, InventoryResponse,
    InventoryTransactionCreate, InventoryTransactionResponse
)
from app.schemas.common import PaginatedResponse
from app.api.dependencies import (
    get_current_user,
    require_technician,
    require_any_role,
    PaginationParams
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("", response_model=PaginatedResponse[InventoryResponse])
def list_inventory(
    pagination: PaginationParams = Depends(),
    material_id: Optional[int] = Query(None),
    status: Optional[InventoryStatus] = Query(None),
    location: Optional[str] = Query(None),
    lot_number: Optional[str] = Query(None),
    expired_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """
    List all inventory items with optional filtering.
    """
    query = db.query(Inventory)
    
    if material_id:
        query = query.filter(Inventory.material_id == material_id)
    if status:
        query = query.filter(Inventory.status == status)
    if location:
        query = query.filter(Inventory.location.ilike(f"%{location}%"))
    if lot_number:
        query = query.filter(Inventory.lot_number.ilike(f"%{lot_number}%"))
    if expired_only:
        query = query.filter(Inventory.expiration_date < date.today())
    
    total = query.count()
    items = query.offset(pagination.offset).limit(pagination.limit).all()
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages
    )


@router.get("/{inventory_id}", response_model=InventoryResponse)
def get_inventory(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get inventory item by ID."""
    inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    return inventory


@router.post("", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
def create_inventory(
    inventory_in: InventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Create a new inventory item (receive material)."""
    inventory = Inventory(**inventory_in.model_dump())
    db.add(inventory)
    db.commit()
    db.refresh(inventory)
    
    # Create receipt transaction
    transaction = InventoryTransaction(
        inventory_id=inventory.id,
        performed_by=current_user.id,
        transaction_type=TransactionType.RECEIPT,
        quantity=float(inventory.quantity),
        unit_of_measure=inventory.unit_of_measure,
        to_location=inventory.location,
        reason="Initial receipt"
    )
    db.add(transaction)
    db.commit()
    
    return inventory


@router.put("/{inventory_id}", response_model=InventoryResponse)
def update_inventory(
    inventory_id: int,
    inventory_in: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Update an inventory item."""
    inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    update_data = inventory_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(inventory, field, value)
    
    db.commit()
    db.refresh(inventory)
    return inventory


@router.post("/{inventory_id}/transactions", response_model=InventoryTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    inventory_id: int,
    transaction_in: InventoryTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """
    Create an inventory transaction (issue, transfer, adjustment, etc.).
    """
    inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    # Validate quantity for issue transactions
    if transaction_in.transaction_type == TransactionType.ISSUE:
        available = float(inventory.quantity) - float(inventory.reserved_quantity)
        if transaction_in.quantity > available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient quantity. Available: {available}"
            )
        inventory.quantity = float(inventory.quantity) - transaction_in.quantity
    
    elif transaction_in.transaction_type == TransactionType.RECEIPT:
        inventory.quantity = float(inventory.quantity) + transaction_in.quantity
    
    elif transaction_in.transaction_type == TransactionType.ADJUSTMENT:
        inventory.quantity = transaction_in.quantity
    
    elif transaction_in.transaction_type == TransactionType.TRANSFER:
        if transaction_in.to_location:
            inventory.location = transaction_in.to_location
    
    elif transaction_in.transaction_type == TransactionType.QUARANTINE:
        inventory.status = InventoryStatus.QUARANTINE
    
    elif transaction_in.transaction_type == TransactionType.RELEASE:
        inventory.status = InventoryStatus.AVAILABLE
    
    elif transaction_in.transaction_type == TransactionType.SCRAP:
        inventory.quantity = float(inventory.quantity) - transaction_in.quantity
        if inventory.quantity <= 0:
            inventory.status = InventoryStatus.CONSUMED
    
    transaction = InventoryTransaction(
        inventory_id=inventory_id,
        performed_by=current_user.id,
        **transaction_in.model_dump(exclude={"inventory_id"})
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return transaction


@router.get("/{inventory_id}/transactions", response_model=list[InventoryTransactionResponse])
def list_transactions(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """List all transactions for an inventory item."""
    inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    return inventory.transactions
