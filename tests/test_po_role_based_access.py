"""Tests for role-based access control on PO operations."""
import pytest
from datetime import date
from fastapi.testclient import TestClient

from app.models.purchase_order import PurchaseOrder, POStatus


class TestPOCreationAccess:
    """Test access control for PO creation."""
    
    def test_purchase_user_can_create_po(
        self,
        client: TestClient,
        auth_headers: dict,
        test_supplier,
        test_material
    ):
        """Test that purchase user can create PO."""
        po_data = {
            "supplier_id": test_supplier.id,
            "total_amount": 1000.0,
            "line_items": [
                {
                    "material_id": test_material.id,
                    "quantity_ordered": 100.0,
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
    
    def test_store_user_cannot_create_po(
        self,
        client: TestClient,
        store_headers: dict,
        test_supplier
    ):
        """Test that store user cannot create PO."""
        po_data = {
            "supplier_id": test_supplier.id,
            "total_amount": 1000.0,
            "line_items": []
        }
        
        response = client.post(
            "/api/v1/purchase-orders/",
            json=po_data,
            headers=store_headers
        )
        
        assert response.status_code == 403
    
    def test_qa_user_cannot_create_po(
        self,
        client: TestClient,
        qa_headers: dict,
        test_supplier
    ):
        """Test that QA user cannot create PO."""
        po_data = {
            "supplier_id": test_supplier.id,
            "total_amount": 1000.0,
            "line_items": []
        }
        
        response = client.post(
            "/api/v1/purchase-orders/",
            json=po_data,
            headers=qa_headers
        )
        
        assert response.status_code == 403


class TestPOApprovalAccess:
    """Test access control for PO approval."""
    
    def test_director_can_approve_po(
        self,
        client: TestClient,
        director_headers: dict,
        test_po_with_line_items
    ):
        """Test that director can approve PO."""
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
    
    def test_head_ops_can_approve_po(
        self,
        client: TestClient,
        head_ops_headers: dict,
        test_po_with_line_items
    ):
        """Test that head of operations can approve PO."""
        po_id = test_po_with_line_items.id
        
        # Submit first
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=head_ops_headers
        )
        
        # Approve
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
            json={"comments": "Approved"},
            headers=head_ops_headers
        )
        
        assert response.status_code == 200
    
    def test_purchase_user_cannot_approve_po(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items
    ):
        """Test that purchase user cannot approve PO."""
        po_id = test_po_with_line_items.id
        
        # Submit first
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=auth_headers
        )
        
        # Try to approve (should fail)
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
            json={"action": "approved", "comments": "Trying to approve"},
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_store_user_cannot_approve_po(
        self,
        client: TestClient,
        store_headers: dict,
        test_po_with_line_items
    ):
        """Test that store user cannot approve PO."""
        po_id = test_po_with_line_items.id
        
        # Submit first (using purchase user - auth_headers)
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=auth_headers
        )
        
        # Try to approve as store user (should fail)
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
            json={"comments": "Trying to approve"},
            headers=store_headers
        )
        
        assert response.status_code == 403


