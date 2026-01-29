"""
WebSocket endpoint for real-time updates.

Provides:
- Real-time PO status updates
- Material status changes
- Inventory alerts
- Dashboard live data
"""
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.security import decode_token
from app.core.websocket_manager import websocket_manager, event_emitter
from app.core.alerts import alert_service


router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time updates.
    
    Connect with token: ws://host/api/v1/ws?token=<jwt_token>
    
    Message types received:
    - po_status_change: PO status updates
    - material_status_change: Material lifecycle updates
    - new_alert: New system alerts
    - inventory_update: Stock level changes
    - approval_required: New approval requests
    - dashboard_update: General dashboard refresh
    - grn_received: New goods receipt
    - inspection_complete: Inspection completed
    
    Client can send:
    - {"type": "subscribe", "entity_type": "purchase_order", "entity_id": 123}
    - {"type": "unsubscribe", "entity_type": "purchase_order", "entity_id": 123}
    - {"type": "ping"}
    """
    
    # Authenticate
    user_id = None
    role = "viewer"
    
    if token:
        payload = decode_token(token)
        if payload:
            user_id = int(payload.get("sub", 0))
            role = payload.get("role", "viewer")
    
    if not user_id:
        # Allow anonymous connection with limited features
        user_id = 0
        role = "anonymous"
    
    # Connect
    connection_id = await websocket_manager.connect(websocket, user_id, role)
    logger.info(
        "WebSocket connected: connection_id=%s user_id=%s role=%s",
        connection_id, user_id, role,
    )

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "connection_id": connection_id,
            "user_id": user_id,
            "role": role,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to real-time updates"
        })
        
        # Listen for messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                msg_type = message.get("type")
                
                if msg_type == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif msg_type == "subscribe":
                    entity_type = message.get("entity_type")
                    entity_id = message.get("entity_id")
                    
                    if entity_type and entity_id:
                        websocket_manager.subscribe_to_entity(
                            connection_id, entity_type, int(entity_id)
                        )
                        await websocket.send_json({
                            "type": "subscribed",
                            "entity_type": entity_type,
                            "entity_id": entity_id
                        })
                
                elif msg_type == "unsubscribe":
                    entity_type = message.get("entity_type")
                    entity_id = message.get("entity_id")
                    
                    if entity_type and entity_id:
                        websocket_manager.unsubscribe_from_entity(
                            connection_id, entity_type, int(entity_id)
                        )
                        await websocket.send_json({
                            "type": "unsubscribed",
                            "entity_type": entity_type,
                            "entity_id": entity_id
                        })
                
                elif msg_type == "get_alerts":
                    # Requires database session - simplified response
                    await websocket.send_json({
                        "type": "alerts_summary",
                        "message": "Use /api/v1/dashboard/alerts for detailed alerts",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif msg_type == "get_status":
                    await websocket.send_json({
                        "type": "status",
                        "connections": websocket_manager.get_connection_count(),
                        "users": websocket_manager.get_user_count(),
                        "your_connection_id": connection_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {msg_type}"
                    })
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: connection_id=%s user_id=%s", connection_id, user_id)
        websocket_manager.disconnect(connection_id, user_id, role)
    except Exception as e:
        logger.exception("WebSocket error: connection_id=%s user_id=%s", connection_id, user_id)
        websocket_manager.disconnect(connection_id, user_id, role)


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket server status."""
    return {
        "active_connections": websocket_manager.get_connection_count(),
        "connected_users": websocket_manager.get_user_count(),
        "dashboard_subscribers": len(websocket_manager.dashboard_subscribers),
        "timestamp": datetime.utcnow().isoformat()
    }


# Helper functions for emitting events from other parts of the application
async def emit_po_update(po_id: int, po_number: str, old_status: str, new_status: str, changed_by: str):
    """Emit PO status change event."""
    await event_emitter.emit_po_status_change(po_id, po_number, old_status, new_status, changed_by)


async def emit_material_update(instance_id: int, material_name: str, old_status: str, new_status: str, barcode: str = None):
    """Emit material status change event."""
    await event_emitter.emit_material_status_change(instance_id, material_name, old_status, new_status, barcode)


async def emit_alert(alert_type: str, severity: str, title: str, message: str, entity_type: str = None, entity_id: int = None):
    """Emit new alert event."""
    await event_emitter.emit_new_alert(alert_type, severity, title, message, entity_type, entity_id)


async def emit_inventory_change(material_id: int, material_name: str, old_qty: float, new_qty: float, location: str):
    """Emit inventory update event."""
    await event_emitter.emit_inventory_update(material_id, material_name, old_qty, new_qty, location)


async def emit_approval_request(workflow_type: str, entity_type: str, entity_id: int, entity_ref: str, roles: list):
    """Emit approval required event."""
    await event_emitter.emit_approval_required(workflow_type, entity_type, entity_id, entity_ref, roles)


async def emit_grn_receipt(grn_id: int, grn_number: str, po_number: str, supplier_name: str):
    """Emit GRN received event."""
    await event_emitter.emit_grn_received(grn_id, grn_number, po_number, supplier_name)


async def emit_inspection_result(material_id: int, material_name: str, result: str, inspector: str):
    """Emit inspection complete event."""
    await event_emitter.emit_inspection_complete(material_id, material_name, result, inspector)
