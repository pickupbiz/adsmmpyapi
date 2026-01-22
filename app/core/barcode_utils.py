"""
Barcode generation utilities with PO integration.

Supports:
- Code128 barcode generation
- QR code generation with embedded material/PO data
- Unique barcode value generation
- Traceability data encoding
"""
import json
import base64
import hashlib
from datetime import date, datetime
from typing import Optional, Dict, Any, List
from io import BytesIO

# These will be conditionally imported
try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_M
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

try:
    from barcode import Code128, Code39
    from barcode.writer import ImageWriter, SVGWriter
    HAS_BARCODE = True
except ImportError:
    HAS_BARCODE = False


class BarcodeGenerator:
    """
    Utility class for generating barcodes with PO integration.
    
    Barcode Format: {PREFIX}-{TYPE}-{DATE}-{SEQUENCE}
    Example: RM-PO2026001-240123-00001 (Raw Material from PO)
    """
    
    # Prefixes for different entity types
    PREFIXES = {
        "raw_material": "RM",
        "wip": "WIP",
        "finished_goods": "FG",
        "material_instance": "MI",
        "po_line_item": "POL",
        "grn_line_item": "GRN",
        "inventory": "INV",
        "part": "PRT",
    }
    
    @classmethod
    def generate_barcode_value(
        cls,
        entity_type: str,
        po_number: Optional[str] = None,
        material_id: Optional[int] = None,
        lot_number: Optional[str] = None,
        sequence: int = 1,
        include_date: bool = True
    ) -> str:
        """
        Generate a unique barcode value with PO reference.
        
        Format: {PREFIX}-{PO_REF}-{DATE}-{SEQ}
        Example: RM-PO2026001-240123-00001
        """
        parts = []
        
        # Prefix based on entity type
        prefix = cls.PREFIXES.get(entity_type, "BC")
        parts.append(prefix)
        
        # PO reference (shortened)
        if po_number:
            # Extract key part of PO number (e.g., "PO-2026-001" -> "2026001")
            po_ref = po_number.replace("-", "").replace("PO", "")[:10]
            parts.append(f"PO{po_ref}")
        elif material_id:
            parts.append(f"M{material_id}")
        
        # Date component
        if include_date:
            date_str = datetime.now().strftime("%y%m%d")
            parts.append(date_str)
        
        # Lot number (shortened if provided)
        if lot_number:
            lot_ref = lot_number[:8].replace("-", "")
            parts.append(lot_ref)
        
        # Sequence number with padding
        parts.append(f"{sequence:05d}")
        
        return "-".join(parts)
    
    @classmethod
    def generate_unique_id(
        cls,
        entity_type: str,
        entity_id: int,
        timestamp: Optional[datetime] = None
    ) -> str:
        """Generate a unique hash-based ID for deduplication."""
        ts = timestamp or datetime.utcnow()
        data = f"{entity_type}:{entity_id}:{ts.isoformat()}"
        hash_value = hashlib.md5(data.encode()).hexdigest()[:8].upper()
        return hash_value
    
    @classmethod
    def generate_qr_data(
        cls,
        barcode_value: str,
        po_number: Optional[str] = None,
        material_part_number: Optional[str] = None,
        material_name: Optional[str] = None,
        specification: Optional[str] = None,
        lot_number: Optional[str] = None,
        batch_number: Optional[str] = None,
        heat_number: Optional[str] = None,
        quantity: Optional[float] = None,
        unit_of_measure: Optional[str] = None,
        supplier_name: Optional[str] = None,
        manufacture_date: Optional[date] = None,
        expiry_date: Optional[date] = None,
        traceability_stage: Optional[str] = None,
        parent_barcode: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate structured QR data for mobile scanning.
        
        Returns a dictionary that can be JSON-encoded into a QR code.
        """
        qr_data = {
            "v": 1,  # Version for future compatibility
            "bc": barcode_value,
            "ts": datetime.utcnow().isoformat(),
        }
        
        # PO Reference
        if po_number:
            qr_data["po"] = po_number
        
        # Material Details
        if material_part_number:
            qr_data["pn"] = material_part_number
        if material_name:
            qr_data["name"] = material_name[:50]  # Truncate for QR size
        if specification:
            qr_data["spec"] = specification
        
        # Traceability
        if lot_number:
            qr_data["lot"] = lot_number
        if batch_number:
            qr_data["batch"] = batch_number
        if heat_number:
            qr_data["heat"] = heat_number
        
        # Quantity
        if quantity is not None:
            qr_data["qty"] = quantity
        if unit_of_measure:
            qr_data["uom"] = unit_of_measure
        
        # Supplier
        if supplier_name:
            qr_data["supplier"] = supplier_name[:30]
        
        # Dates
        if manufacture_date:
            qr_data["mfg"] = manufacture_date.isoformat()
        if expiry_date:
            qr_data["exp"] = expiry_date.isoformat()
        
        # Stage
        if traceability_stage:
            qr_data["stage"] = traceability_stage
        
        # Parent barcode for traceability chain
        if parent_barcode:
            qr_data["parent"] = parent_barcode
        
        # Additional custom data
        if additional_data:
            qr_data["extra"] = additional_data
        
        return qr_data
    
    @classmethod
    def encode_qr_data_compact(cls, qr_data: Dict[str, Any]) -> str:
        """
        Encode QR data to a compact string for smaller QR codes.
        Uses base64 encoding of JSON.
        """
        json_str = json.dumps(qr_data, separators=(',', ':'))
        encoded = base64.b64encode(json_str.encode()).decode()
        return encoded
    
    @classmethod
    def decode_qr_data_compact(cls, encoded_data: str) -> Dict[str, Any]:
        """Decode compact QR data back to dictionary."""
        try:
            json_str = base64.b64decode(encoded_data.encode()).decode()
            return json.loads(json_str)
        except Exception:
            return {}
    
    @classmethod
    def generate_code128_image(
        cls,
        barcode_value: str,
        output_format: str = "png",
        module_width: float = 0.2,
        module_height: float = 15.0,
        text: bool = True
    ) -> Optional[bytes]:
        """
        Generate Code128 barcode image.
        
        Args:
            barcode_value: The barcode value to encode
            output_format: 'png' or 'svg'
            module_width: Width of barcode modules in mm
            module_height: Height of barcode in mm
            text: Whether to include human-readable text
        
        Returns:
            Bytes of the generated image or None if library not available
        """
        if not HAS_BARCODE:
            return None
        
        try:
            writer = ImageWriter() if output_format == "png" else SVGWriter()
            
            # Configure writer options
            writer_options = {
                'module_width': module_width,
                'module_height': module_height,
                'write_text': text,
                'font_size': 10,
                'text_distance': 5.0,
            }
            
            barcode = Code128(barcode_value, writer=writer)
            
            buffer = BytesIO()
            barcode.write(buffer, options=writer_options)
            buffer.seek(0)
            
            return buffer.getvalue()
        except Exception as e:
            print(f"Error generating Code128: {e}")
            return None
    
    @classmethod
    def generate_qr_code_image(
        cls,
        data: str,
        output_format: str = "png",
        box_size: int = 10,
        border: int = 4,
        error_correction: str = "M"
    ) -> Optional[bytes]:
        """
        Generate QR code image.
        
        Args:
            data: Data to encode (JSON string or URL)
            output_format: 'png' or 'svg'
            box_size: Size of each box in pixels
            border: Border size in boxes
            error_correction: 'L', 'M', 'Q', 'H' (7%, 15%, 25%, 30% recovery)
        
        Returns:
            Bytes of the generated image or None if library not available
        """
        if not HAS_QRCODE:
            return None
        
        try:
            error_levels = {
                'L': qrcode.constants.ERROR_CORRECT_L,
                'M': qrcode.constants.ERROR_CORRECT_M,
                'Q': qrcode.constants.ERROR_CORRECT_Q,
                'H': qrcode.constants.ERROR_CORRECT_H,
            }
            
            qr = qrcode.QRCode(
                version=None,  # Auto-determine
                error_correction=error_levels.get(error_correction, ERROR_CORRECT_M),
                box_size=box_size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format=output_format.upper())
            buffer.seek(0)
            
            return buffer.getvalue()
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return None
    
    @classmethod
    def generate_material_barcode_with_qr(
        cls,
        barcode_value: str,
        qr_data: Dict[str, Any],
        output_format: str = "png"
    ) -> Dict[str, Optional[bytes]]:
        """
        Generate both Code128 barcode and QR code for a material.
        
        Returns:
            Dictionary with 'barcode' and 'qr_code' image bytes
        """
        result = {
            'barcode': None,
            'qr_code': None,
            'qr_data_encoded': None,
        }
        
        # Generate Code128
        result['barcode'] = cls.generate_code128_image(
            barcode_value, 
            output_format=output_format
        )
        
        # Generate QR code with embedded data
        qr_json = json.dumps(qr_data, separators=(',', ':'))
        result['qr_code'] = cls.generate_qr_code_image(
            qr_json,
            output_format=output_format
        )
        
        # Also provide encoded data for storage
        result['qr_data_encoded'] = cls.encode_qr_data_compact(qr_data)
        
        return result


class BarcodeValidator:
    """Utility class for validating barcodes against PO and material details."""
    
    @classmethod
    def validate_barcode_format(cls, barcode_value: str) -> Dict[str, Any]:
        """
        Validate barcode format and extract components.
        
        Returns:
            Dictionary with validation result and extracted components
        """
        result = {
            'is_valid': False,
            'prefix': None,
            'entity_type': None,
            'po_reference': None,
            'date': None,
            'sequence': None,
            'errors': []
        }
        
        if not barcode_value:
            result['errors'].append("Barcode value is empty")
            return result
        
        parts = barcode_value.split('-')
        if len(parts) < 2:
            result['errors'].append("Invalid barcode format")
            return result
        
        # Extract prefix
        result['prefix'] = parts[0]
        
        # Map prefix to entity type
        prefix_map = {v: k for k, v in BarcodeGenerator.PREFIXES.items()}
        result['entity_type'] = prefix_map.get(parts[0])
        
        # Extract PO reference if present
        for part in parts[1:]:
            if part.startswith('PO'):
                result['po_reference'] = part
            elif len(part) == 6 and part.isdigit():
                result['date'] = part
            elif part.isdigit() and len(part) >= 4:
                result['sequence'] = int(part)
        
        result['is_valid'] = True
        return result
    
    @classmethod
    def validate_against_po(
        cls,
        barcode_data: Dict[str, Any],
        po_number: str,
        material_id: int,
        expected_quantity: float
    ) -> Dict[str, Any]:
        """
        Validate barcode data against PO details.
        
        Returns:
            Dictionary with validation results
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'checks': {}
        }
        
        # Check PO match
        if barcode_data.get('po') != po_number:
            result['errors'].append(f"PO mismatch: expected {po_number}, got {barcode_data.get('po')}")
            result['is_valid'] = False
        result['checks']['po_match'] = barcode_data.get('po') == po_number
        
        # Check quantity
        bc_qty = barcode_data.get('qty')
        if bc_qty is not None:
            if bc_qty > expected_quantity:
                result['warnings'].append(f"Quantity {bc_qty} exceeds expected {expected_quantity}")
            result['checks']['quantity_valid'] = bc_qty <= expected_quantity
        
        # Check expiry
        exp_date = barcode_data.get('exp')
        if exp_date:
            try:
                expiry = date.fromisoformat(exp_date)
                if expiry < date.today():
                    result['errors'].append("Material has expired")
                    result['is_valid'] = False
                result['checks']['not_expired'] = expiry >= date.today()
            except ValueError:
                result['warnings'].append("Could not parse expiry date")
        
        return result
    
    @classmethod
    def decode_and_validate_qr(cls, qr_data_string: str) -> Dict[str, Any]:
        """
        Decode QR data string and validate structure.
        
        Supports both JSON and base64-encoded JSON.
        """
        result = {
            'is_valid': False,
            'data': None,
            'errors': []
        }
        
        # Try direct JSON first
        try:
            data = json.loads(qr_data_string)
            result['data'] = data
            result['is_valid'] = True
            return result
        except json.JSONDecodeError:
            pass
        
        # Try base64 encoded
        try:
            data = BarcodeGenerator.decode_qr_data_compact(qr_data_string)
            if data:
                result['data'] = data
                result['is_valid'] = True
                return result
        except Exception:
            pass
        
        result['errors'].append("Could not decode QR data")
        return result


