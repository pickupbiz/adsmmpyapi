"""Tests for PO status transitions."""
import pytest
from datetime import date
from fastapi.testclient import TestClient

from app.models.purchase_order import (
    PurchaseOrder, POLineItem, POStatus, POApprovalHistory, ApprovalAction
)


class TestPOStatusTransitions:
    """Test valid and invalid PO status transitions."""
    
    def test_draft_to_pending_approval(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test transition from draft to pending_approval."""
        po_id = test_po_with_line_items.id
        
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        assert po.status == POStatus.DRAFT
        
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        db.refresh(po)
        assert po.status == POStatus.PENDING_APPROVAL
    
    def test_pending_approval_to_approved(
        self,
        client: TestClient,
        director_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test transition from pending_approval to approved."""
        po_id = test_po_with_line_items.id
        
        # Submit first
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=director_headers
        )
        
        # Approve
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
            json={"action": "approved", "comments": "Approved"},
            headers=director_headers
        )
        
        assert response.status_code == 200
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        assert po.status == POStatus.APPROVED
    
    def test_pending_approval_to_rejected(
        self,
        client: TestClient,
        director_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test transition from pending_approval to rejected."""
        po_id = test_po_with_line_items.id
        
        # Submit first
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=director_headers
        )
        
        # Reject
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
            json={"action": "rejected", "comments": "Rejected"},
            headers=director_headers
        )
        
        assert response.status_code == 200
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        assert po.status == POStatus.REJECTED
    
    def test_pending_approval_to_draft_return(
        self,
        client: TestClient,
        director_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test transition from pending_approval back to draft (return)."""
        po_id = test_po_with_line_items.id
        
        # Submit first
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=director_headers
        )
        
        # Return for revision
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
            json={"action": "returned", "comments": "Needs revision"},
            headers=director_headers
        )
        
        assert response.status_code == 200
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        assert po.status == POStatus.DRAFT
    
    def test_approved_to_ordered(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test transition from approved to ordered."""
        po_id = test_po_with_line_items.id
        
        # Set to approved
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        po.status = POStatus.APPROVED
        db.commit()
        
        # Mark as ordered
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/order",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        db.refresh(po)
        assert po.status == POStatus.ORDERED
        assert po.ordered_date is not None
    
    def test_ordered_to_partially_received(
        self,
        client: TestClient,
        store_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test transition from ordered to partially_received."""
        po_id = test_po_with_line_items.id
        
        # Set to ordered
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        po.status = POStatus.ORDERED
        db.commit()
        
        line_item = db.query(POLineItem).filter(
            POLineItem.purchase_order_id == po_id
        ).first()
        
        # Create GRN with partial receipt via API
        grn_data = {
            "purchase_order_id": po_id,
            "receipt_date": str(date.today()),
            "line_items": [
                {
                    "po_line_item_id": line_item.id,
                    "quantity_received": 50.0,  # Partial (ordered 100.0)
                    "unit_of_measure": "kg"
                }
            ]
        }
        
        grn_response = client.post(
            f"/api/v1/purchase-orders/{po_id}/receive",
            json=grn_data,
            headers=store_headers
        )
        grn_id = grn_response.json()["id"]
        
        # Inspect and accept GRN
        client.post(
            f"/api/v1/purchase-orders/grn/{grn_id}/inspect",
            json={"inspection_notes": "Passed"},
            headers=qa_headers
        )
        client.post(
            f"/api/v1/purchase-orders/grn/{grn_id}/accept",
            headers=store_headers
        )
        
        # Check PO status
        db.refresh(po)
        assert po.status == POStatus.PARTIALLY_RECEIVED
    
    def test_partially_received_to_received(
        self,
        client: TestClient,
        store_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test transition from partially_received to received."""
        po_id = test_po_with_line_items.id
        
        # Set to partially received
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        po.status = POStatus.PARTIALLY_RECEIVED
        db.commit()
        
        line_item = db.query(POLineItem).filter(
            POLineItem.purchase_order_id == po_id
        ).first()
        line_item.quantity_received = 50.0  # Already received 50
        
        # Create second GRN for remaining quantity via API
        grn_data = {
            "purchase_order_id": po_id,
            "receipt_date": str(date.today()),
            "line_items": [
                {
                    "po_line_item_id": line_item.id,
                    "quantity_received": 50.0,  # Remaining 50
                    "unit_of_measure": "kg"
                }
            ]
        }
        
        grn_response = client.post(
            f"/api/v1/purchase-orders/{po_id}/receive",
            json=grn_data,
            headers=store_headers
        )
        grn_id = grn_response.json()["id"]
        
        # Inspect and accept GRN
        client.post(
            f"/api/v1/purchase-orders/grn/{grn_id}/inspect",
            json={"inspection_notes": "Passed"},
            headers=qa_headers
        )
        client.post(
            f"/api/v1/purchase-orders/grn/{grn_id}/accept",
            headers=store_headers
        )
        
        # Check PO status
        db.refresh(po)
        assert po.status == POStatus.RECEIVED
    
    def test_invalid_transition_draft_to_approved(
        self,
        client: TestClient,
        director_headers: dict,
        test_po_with_line_items
    ):
        """Test that draft cannot directly transition to approved."""
        po_id = test_po_with_line_items.id
        
        # Try to approve draft PO directly
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
            json={"comments": "Direct approval"},
            headers=director_headers
        )
        
        assert response.status_code == 400
    
    def test_invalid_transition_rejected_to_approved(
        self,
        client: TestClient,
        director_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test that rejected PO cannot be approved."""
        po_id = test_po_with_line_items.id
        
        # Set to rejected
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        po.status = POStatus.REJECTED
        db.commit()
        
        # Try to approve
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
            json={"action": "approved", "comments": "Trying to approve rejected"},
            headers=director_headers
        )
        
        assert response.status_code == 400


class TestPOStatusHistory:
    """Test PO status change history tracking."""
    
    def test_status_transition_creates_history(
        self,
        client: TestClient,
        director_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test that status transitions create history records."""
        po_id = test_po_with_line_items.id
        
        # Submit
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=director_headers
        )
        
        # Approve
        client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
            json={"action": "approved", "comments": "Approved"},
            headers=director_headers
        )
        
        # Check history
        history = db.query(POApprovalHistory).filter(
            POApprovalHistory.purchase_order_id == po_id
        ).order_by(POApprovalHistory.created_at).all()
        
        assert len(history) >= 2
        assert history[0].action == ApprovalAction.SUBMITTED
        assert history[1].action == ApprovalAction.APPROVED
        assert history[0].from_status == POStatus.DRAFT
        assert history[0].to_status == POStatus.PENDING_APPROVAL
        assert history[1].from_status == POStatus.PENDING_APPROVAL
        assert history[1].to_status == POStatus.APPROVED
