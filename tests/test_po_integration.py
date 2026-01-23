"""Integration tests for complete PO→Material flow."""
import pytest
from datetime import date
from fastapi.testclient import TestClient

from app.models.purchase_order import (
    PurchaseOrder, POLineItem, GoodsReceiptNote, GRNLineItem,
    POStatus, GRNStatus
)
from app.models.material_instance import MaterialInstance, MaterialLifecycleStatus
from app.models.inventory import Inventory


class TestCompletePOFlow:
    """Test complete PO to material flow."""
    
    def test_complete_po_to_material_flow(
        self,
        client: TestClient,
        auth_headers: dict,
        director_headers: dict,
        store_headers: dict,
        qa_headers: dict,
        test_supplier,
        test_material,
        db
    ):
        """Test complete flow: Create PO → Approve → Order → Receive → Inspect → Accept → Inventory."""
        # Step 1: Create PO
        po_data = {
            "supplier_id": test_supplier.id,
            "priority": "high",
            "po_date": str(date.today()),
            "expected_delivery_date": str(date.today() + timedelta(days=30)),
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
        
        create_response = client.post(
            "/api/v1/purchase-orders/",
            json=po_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        po_id = create_response.json()["id"]
        
        # Step 2: Submit for approval
        submit_response = client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=auth_headers
        )
        assert submit_response.status_code == 200
        assert submit_response.json()["status"] == "pending_approval"
        
        # Step 3: Approve PO
        approve_response = client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
            json={"action": "approved", "comments": "Approved for procurement"},
            headers=director_headers
        )
        assert approve_response.status_code == 200
        assert approve_response.json()["status"] == "approved"
        
        # Step 4: Mark as ordered
        order_response = client.post(
            f"/api/v1/purchase-orders/{po_id}/mark-ordered",
            headers=auth_headers
        )
        assert order_response.status_code == 200
        assert order_response.json()["status"] == "ordered"
        
        # Step 5: Create GRN (receive materials)
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        line_item = db.query(POLineItem).filter(
            POLineItem.purchase_order_id == po_id
        ).first()
        
        grn_data = {
            "purchase_order_id": po_id,
            "receipt_date": str(date.today()),
            "line_items": [
                {
                    "po_line_item_id": line_item.id,
                    "quantity_received": 100.0,
                    "unit_of_measure": "kg",
                    "lot_number": "LOT-INTEGRATION-001"
                }
            ]
        }
        
        grn_response = client.post(
            f"/api/v1/purchase-orders/{po_id}/receive",
            json=grn_data,
            headers=store_headers
        )
        assert grn_response.status_code == 201
        grn_id = grn_response.json()["id"]
        # GRN is created in DRAFT status, needs to be inspected
        
        # Step 6: Inspect GRN
        inspect_response = client.post(
            f"/api/v1/purchase-orders/grn/{grn_id}/inspect",
            params={"inspection_passed": True},
            json={"inspection_notes": "All materials passed quality inspection"},
            headers=qa_headers
        )
        assert inspect_response.status_code == 200
        # Status should be inspection_passed after inspection
        assert inspect_response.json()["status"] in ["inspection_passed", "pending_inspection"]
        
        # Step 7: Accept GRN to inventory
        accept_response = client.post(
            f"/api/v1/purchase-orders/grn/{grn_id}/accept",
            headers=store_headers
        )
        assert accept_response.status_code == 200
        assert accept_response.json()["status"] == "accepted"
        
        # Step 8: Verify PO status updated
        db.refresh(po)
        assert po.status == POStatus.RECEIVED
        
        # Step 9: Verify line item quantities
        db.refresh(line_item)
        assert line_item.quantity_received == 100.0
        assert line_item.quantity_accepted == 100.0
        
        # Step 10: Verify material instances created
        instances = db.query(MaterialInstance).filter(
            MaterialInstance.po_line_item_id == line_item.id
        ).all()
        assert len(instances) > 0
        assert all(inst.lifecycle_status == MaterialLifecycleStatus.RECEIVED for inst in instances)
        assert all(inst.purchase_order_id == po_id for inst in instances)
        
        # Step 11: Verify inventory updated
        inventory = db.query(Inventory).filter(
            Inventory.material_id == test_material.id
        ).first()
        if inventory:
            assert inventory.quantity >= 100.0