def generate_po_receipt_barcode(
    po_number: str,
    po_line_item_id: int,
    material_id: int,
    material_part_number: str,
    material_name: str,
    specification: Optional[str],
    lot_number: Optional[str],
    batch_number: Optional[str],
    heat_number: Optional[str],
    quantity: float,
    unit_of_measure: str,
    supplier_name: Optional[str],
    manufacture_date: Optional[date],
    expiry_date: Optional[date],
    sequence: int = 1
) -> Dict[str, Any]:
    """
    Convenience function to generate a complete barcode package for PO receipt.
    
    Returns:
        Dictionary containing:
        - barcode_value: The unique barcode string
        - qr_data: Structured QR data dictionary
        - barcode_image: Code128 image bytes (if library available)
        - qr_image: QR code image bytes (if library available)
    """
    # Generate barcode value
    barcode_value = BarcodeGenerator.generate_barcode_value(
        entity_type="raw_material",
        po_number=po_number,
        material_id=material_id,
        lot_number=lot_number,
        sequence=sequence
    )
    
    # Generate QR data
    qr_data = BarcodeGenerator.generate_qr_data(
        barcode_value=barcode_value,
        po_number=po_number,
        material_part_number=material_part_number,
        material_name=material_name,
        specification=specification,
        lot_number=lot_number,
        batch_number=batch_number,
        heat_number=heat_number,
        quantity=quantity,
        unit_of_measure=unit_of_measure,
        supplier_name=supplier_name,
        manufacture_date=manufacture_date,
        expiry_date=expiry_date,
        traceability_stage="received"
    )
    
    # Generate images
    images = BarcodeGenerator.generate_material_barcode_with_qr(
        barcode_value=barcode_value,
        qr_data=qr_data
    )
    
    return {
        'barcode_value': barcode_value,
        'qr_data': qr_data,
        'barcode_image': images.get('barcode'),
        'qr_image': images.get('qr_code'),
        'qr_data_encoded': images.get('qr_data_encoded'),
    }