class TestGRNAccess:
    """Test access control for GRN operations."""
    
    def test_store_user_can_create_grn(
        self,
        client: TestClient,
        store_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test that store user can create GRN."""
        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.id == test_po_with_line_items.id
        ).first()
        po.status = POStatus.ORDERED
        db.commit()
        
        po_id = po.id
        line_item = db.query(POLineItem).filter(
            POLineItem.purchase_order_id == po_id
        ).first()
        
        grn_data = {
            "purchase_order_id": po_id,
            "receipt_date": str(date.today()),
            "line_items": [
                {
                    "po_line_item_id": line_item.id,
                    "quantity_received": 50.0,
                    "unit_of_measure": "kg"
                }
            ]
        }
        
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/receive",
            json=grn_data,
            headers=store_headers
        )
        
        assert response.status_code == 201
    
    def test_purchase_user_cannot_create_grn(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test that purchase user cannot create GRN."""
        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.id == test_po_with_line_items.id
        ).first()
        po.status = POStatus.ORDERED
        db.commit()
        
        po_id = po.id
        line_item = db.query(POLineItem).filter(
            POLineItem.purchase_order_id == po_id
        ).first()
        
        grn_data = {
            "purchase_order_id": po_id,
            "receipt_date": str(date.today()),
            "line_items": [
                {
                    "po_line_item_id": line_item.id,
                    "quantity_received": 50.0,
                    "unit_of_measure": "kg"
                }
            ]
        }
        
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/receive",
            json=grn_data,
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_qa_user_can_inspect_grn(
        self,
        client: TestClient,
        qa_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test that QA user can inspect GRN."""
        from app.models.purchase_order import GoodsReceiptNote, GRNLineItem, GRNStatus
        
        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.id == test_po_with_line_items.id
        ).first()
        po.status = POStatus.ORDERED
        db.commit()
        
        po_id = po.id
        line_item = db.query(POLineItem).filter(
            POLineItem.purchase_order_id == po_id
        ).first()
        
        grn = GoodsReceiptNote(
            grn_number="GRN-QA-001",
            purchase_order_id=po_id,
            received_by_id=1,
            status=GRNStatus.PENDING_INSPECTION,
            receipt_date=date.today()
        )
        db.add(grn)
        db.commit()
        db.refresh(grn)
        
        grn_item = GRNLineItem(
            goods_receipt_id=grn.id,
            po_line_item_id=line_item.id,
            quantity_received=50.0,
            unit_of_measure="kg"
        )
        db.add(grn_item)
        db.commit()
        
        # Inspect GRN
        response = client.post(
            f"/api/v1/purchase-orders/grn/{grn.id}/inspect",
            params={"inspection_passed": True},
            json={"inspection_notes": "Passed inspection"},
            headers=qa_headers
        )
        
        assert response.status_code == 200
    
    def test_store_user_cannot_inspect_grn(
        self,
        client: TestClient,
        store_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test that store user cannot inspect GRN."""
        from app.models.purchase_order import GoodsReceiptNote, GRNLineItem, GRNStatus
        
        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.id == test_po_with_line_items.id
        ).first()
        po.status = POStatus.ORDERED
        db.commit()
        
        po_id = po.id
        line_item = db.query(POLineItem).filter(
            POLineItem.purchase_order_id == po_id
        ).first()
        
        grn = GoodsReceiptNote(
            grn_number="GRN-STORE-001",
            purchase_order_id=po_id,
            received_by_id=1,
            status=GRNStatus.PENDING_INSPECTION,
            receipt_date=date.today()
        )
        db.add(grn)
        db.commit()
        db.refresh(grn)
        
        grn_item = GRNLineItem(
            goods_receipt_id=grn.id,
            po_line_item_id=line_item.id,
            quantity_received=50.0,
            unit_of_measure="kg"
        )
        db.add(grn_item)
        db.commit()
        
        # Try to inspect (should fail)
        response = client.post(
            f"/api/v1/purchase-orders/grn/{grn.id}/inspect",
            params={"inspection_passed": True},
            json={"inspection_notes": "Trying to inspect"},
            headers=store_headers
        )
        
        assert response.status_code == 403


class TestPOViewAccess:
    """Test access control for viewing PO."""
    
    def test_all_roles_can_view_po(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items
    ):
        """Test that all authenticated users can view PO."""
        po_id = test_po_with_line_items.id
        
        response = client.get(
            f"/api/v1/purchase-orders/{po_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_unauthenticated_cannot_view_po(
        self,
        client: TestClient,
        test_po_with_line_items
    ):
        """Test that unauthenticated users cannot view PO."""
        po_id = test_po_with_line_items.id
        
        response = client.get(f"/api/v1/purchase-orders/{po_id}")
        
        assert response.status_code == 401
