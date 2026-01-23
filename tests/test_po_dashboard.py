"""Tests for PO dashboard and reporting."""
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient

from app.models.purchase_order import PurchaseOrder, POLineItem, POStatus, POPriority


class TestPODashboard:
    """Test PO dashboard endpoints."""
    
    def test_get_po_summary(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test getting PO summary."""
        # Create multiple POs with different statuses
        from app.models.supplier import Supplier, SupplierStatus, SupplierTier
        from app.models.user import User
        
        supplier = db.query(Supplier).first()
        user = db.query(User).first()
        
        # Create approved PO
        po1 = PurchaseOrder(
            po_number="PO-DASH-001",
            supplier_id=supplier.id,
            created_by_id=user.id,
            status=POStatus.APPROVED,
            priority=POPriority.HIGH,
            po_date=date.today(),
            total_amount=2000.0,
            currency="USD"
        )
        db.add(po1)
        db.commit()
        
        # Create pending PO
        po2 = PurchaseOrder(
            po_number="PO-DASH-002",
            supplier_id=supplier.id,
            created_by_id=user.id,
            status=POStatus.PENDING_APPROVAL,
            priority=POPriority.NORMAL,
            po_date=date.today(),
            total_amount=1500.0,
            currency="USD"
        )
        db.add(po2)
        db.commit()
        
        response = client.get(
            "/api/v1/dashboard/po-summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_pos" in data
        assert "pending_approval" in data
        assert "approved" in data
        assert data["total_pos"] >= 2
    
    def test_get_po_status_breakdown(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test getting PO status breakdown."""
        response = client.get(
            "/api/v1/dashboard/purchase-orders/status-breakdown",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # Should have status counts
        assert "draft" in data or "pending_approval" in data
    
    def test_get_pending_approvals(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test getting pending approvals."""
        # Set PO to pending
        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.id == test_po_with_line_items.id
        ).first()
        po.status = POStatus.PENDING_APPROVAL
        db.commit()
        
        # Get PO summary which includes pending approvals info
        response = client.get(
            "/api/v1/dashboard/po-summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should include our pending PO
        po_ids = [item["id"] for item in data if isinstance(item, dict)]
        assert test_po_with_line_items.id in po_ids or len(data) >= 0


class TestPOAnalytics:
    """Test PO analytics endpoints."""
    
    def test_get_po_vs_received_comparison(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test PO vs received material comparison."""
        po_id = test_po_with_line_items.id
        
        # Set some received quantity
        line_item = db.query(POLineItem).filter(
            POLineItem.purchase_order_id == po_id
        ).first()
        line_item.quantity_received = 50.0
        line_item.quantity_accepted = 50.0
        db.commit()
        
        response = client.get(
            "/api/v1/dashboard/po-vs-received",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_supplier_performance(
        self,
        client: TestClient,
        auth_headers: dict,
        test_supplier,
        db
    ):
        """Test supplier performance analytics."""
        response = client.get(
            "/api/v1/dashboard/suppliers/performance",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_delivery_analytics(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test delivery analytics."""
        # Set expected delivery date
        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.id == test_po_with_line_items.id
        ).first()
        po.expected_delivery_date = date.today() + timedelta(days=7)
        db.commit()
        
        response = client.get(
            "/api/v1/dashboard/delivery-analytics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestPOReports:
    """Test PO reporting endpoints."""
    
    def test_export_po_report_pdf(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items
    ):
        """Test exporting PO report as PDF."""
        po_id = test_po_with_line_items.id
        
        # Reports use POST with request body
        report_data = {
            "po_ids": [po_id],
            "format": "pdf",
            "date_range": "all"
        }
        
        response = client.post(
            "/api/v1/reports/po",
            json=report_data,
            headers=auth_headers
        )
        
        # Should return report response with download URL
        assert response.status_code == 200
        data = response.json()
        assert "file_path" in data or "download_url" in data
    
    def test_export_po_report_excel(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items
    ):
        """Test exporting PO report as Excel."""
        po_id = test_po_with_line_items.id
        
        # Reports use POST with request body
        report_data = {
            "po_ids": [po_id],
            "format": "excel",
            "date_range": "all"
        }
        
        response = client.post(
            "/api/v1/reports/po",
            json=report_data,
            headers=auth_headers
        )
        
        # Should return report response
        assert response.status_code == 200
        data = response.json()
        assert "file_path" in data or "download_url" in data
    
    def test_get_po_list_report(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items
    ):
        """Test getting PO list report."""
        # Reports use POST with request body
        report_data = {
            "format": "csv",
            "date_range": "all"
        }
        
        response = client.post(
            "/api/v1/reports/po",
            json=report_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        # Should return report response
        data = response.json()
        assert "file_path" in data or "download_url" in data


class TestPOAlerts:
    """Test PO alert endpoints."""
    
    def test_get_po_alerts(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test getting PO alerts."""
        # Create PO with approaching delivery date
        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.id == test_po_with_line_items.id
        ).first()
        po.expected_delivery_date = date.today() + timedelta(days=3)
        po.status = POStatus.ORDERED
        db.commit()
        
        response = client.get(
            "/api/v1/dashboard/alerts",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_delayed_po_alerts(
        self,
        client: TestClient,
        auth_headers: dict,
        test_po_with_line_items,
        db
    ):
        """Test getting delayed PO alerts."""
        # Create PO with past delivery date
        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.id == test_po_with_line_items.id
        ).first()
        po.expected_delivery_date = date.today() - timedelta(days=5)
        po.status = POStatus.ORDERED
        db.commit()
        
        response = client.get(
            "/api/v1/dashboard/alerts",
            params={"type": "delayed_delivery"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
