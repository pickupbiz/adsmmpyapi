"""
WebSocket manager for real-time updates.

Provides:
- Connection management
- Broadcast capabilities
- Room-based messaging (by user role, entity type, etc.)
- Message queuing for offline clients
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

from app.schemas.dashboard import WebSocketMessage, WebSocketMessageType


class ConnectionManager:
    """Manages WebSocket connections and messaging."""
    
    def __init__(self):
        # Active connections: {connection_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # User connections: {user_id: Set[connection_id]}
        self.user_connections: Dict[int, Set[str]] = {}
        
        # Role subscriptions: {role: Set[connection_id]}
        self.role_subscriptions: Dict[str, Set[str]] = {}
        
        # Entity subscriptions: {entity_type: {entity_id: Set[connection_id]}}
        self.entity_subscriptions: Dict[str, Dict[int, Set[str]]] = {}
        
        # General subscriptions (dashboard updates)
        self.dashboard_subscribers: Set[str] = set()
        
        # Connection counter for unique IDs
        self._connection_counter = 0
    
    def _generate_connection_id(self) -> str:
        """Generate unique connection ID."""
        self._connection_counter += 1
        return f"conn_{self._connection_counter}_{datetime.utcnow().timestamp()}"
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        role: str
    ) -> str:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        connection_id = self._generate_connection_id()
        self.active_connections[connection_id] = websocket
        
        # Track by user
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        # Track by role
        if role not in self.role_subscriptions:
            self.role_subscriptions[role] = set()
        self.role_subscriptions[role].add(connection_id)
        
        # Auto-subscribe to dashboard updates
        self.dashboard_subscribers.add(connection_id)
        
        return connection_id
    
    def disconnect(self, connection_id: str, user_id: int, role: str):
        """Handle WebSocket disconnection."""
        # Remove from active connections
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from user connections
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove from role subscriptions
        if role in self.role_subscriptions:
            self.role_subscriptions[role].discard(connection_id)
        
        # Remove from dashboard subscribers
        self.dashboard_subscribers.discard(connection_id)
        
        # Remove from entity subscriptions
        for entity_type in self.entity_subscriptions:
            for entity_id in self.entity_subscriptions[entity_type]:
                self.entity_subscriptions[entity_type][entity_id].discard(connection_id)
    
    def subscribe_to_entity(
        self,
        connection_id: str,
        entity_type: str,
        entity_id: int
    ):
        """Subscribe a connection to entity updates."""
        if entity_type not in self.entity_subscriptions:
            self.entity_subscriptions[entity_type] = {}
        if entity_id not in self.entity_subscriptions[entity_type]:
            self.entity_subscriptions[entity_type][entity_id] = set()
        self.entity_subscriptions[entity_type][entity_id].add(connection_id)
    
    def unsubscribe_from_entity(
        self,
        connection_id: str,
        entity_type: str,
        entity_id: int
    ):
        """Unsubscribe a connection from entity updates."""
        if (entity_type in self.entity_subscriptions and 
            entity_id in self.entity_subscriptions[entity_type]):
            self.entity_subscriptions[entity_type][entity_id].discard(connection_id)
    
    async def send_personal_message(self, message: dict, connection_id: str):
        """Send message to a specific connection."""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_json(message)
            except Exception:
                pass
    
    async def send_to_user(self, message: dict, user_id: int):
        """Send message to all connections of a user."""
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                await self.send_personal_message(message, connection_id)
    
    async def broadcast_to_role(self, message: dict, role: str):
        """Broadcast message to all users with a specific role."""
        if role in self.role_subscriptions:
            for connection_id in self.role_subscriptions[role]:
                await self.send_personal_message(message, connection_id)
    
    async def broadcast_to_roles(self, message: dict, roles: List[str]):
        """Broadcast message to all users with any of the specified roles."""
        sent_connections = set()
        for role in roles:
            if role in self.role_subscriptions:
                for connection_id in self.role_subscriptions[role]:
                    if connection_id not in sent_connections:
                        await self.send_personal_message(message, connection_id)
                        sent_connections.add(connection_id)
    
    async def broadcast_entity_update(
        self,
        entity_type: str,
        entity_id: int,
        message: dict
    ):
        """Broadcast update to all subscribers of an entity."""
        if (entity_type in self.entity_subscriptions and 
            entity_id in self.entity_subscriptions[entity_type]):
            for connection_id in self.entity_subscriptions[entity_type][entity_id]:
                await self.send_personal_message(message, connection_id)
    
    async def broadcast_dashboard_update(self, message: dict):
        """Broadcast dashboard update to all subscribers."""
        for connection_id in self.dashboard_subscribers:
            await self.send_personal_message(message, connection_id)
    
    async def broadcast_all(self, message: dict):
        """Broadcast message to all connected clients."""
        for connection_id in self.active_connections:
            await self.send_personal_message(message, connection_id)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.active_connections)
    
    def get_user_count(self) -> int:
        """Get number of unique connected users."""
        return len(self.user_connections)


# Singleton instance
websocket_manager = ConnectionManager()


class WebSocketEventEmitter:
    """Helper class to emit WebSocket events from application code."""
    
    def __init__(self, manager: ConnectionManager):
        self.manager = manager
    
    async def emit_po_status_change(
        self,
        po_id: int,
        po_number: str,
        old_status: str,
        new_status: str,
        changed_by: str
    ):
        """Emit PO status change event."""
        message = WebSocketMessage(
            type=WebSocketMessageType.PO_STATUS_CHANGE,
            entity_type="purchase_order",
            entity_id=po_id,
            data={
                "po_id": po_id,
                "po_number": po_number,
                "old_status": old_status,
                "new_status": new_status,
                "changed_by": changed_by,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        await self.manager.broadcast_dashboard_update(message.model_dump())
        await self.manager.broadcast_entity_update("purchase_order", po_id, message.model_dump())
    
    async def emit_material_status_change(
        self,
        instance_id: int,
        material_name: str,
        old_status: str,
        new_status: str,
        barcode: Optional[str] = None
    ):
        """Emit material status change event."""
        message = WebSocketMessage(
            type=WebSocketMessageType.MATERIAL_STATUS_CHANGE,
            entity_type="material_instance",
            entity_id=instance_id,
            data={
                "instance_id": instance_id,
                "material_name": material_name,
                "barcode": barcode,
                "old_status": old_status,
                "new_status": new_status,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        await self.manager.broadcast_dashboard_update(message.model_dump())
    
    async def emit_new_alert(
        self,
        alert_type: str,
        severity: str,
        title: str,
        message_text: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None
    ):
        """Emit new alert event."""
        message = WebSocketMessage(
            type=WebSocketMessageType.NEW_ALERT,
            entity_type=entity_type,
            entity_id=entity_id,
            data={
                "alert_type": alert_type,
                "severity": severity,
                "title": title,
                "message": message_text,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        await self.manager.broadcast_all(message.model_dump())
    
    async def emit_inventory_update(
        self,
        material_id: int,
        material_name: str,
        old_quantity: float,
        new_quantity: float,
        location: str
    ):
        """Emit inventory update event."""
        message = WebSocketMessage(
            type=WebSocketMessageType.INVENTORY_UPDATE,
            entity_type="inventory",
            entity_id=material_id,
            data={
                "material_id": material_id,
                "material_name": material_name,
                "old_quantity": old_quantity,
                "new_quantity": new_quantity,
                "location": location,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        await self.manager.broadcast_dashboard_update(message.model_dump())
    
    async def emit_approval_required(
        self,
        workflow_type: str,
        entity_type: str,
        entity_id: int,
        entity_reference: str,
        required_roles: List[str]
    ):
        """Emit approval required event to appropriate roles."""
        message = WebSocketMessage(
            type=WebSocketMessageType.APPROVAL_REQUIRED,
            entity_type=entity_type,
            entity_id=entity_id,
            data={
                "workflow_type": workflow_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "entity_reference": entity_reference,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        await self.manager.broadcast_to_roles(message.model_dump(), required_roles)
    
    async def emit_grn_received(
        self,
        grn_id: int,
        grn_number: str,
        po_number: str,
        supplier_name: str
    ):
        """Emit GRN received event."""
        message = WebSocketMessage(
            type=WebSocketMessageType.GRN_RECEIVED,
            entity_type="grn",
            entity_id=grn_id,
            data={
                "grn_id": grn_id,
                "grn_number": grn_number,
                "po_number": po_number,
                "supplier_name": supplier_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        await self.manager.broadcast_dashboard_update(message.model_dump())
        # Notify Store and QA roles
        await self.manager.broadcast_to_roles(message.model_dump(), ["store", "qa"])
    
    async def emit_inspection_complete(
        self,
        material_id: int,
        material_name: str,
        result: str,  # passed, failed
        inspector: str
    ):
        """Emit inspection complete event."""
        message = WebSocketMessage(
            type=WebSocketMessageType.INSPECTION_COMPLETE,
            entity_type="material",
            entity_id=material_id,
            data={
                "material_id": material_id,
                "material_name": material_name,
                "result": result,
                "inspector": inspector,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        await self.manager.broadcast_dashboard_update(message.model_dump())


# Singleton event emitter
event_emitter = WebSocketEventEmitter(websocket_manager)
