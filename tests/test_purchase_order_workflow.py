"""Tests for Purchase Order creation and approval workflow."""
import pytest
from datetime import date, datetime
from fastapi.testclient import TestClient

from app.models.purchase_order import PurchaseOrder, POLineItem, POStatus, POApprovalHistory, ApprovalAction
from app.models.user import UserRole


class TestPOCreation:
    """Test PO creation functionality."""
    
    def test_create_po_as_purchase_user(
        self,
        client: TestClient,
        auth_headers: dict,
        test_supplier,
        test_material
    ):
        """Test creating a PO as a purchase user."""
        po_data = {
            "supplier_id": test_supplier.id,
            "priority": "normal",
            "po_date": str(date.today()),
            "expected_delivery_date": str(date.today()),
            "subtotal": 1000.0,
            "tax_amount": 100.0,
            "shipping_cost": 50.0,
            "total_amount": 1150.0,
            "currency": "USD",
            "line_items": [
                {
                    "material_id": test_material.id,
                    "quantity_ordered": 100.0,
                    "unit_of_measure": "kg",
                    "unit_price": 10.0,
                    "line_number": 1
                }
            ]
        }
        
        response = client.post(
            "/api/v1/purchase-orders/",
            json=po_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "draft"
        assert data["po_number"] is not None
        assert len(data["line_items"]) == 1
        assert data["line_items"][0]["quantity_ordered"] == 100.0
    
    def test_create_po_with_multiple_line_items(
        self,
        client: TestClient,
        auth_headers: dict,
        test_supplier,
        test_material,
        db
    ):
        """Test creating a PO with multiple line items."""
        # Create second material
        from app.models.material import Material, MaterialType, MaterialStatus
        
        material2 = Material(
            item_number="MAT002",
            title="Test Material 2",
            material_type=MaterialType.RAW,
            status=MaterialStatus.ORDERED,
            quantity=50.0,
            unit_of_measure="kg",
            min_stock_level=5.0
        )
        db.add(material2)
        db.commit()
        db.refresh(material2)
        
        po_data = {
            "supplier_id": test_supplier.id,
            "priority": "high",
            "po_date": str(date.today()),
            "subtotal": 1500.0,
            "tax_amount": 150.0,
            "shipping_cost": 75.0,
            "total_amount": 1725.0,
            "currency": "USD",
            "line_items": [
                {
                    "material_id": test_material.id,
                    "quantity_ordered": 100.0,
                    "unit_of_measure": "kg",
                    "unit_price": 10.0,
                    "line_number": 1
                },
                {
                    "material_id": material2.id,
                    "quantity_ordered": 50.0,
                    "unit_of_measure": "kg",
                    "unit_price": 10.0,
                    "line_number": 2
                }
            ]
        }
        
        response = client.post(
            "/api/v1/purchase-orders/",
            json=po_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data["line_items"]) == 2
        assert data["total_amount"] == 1725.0
    
    def test_create_po_requires_authentication(
        self,
        client: TestClient,
        test_supplier
    ):
        """Test that creating a PO requires authentication."""
        po_data = {
            "supplier_id": test_supplier.id,
            "total_amount": 1000.0
        }
        
        response = client.post("/api/v1/purchase-orders/", json=po_data)
        assert response.status_code == 401
    
    def test_create_po_validates_supplier_exists(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test that PO creation validates supplier exists."""
        po_data = {
            "supplier_id": 99999,  # Non-existent supplier
            "total_amount": 1000.0,
            "line_items": []
        }
        
        response = client.post(
            "/api/v1/purchase-orders/",
            json=po_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestPOSubmission:
    """Test PO submission for approval."""
    
    def test_submit_po_for_approval(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items
    ):
        """Test submitting a PO for approval."""
        po_id = test_po_with_line_items.id
        
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending_approval"
    
    def test_submit_po_creates_approval_history(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test that submitting a PO creates approval history."""
        po_id = test_po_with_line_items.id
        
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Check approval history
        history = db.query(POApprovalHistory).filter(
            POApprovalHistory.purchase_order_id == po_id
        ).first()
        
        assert history is not None
        assert history.action == ApprovalAction.SUBMITTED
        assert history.to_status == POStatus.PENDING_APPROVAL


class TestPOApproval:
    """Test PO approval workflow."""
    
    def test_director_can_approve_po(
        self,
        client: TestClient,
        director_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test that director can approve a PO."""
        po_id = test_po_with_line_items.id
        
        # First submit the PO
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=director_headers
        )
        
        # Then approve it
        approval_data = {
            "action": "approved",
            "comments": "Approved for procurement"
        }
        
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
            json=approval_data,
            headers=director_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        
        # Verify approval history
        history = db.query(POApprovalHistory).filter(
            POApprovalHistory.purchase_order_id == po_id,
            POApprovalHistory.action == ApprovalAction.APPROVED
        ).first()
        
        assert history is not None
        assert history.comments == "Approved for procurement"
    
    def test_head_ops_can_approve_po(
        self,
        client: TestClient,
        head_ops_headers: dict,
        test_po_with_line_items
    ):
        """Test that head of operations can approve a PO."""
        po_id = test_po_with_line_items.id
        
        # Submit the PO
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=head_ops_headers
        )
        
        # Approve it
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
            json={"comments": "Approved"},
            headers=head_ops_headers
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "approved"
    
    def test_purchase_user_cannot_approve_po(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items
    ):
        """Test that purchase user cannot approve their own PO."""
        po_id = test_po_with_line_items.id
        
        # Submit the PO
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=auth_headers
        )
        
        # Try to approve it (should fail)
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
            json={"action": "approved", "comments": "Trying to approve"},
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_approve_po_requires_pending_status(
        self,
        client: TestClient,
        director_headers: dict,
        test_po_with_line_items
    ):
        """Test that only pending PO can be approved."""
        po_id = test_po_with_line_items.id
        
        # Try to approve draft PO directly (should fail)
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
            json={"action": "approved", "comments": "Trying to approve draft"},
            headers=director_headers
        )
        
        assert response.status_code == 400


class TestPORejection:
    """Test PO rejection workflow."""
    
    def test_director_can_reject_po(
        self,
        client: TestClient,
        director_headers: dict,
        test_po_with_line_items
    ):
        """Test that director can reject a PO."""
        po_id = test_po_with_line_items.id
        
        # Submit the PO
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=director_headers
        )
        
        # Reject it
        rejection_data = {
            "comments": "Rejected: Budget constraints"
        }
        
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/reject",
            json=rejection_data,
            headers=director_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"
        assert data["rejection_reason"] == "Rejected: Budget constraints"
    
    def test_reject_po_creates_history(
        self,
        client: TestClient,
        director_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test that rejecting a PO creates approval history."""
        po_id = test_po_with_line_items.id
        
        # Submit and reject
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=director_headers
        )
        
        client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
            json={"action": "rejected", "comments": "Rejected"},
            headers=director_headers
        )
        
        # Check history
        history = db.query(POApprovalHistory).filter(
            POApprovalHistory.purchase_order_id == po_id,
            POApprovalHistory.action == ApprovalAction.REJECTED
        ).first()
        
        assert history is not None


class TestPOReturn:
    """Test PO return for revision."""
    
    def test_director_can_return_po_for_revision(
        self,
        client: TestClient,
        director_headers: dict,
        test_po_with_line_items
    ):
        """Test that director can return a PO for revision."""
        po_id = test_po_with_line_items.id
        
        # Submit the PO
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=director_headers
        )
        
        # Return it
        return_data = {
            "comments": "Please revise pricing"
        }
        
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
            json=return_data,
            headers=director_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "draft"  # Returns to draft for revision


class TestPOOrdering:
    """Test marking PO as ordered."""
    
    def test_mark_po_as_ordered(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test marking an approved PO as ordered."""
        po_id = test_po_with_line_items.id
        
        # Submit and approve (using director)
        from app.models.purchase_order import POStatus
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        po.status = POStatus.APPROVED
        db.commit()
        
        # Mark as ordered
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/order",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ordered"
        assert data["ordered_date"] is not None