def generate_wip_barcode(
    parent_barcode: str,
    work_order_reference: str,
    quantity_used: float,
    unit_of_measure: str,
    original_qr_data: Dict[str, Any],
    sequence: int = 1
) -> Dict[str, Any]:
    """
    Generate a WIP barcode linked to raw material barcode for traceability.
    """
    barcode_value = BarcodeGenerator.generate_barcode_value(
        entity_type="wip",
        lot_number=original_qr_data.get('lot'),
        sequence=sequence
    )
    
    qr_data = BarcodeGenerator.generate_qr_data(
        barcode_value=barcode_value,
        po_number=original_qr_data.get('po'),
        material_part_number=original_qr_data.get('pn'),
        material_name=original_qr_data.get('name'),
        specification=original_qr_data.get('spec'),
        lot_number=original_qr_data.get('lot'),
        heat_number=original_qr_data.get('heat'),
        quantity=quantity_used,
        unit_of_measure=unit_of_measure,
        traceability_stage="in_production",
        parent_barcode=parent_barcode,
        additional_data={'wo': work_order_reference}
    )
    
    images = BarcodeGenerator.generate_material_barcode_with_qr(
        barcode_value=barcode_value,
        qr_data=qr_data
    )
    
    return {
        'barcode_value': barcode_value,
        'qr_data': qr_data,
        'parent_barcode': parent_barcode,
        'barcode_image': images.get('barcode'),
        'qr_image': images.get('qr_code'),
    }


def generate_finished_goods_barcode(
    parent_barcodes: List[str],
    part_number: str,
    part_name: str,
    serial_number: str,
    work_order_reference: str,
    sequence: int = 1
) -> Dict[str, Any]:
    """
    Generate a finished goods barcode with full traceability to source materials.
    """
    barcode_value = BarcodeGenerator.generate_barcode_value(
        entity_type="finished_goods",
        lot_number=serial_number,
        sequence=sequence
    )
    
    qr_data = {
        'v': 1,
        'bc': barcode_value,
        'ts': datetime.utcnow().isoformat(),
        'pn': part_number,
        'name': part_name,
        'sn': serial_number,
        'stage': 'completed',
        'wo': work_order_reference,
        'materials': parent_barcodes,  # Full traceability chain
    }
    
    images = BarcodeGenerator.generate_material_barcode_with_qr(
        barcode_value=barcode_value,
        qr_data=qr_data
    )
    
    return {
        'barcode_value': barcode_value,
        'qr_data': qr_data,
        'parent_barcodes': parent_barcodes,
        'barcode_image': images.get('barcode'),
        'qr_image': images.get('qr_code'),
    }
