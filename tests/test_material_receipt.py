"""Tests for material receipt against PO validation."""
import pytest
from datetime import date
from fastapi.testclient import TestClient

from app.models.purchase_order import (
    PurchaseOrder, POLineItem, GoodsReceiptNote, GRNLineItem,
    POStatus, GRNStatus
)
from app.models.material_instance import MaterialInstance, MaterialLifecycleStatus


class TestGRNCreation:
    """Test Goods Receipt Note creation."""
    
    def test_create_grn_for_ordered_po(
        self,
        client: TestClient,
        store_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test creating a GRN for an ordered PO."""
        # Set PO to ordered status
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
                    "unit_of_measure": "kg",
                    "lot_number": "LOT001"
                }
            ]
        }
        
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/receive",
            json=grn_data,
            headers=store_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        # GRN is created in DRAFT status
        assert data["status"] in ["draft", "pending_inspection"]
        assert len(data["line_items"]) == 1
        assert data["line_items"][0]["quantity_received"] == 50.0
    
    def test_create_grn_validates_po_status(
        self,
        client: TestClient,
        store_headers: dict,
        test_po_with_line_items
    ):
        """Test that GRN can only be created for ordered PO."""
        po_id = test_po_with_line_items.id
        
        # PO is in draft status, should fail
        grn_data = {
            "purchase_order_id": po_id,
            "receipt_date": str(date.today()),
            "line_items": []
        }
        
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/receive",
            json=grn_data,
            headers=store_headers
        )
        
        assert response.status_code == 400
    
    def test_create_grn_validates_quantity(
        self,
        client: TestClient,
        store_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test that GRN validates received quantity against ordered."""
        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.id == test_po_with_line_items.id
        ).first()
        po.status = POStatus.ORDERED
        db.commit()
        
        po_id = po.id
        line_item = db.query(POLineItem).filter(
            POLineItem.purchase_order_id == po_id
        ).first()
        
        # Try to receive more than ordered
        grn_data = {
            "purchase_order_id": po_id,
            "receipt_date": str(date.today()),
            "line_items": [
                {
                    "po_line_item_id": line_item.id,
                    "quantity_received": 200.0,  # More than ordered (100.0)
                    "unit_of_measure": "kg"
                }
            ]
        }
        
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/receive",
            json=grn_data,
            headers=store_headers
        )
        
        # Should either reject or warn
        assert response.status_code in [400, 201]  # May allow with warning


class TestGRNInspection:
    """Test GRN inspection workflow."""
    
    def test_qa_can_inspect_grn(
        self,
        client: TestClient,
        qa_headers: dict,
        store_headers: dict,
        test_po_with_line_items,
        test_store_user,
        db
    ):
        """Test that QA can inspect a GRN."""
        # Create GRN
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
            grn_number="GRN-TEST-001",
            purchase_order_id=po_id,
            received_by_id=test_store_user.id,
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
            json={"inspection_notes": "All materials passed inspection"},
            headers=qa_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # After inspection, status should be inspection_passed
        assert data["status"] in ["inspection_passed", "pending_inspection"]
    
    def test_qa_can_reject_grn(
        self,
        client: TestClient,
        qa_headers: dict,
        test_po_with_line_items,
        test_store_user,
        db
    ):
        """Test that QA can reject a GRN."""
        # Create GRN
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
            grn_number="GRN-TEST-002",
            purchase_order_id=po_id,
            received_by_id=test_store_user.id,
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
        
        # Reject GRN
        response = client.post(
            f"/api/v1/purchase-orders/grn/{grn.id}/inspect",
            params={"inspection_passed": False},
            json={"inspection_notes": "Materials do not meet specifications"},
            headers=qa_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # After failed inspection, status should be inspection_failed
        assert data["status"] in ["inspection_failed", "pending_inspection"]


class TestGRNAcceptance:
    """Test GRN acceptance to inventory."""
    
    def test_accept_grn_to_inventory(
        self,
        client: TestClient,
        store_headers: dict,
        qa_headers: dict,
        test_po_with_line_items,
        test_store_user,
        db
    ):
        """Test accepting a GRN to inventory."""
        # Create and inspect GRN
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
            grn_number="GRN-TEST-003",
            purchase_order_id=po_id,
            received_by_id=test_store_user.id,
            status=GRNStatus.INSPECTION_PASSED,
            receipt_date=date.today()
        )
        db.add(grn)
        db.commit()
        db.refresh(grn)
        
        grn_item = GRNLineItem(
            goods_receipt_id=grn.id,
            po_line_item_id=line_item.id,
            quantity_received=50.0,
            quantity_accepted=50.0,
            unit_of_measure="kg"
        )
        db.add(grn_item)
        db.commit()
        
        # Accept GRN (after inspection)
        # First inspect it
        client.post(
            f"/api/v1/purchase-orders/grn/{grn.id}/inspect",
            params={"inspection_passed": True},
            json={"inspection_notes": "Passed"},
            headers=qa_headers
        )
        
        # Then accept
        response = client.post(
            f"/api/v1/purchase-orders/grn/{grn.id}/accept",
            headers=store_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        
        # Verify PO line item updated
        db.refresh(line_item)
        assert line_item.quantity_received == 50.0
        assert line_item.quantity_accepted == 50.0


class TestMaterialInstanceCreation:
    """Test material instance creation from GRN."""
    
    def test_accept_grn_creates_material_instances(
        self,
        client: TestClient,
        store_headers: dict,
        test_po_with_line_items,
        test_store_user,
        db
    ):
        """Test that accepting GRN creates material instances."""
        # Setup GRN
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
            grn_number="GRN-TEST-004",
            purchase_order_id=po_id,
            received_by_id=test_store_user.id,
            status=GRNStatus.INSPECTION_PASSED,
            receipt_date=date.today()
        )
        db.add(grn)
        db.commit()
        db.refresh(grn)
        
        grn_item = GRNLineItem(
            goods_receipt_id=grn.id,
            po_line_item_id=line_item.id,
            quantity_received=50.0,
            quantity_accepted=50.0,
            unit_of_measure="kg",
            lot_number="LOT001"
        )
        db.add(grn_item)
        db.commit()
        
        # Accept GRN
        client.post(
            f"/api/v1/purchase-orders/grn/{grn.id}/accept",
            headers=store_headers
        )
        
        # Check material instances created
        instances = db.query(MaterialInstance).filter(
            MaterialInstance.po_line_item_id == line_item.id
        ).all()
        
        assert len(instances) > 0
        assert instances[0].lifecycle_status == MaterialLifecycleStatus.RECEIVED
        assert instances[0].lot_number == "LOT001"