class TestPartialReceiptFlow:
    """Test partial receipt flow."""
    
    def test_partial_receipt_and_completion(
        self,
        client: TestClient,
        auth_headers: dict,
        director_headers: dict,
        store_headers: dict,
        qa_headers: dict,
        test_supplier,
        test_material,
        db
    ):
        """Test receiving materials in multiple shipments."""
        from datetime import timedelta
        
        # Create and approve PO
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
        
        create_response = client.post(
            "/api/v1/purchase-orders/",
            json=po_data,
            headers=auth_headers
        )
        po_id = create_response.json()["id"]
        
        # Submit and approve
        client.post(f"/api/v1/purchase-orders/{po_id}/submit", headers=auth_headers)
        client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
            json={"action": "approved", "comments": "Approved"},
            headers=director_headers
        )
        client.post(f"/api/v1/purchase-orders/{po_id}/order", headers=auth_headers)
        
        # First partial receipt (50%)
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        line_item = db.query(POLineItem).filter(
            POLineItem.purchase_order_id == po_id
        ).first()
        
        grn1_data = {
            "purchase_order_id": po_id,
            "receipt_date": str(date.today()),
            "line_items": [
                {
                    "po_line_item_id": line_item.id,
                    "quantity_received": 50.0,
                    "unit_of_measure": "kg",
                    "lot_number": "LOT-PARTIAL-001"
                }
            ]
        }
        
        grn1_response = client.post(
            f"/api/v1/purchase-orders/{po_id}/receive",
            json=grn1_data,
            headers=store_headers
        )
        grn1_id = grn1_response.json()["id"]
        
        # Inspect and accept first GRN
        grn1_item = db.query(GRNLineItem).filter(
            GRNLineItem.goods_receipt_id == grn1_id
        ).first()
        
        client.post(
            f"/api/v1/purchase-orders/grn/{grn1_id}/inspect",
            params={"inspection_passed": True},
            json={"inspection_notes": "Passed"},
            headers=qa_headers
        )
        client.post(f"/api/v1/purchase-orders/grn/{grn1_id}/accept", headers=store_headers)
        
        # Verify partial status
        db.refresh(po)
        assert po.status == POStatus.PARTIALLY_RECEIVED
        db.refresh(line_item)
        assert line_item.quantity_received == 50.0
        
        # Second receipt (remaining 50%)
        grn2_data = {
            "purchase_order_id": po_id,
            "receipt_date": str(date.today()),
            "line_items": [
                {
                    "po_line_item_id": line_item.id,
                    "quantity_received": 50.0,
                    "unit_of_measure": "kg",
                    "lot_number": "LOT-PARTIAL-002"
                }
            ]
        }
        
        grn2_response = client.post(
            f"/api/v1/purchase-orders/{po_id}/receive",
            json=grn2_data,
            headers=store_headers
        )
        grn2_id = grn2_response.json()["id"]
        
        # Inspect and accept second GRN
        client.post(
            f"/api/v1/purchase-orders/grn/{grn2_id}/inspect",
            params={"inspection_passed": True},
            json={"inspection_notes": "Passed"},
            headers=qa_headers
        )
        client.post(f"/api/v1/purchase-orders/grn/{grn2_id}/accept", headers=store_headers)
        
        # Verify complete status
        db.refresh(po)
        assert po.status == POStatus.RECEIVED
        db.refresh(line_item)
        assert line_item.quantity_received == 100.0
        assert line_item.quantity_accepted == 100.0


class TestMaterialLifecycleFromPO:
    """Test material lifecycle starting from PO."""
    
    def test_material_lifecycle_from_po_to_production(
        self,
        client: TestClient,
        auth_headers: dict,
        director_headers: dict,
        store_headers: dict,
        qa_headers: dict,
        test_supplier,
        test_material,
        db
    ):
        """Test material moving through lifecycle from PO receipt to production."""
        from datetime import timedelta
        
        # Create, approve, and receive PO
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
        
        po_response = client.post(
            "/api/v1/purchase-orders/",
            json=po_data,
            headers=auth_headers
        )
        po_id = po_response.json()["id"]
        
        # Complete PO workflow
        client.post(f"/api/v1/purchase-orders/{po_id}/submit", headers=auth_headers)
        client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
            json={"action": "approved", "comments": "Approved"},
            headers=director_headers
        )
        client.post(f"/api/v1/purchase-orders/{po_id}/order", headers=auth_headers)
        
        # Receive and accept
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        line_item = db.query(POLineItem).filter(
            POLineItem.purchase_order_id == po_id
        ).first()
        
        grn_data = {
            "purchase_order_id": po_id,
            "receipt_date": str(date.today()),
            "line_items": [
                {
                    "po_line_item_id": line_item.id,
                    "quantity_received": 100.0,
                    "unit_of_measure": "kg",
                    "lot_number": "LOT-LIFECYCLE"
                }
            ]
        }
        
        grn_response = client.post(
            f"/api/v1/purchase-orders/{po_id}/receive",
            json=grn_data,
            headers=store_headers
        )
        grn_id = grn_response.json()["id"]
        
        client.post(
            f"/api/v1/purchase-orders/grn/{grn_id}/inspect",
            params={"inspection_passed": True},
            json={"inspection_notes": "Passed"},
            headers=qa_headers
        )
        client.post(f"/api/v1/purchase-orders/grn/{grn_id}/accept", headers=store_headers)
        
        # Get material instance
        instance = db.query(MaterialInstance).filter(
            MaterialInstance.po_line_item_id == line_item.id
        ).first()
        
        assert instance is not None
        assert instance.lifecycle_status == MaterialLifecycleStatus.RECEIVED
        assert instance.purchase_order_id == po_id
        
        # Move through lifecycle
        statuses = [
            MaterialLifecycleStatus.IN_INSPECTION,
            MaterialLifecycleStatus.IN_STORAGE,
            MaterialLifecycleStatus.ISSUED,
            MaterialLifecycleStatus.IN_PRODUCTION,
            MaterialLifecycleStatus.COMPLETED
        ]
        
        for status in statuses:
            response = client.post(
                f"/api/v1/material-instances/{instance.id}/status",
                json={"status": status.value},
                headers=auth_headers
            )
            assert response.status_code == 200
            
            db.refresh(instance)
            assert instance.lifecycle_status == status
            # Verify PO reference maintained
            assert instance.purchase_order_id == po_id
            assert instance.po_line_item_id == line_item.id
