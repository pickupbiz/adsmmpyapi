"""Order management endpoints."""
from typing import Optional
from datetime import date
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.order import Order, OrderItem, OrderStatus, OrderPriority
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse,
    OrderItemCreate, OrderItemUpdate, OrderItemResponse
)
from app.schemas.common import PaginatedResponse
from app.api.dependencies import (
    get_current_user,
    require_manager,
    require_technician,
    require_any_role,
    PaginationParams
)

router = APIRouter(prefix="/orders", tags=["Orders"])


def generate_order_number() -> str:
    """Generate a unique order number."""
    return f"PO-{date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


@router.get("", response_model=PaginatedResponse[OrderResponse])
def list_orders(
    pagination: PaginationParams = Depends(),
    status: Optional[OrderStatus] = Query(None),
    priority: Optional[OrderPriority] = Query(None),
    supplier_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """
    List all orders with optional filtering.
    """
    query = db.query(Order)
    
    if status:
        query = query.filter(Order.status == status)
    if priority:
        query = query.filter(Order.priority == priority)
    if supplier_id:
        query = query.filter(Order.supplier_id == supplier_id)
    
    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(pagination.offset).limit(pagination.limit).all()
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return PaginatedResponse(
        items=orders,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages
    )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get order by ID."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Create a new order."""
    order_data = order_in.model_dump(exclude={"items"})
    order = Order(
        **order_data,
        order_number=generate_order_number(),
        created_by=current_user.id
    )
    db.add(order)
    db.flush()  # Get the order ID
    
    # Add order items
    for item_in in order_in.items:
        total_price = float(item_in.quantity_ordered) * float(item_in.unit_price)
        item = OrderItem(
            order_id=order.id,
            total_price=total_price,
            **item_in.model_dump()
        )
        db.add(item)
    
    db.commit()
    db.refresh(order)
    
    # Calculate totals
    order.calculate_totals()
    db.commit()
    
    return order


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_in: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Update an order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Cannot update cancelled or received orders
    if order.status in [OrderStatus.CANCELLED, OrderStatus.RECEIVED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update order with status: {order.status.value}"
        )
    
    update_data = order_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    order.calculate_totals()
    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Delete an order (only draft orders)."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status != OrderStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft orders can be deleted"
        )
    
    db.delete(order)
    db.commit()


@router.post("/{order_id}/submit", response_model=OrderResponse)
def submit_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Submit an order for approval."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status != OrderStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft orders can be submitted"
        )
    
    if not order.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit order without items"
        )
    
    order.status = OrderStatus.PENDING_APPROVAL
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/approve", response_model=OrderResponse)
def approve_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Approve an order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status != OrderStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending orders can be approved"
        )
    
    order.status = OrderStatus.APPROVED
    order.order_date = date.today()
    db.commit()
    db.refresh(order)
    return order


# Order Items endpoints
@router.post("/{order_id}/items", response_model=OrderItemResponse, status_code=status.HTTP_201_CREATED)
def add_order_item(
    order_id: int,
    item_in: OrderItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Add an item to an order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status not in [OrderStatus.DRAFT, OrderStatus.PENDING_APPROVAL]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add items to this order"
        )
    
    total_price = float(item_in.quantity_ordered) * float(item_in.unit_price)
    item = OrderItem(
        order_id=order_id,
        total_price=total_price,
        **item_in.model_dump()
    )
    db.add(item)
    db.commit()
    
    order.calculate_totals()
    db.commit()
    db.refresh(item)
    
    return item


@router.put("/{order_id}/items/{item_id}", response_model=OrderItemResponse)
def update_order_item(
    order_id: int,
    item_id: int,
    item_in: OrderItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Update an order item."""
    item = db.query(OrderItem).filter(
        OrderItem.id == item_id,
        OrderItem.order_id == order_id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order item not found"
        )
    
    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    # Recalculate total price
    item.total_price = float(item.quantity_ordered) * float(item.unit_price)
    
    db.commit()
    
    # Recalculate order totals
    item.order.calculate_totals()
    db.commit()
    db.refresh(item)
    
    return item


@router.delete("/{order_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order_item(
    order_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Remove an item from an order."""
    item = db.query(OrderItem).filter(
        OrderItem.id == item_id,
        OrderItem.order_id == order_id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order item not found"
        )
    
    order = item.order
    if order.status not in [OrderStatus.DRAFT, OrderStatus.PENDING_APPROVAL]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove items from this order"
        )
    
    db.delete(item)
    db.commit()
    
    # Recalculate order totals
    order.calculate_totals()
    db.commit()
