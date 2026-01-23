"""Tests for material traceability from PO to Finished Goods."""
import pytest
from datetime import date
from fastapi.testclient import TestClient

from app.models.purchase_order import PurchaseOrder, POLineItem, POStatus
from app.models.material_instance import MaterialInstance, MaterialLifecycleStatus
from app.models.barcode import BarcodeLabel, BarcodeEntityType


class TestPOTraceability:
    """Test PO to material traceability."""
    
    def test_material_instance_linked_to_po(
        self,
        client: TestClient,
        store_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test that material instances are linked to PO."""
        po_id = test_po_with_line_items.id
        
        # Setup: Create GRN and accept
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        po.status = POStatus.ORDERED
        db.commit()
        
        line_item = db.query(POLineItem).filter(
            POLineItem.purchase_order_id == po_id
        ).first()
        
        from app.models.purchase_order import GoodsReceiptNote, GRNLineItem, GRNStatus
        
        grn = GoodsReceiptNote(
            grn_number="GRN-TRACE-001",
            purchase_order_id=po_id,
            received_by_id=1,
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
        
        # Check material instances
        instances = db.query(MaterialInstance).filter(
            MaterialInstance.po_line_item_id == line_item.id
        ).all()
        
        assert len(instances) > 0
        for instance in instances:
            assert instance.purchase_order_id == po_id
            assert instance.po_line_item_id == line_item.id
            assert instance.lot_number == "LOT001"
    
    def test_trace_material_to_po(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test tracing a material instance back to its PO."""
        # Create material instance from PO
        po_id = test_po_with_line_items.id
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        line_item = db.query(POLineItem).filter(
            POLineItem.purchase_order_id == po_id
        ).first()
        
        instance = MaterialInstance(
            item_number="INST-001",
            title="Test Material Instance",
            material_id=line_item.material_id,
            purchase_order_id=po_id,
            po_line_item_id=line_item.id,
            quantity=50.0,
            unit_of_measure="kg",
            lifecycle_status=MaterialLifecycleStatus.RECEIVED,
            lot_number="LOT001"
        )
        db.add(instance)
        db.commit()
        db.refresh(instance)
        
        # Get material instance details
        response = client.get(
            f"/api/v1/material-instances/{instance.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["purchase_order_id"] == po_id
        assert data["po_line_item_id"] == line_item.id
        assert "purchase_order" in data or "po_reference" in str(data)


class TestMaterialLifecycleTracking:
    """Test material lifecycle tracking from PO to finished goods."""
    
    def test_material_lifecycle_from_po_to_finished(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test complete material lifecycle from PO to finished goods."""
        po_id = test_po_with_line_items.id
        line_item = db.query(POLineItem).filter(
            POLineItem.purchase_order_id == po_id
        ).first()
        
        # Create material instance (received from PO)
        instance = MaterialInstance(
            item_number="INST-LIFECYCLE-001",
            title="Lifecycle Test Material",
            material_id=line_item.material_id,
            purchase_order_id=po_id,
            po_line_item_id=line_item.id,
            quantity=50.0,
            unit_of_measure="kg",
            lifecycle_status=MaterialLifecycleStatus.RECEIVED,
            lot_number="LOT-LIFECYCLE"
        )
        db.add(instance)
        db.commit()
        db.refresh(instance)
        
        # Move to inspection
        response = client.post(
            f"/api/v1/material-instances/{instance.id}/status",
            json={"status": "in_inspection"},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        db.refresh(instance)
        assert instance.lifecycle_status == MaterialLifecycleStatus.IN_INSPECTION
        
        # Move to storage
        response = client.post(
            f"/api/v1/material-instances/{instance.id}/status",
            json={"status": "in_storage"},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        db.refresh(instance)
        assert instance.lifecycle_status == MaterialLifecycleStatus.IN_STORAGE
        
        # Issue to production
        response = client.post(
            f"/api/v1/material-instances/{instance.id}/status",
            json={"status": "issued"},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        db.refresh(instance)
        assert instance.lifecycle_status == MaterialLifecycleStatus.ISSUED
        
        # Move to production
        response = client.post(
            f"/api/v1/material-instances/{instance.id}/status",
            json={"status": "in_production"},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        db.refresh(instance)
        assert instance.lifecycle_status == MaterialLifecycleStatus.IN_PRODUCTION
        
        # Complete
        response = client.post(
            f"/api/v1/material-instances/{instance.id}/status",
            json={"status": "completed"},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        db.refresh(instance)
        assert instance.lifecycle_status == MaterialLifecycleStatus.COMPLETED
        
        # Verify PO reference maintained throughout
        assert instance.purchase_order_id == po_id
        assert instance.po_line_item_id == line_item.id


class TestBarcodeTraceability:
    """Test barcode-based traceability."""
    
    def test_barcode_links_to_po(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test that barcodes can link materials to PO."""
        po_id = test_po_with_line_items.id
        line_item = db.query(POLineItem).filter(
            POLineItem.purchase_order_id == po_id
        ).first()
        
        # Create barcode for PO line item
        barcode_data = {
            "entity_type": "po_line_item",
            "entity_id": line_item.id,
            "barcode_type": "code128",
            "value": "BC-PO-001"
        }
        
        response = client.post(
            "/api/v1/barcodes/",
            json=barcode_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        barcode_id = response.json()["id"]
        
        # Verify barcode links to PO
        barcode = db.query(BarcodeLabel).filter(BarcodeLabel.id == barcode_id).first()
        assert barcode.entity_type == BarcodeEntityType.PO_LINE_ITEM
        assert barcode.entity_id == line_item.id
    
    def test_scan_barcode_traces_to_po(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test scanning a barcode traces back to PO."""
        po_id = test_po_with_line_items.id
        line_item = db.query(POLineItem).filter(
            POLineItem.purchase_order_id == po_id
        ).first()
        
        # Create barcode
        barcode = BarcodeLabel(
            entity_type=BarcodeEntityType.PO_LINE_ITEM,
            entity_id=line_item.id,
            barcode_type="code128",
            value="BC-SCAN-001"
        )
        db.add(barcode)
        db.commit()
        db.refresh(barcode)
        
        # Scan barcode
        response = client.post(
            "/api/v1/barcodes/scan",
            json={"barcode_value": "BC-SCAN-001"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["entity_type"] == "po_line_item"
        assert data["entity_id"] == line_item.id
        
        # Verify PO information in response
        assert "purchase_order" in data or "po_reference" in str(data)
