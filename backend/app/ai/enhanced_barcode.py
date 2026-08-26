import cv2
import numpy as np
from typing import List, Dict, Any, Optional
from app.core.logging import logger
from sqlalchemy.orm import Session
from app.data.models.product_model import ProductModel

try:
    from pyzbar import pyzbar
    HAS_PYZBAR = True
except Exception:
    HAS_PYZBAR = False
    logger.warning("pyzbar package or libzbar-64.dll is missing or not installed.")

try:
    import zxing
    HAS_ZXING = True
except ImportError:
    HAS_ZXING = False
    logger.warning("zxing package is missing or not installed.")


class EnhancedBarcodeReader:
    """
    Enhanced barcode reader supporting multiple barcode types.
    
    Supports:
    - EAN-13
    - EAN-8
    - UPC-A
    - UPC-E
    - Code 128
    - Code 39
    - QR Code
    - Data Matrix
    - PDF417
    
    Uses pyzbar as primary (fast, Python-native)
    Falls back to zxing if needed (Java-based, more comprehensive)
    """
    
    def __init__(self):
        self.has_pyzbar = HAS_PYZBAR
        self.has_zxing = HAS_ZXING
        self.zxing_reader = None
        
        if self.has_zxing:
            try:
                self.zxing_reader = zxing.BarCodeReader()
                logger.info("EnhancedBarcodeReader: ZXing reader initialized")
            except Exception as e:
                logger.error(f"EnhancedBarcodeReader: Failed to initialize ZXing: {str(e)}")
                self.has_zxing = False
        
        if self.has_pyzbar:
            logger.info("EnhancedBarcodeReader: pyzbar available")
        else:
            logger.warning("EnhancedBarcodeReader: pyzbar not available")
    
    def read_barcodes(
        self, 
        img: np.ndarray, 
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Read barcodes from image using available readers.
        
        Returns list of barcode results with:
        - barcode: str (decoded value)
        - type: str (barcode type)
        - box: [xmin, ymin, xmax, ymax]
        - product_id: Optional[int]
        - product_name: Optional[str]
        - confidence: float
        """
        results = []
        
        # Try pyzbar first (faster)
        if self.has_pyzbar:
            pyzbar_results = self._read_with_pyzbar(img)
            results.extend(pyzbar_results)
        
        # If no results and zxing available, try it
        if not results and self.has_zxing:
            zxing_results = self._read_with_zxing(img)
            results.extend(zxing_results)
        
        # Resolve product information from database
        if db:
            for result in results:
                product = self._resolve_product(result["barcode"], db)
                if product:
                    result["product_id"] = product.id
                    result["product_name"] = product.name
                    result["sku"] = product.sku
                    result["brand"] = product.brand
                    result["confidence"] = 1.0  # Barcode match is 100% confident
                else:
                    result["product_id"] = None
                    result["product_name"] = f"Unknown Product ({result['barcode']})"
                    result["confidence"] = 0.0
        
        logger.info(f"EnhancedBarcodeReader: Read {len(results)} barcodes")
        return results
    
    def _read_with_pyzbar(self, img: np.ndarray) -> List[Dict[str, Any]]:
        """Read barcodes using pyzbar."""
        results = []
        
        try:
            # pyzbar requires grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            barcodes = pyzbar.decode(gray)
            
            for barcode in barcodes:
                # Get barcode data
                barcode_data = barcode.data.decode('utf-8')
                barcode_type = barcode.type
                
                # Get bounding box
                points = barcode.polygon
                if len(points) == 4:
                    xmin = min(p[0] for p in points)
                    ymin = min(p[1] for p in points)
                    xmax = max(p[0] for p in points)
                    ymax = max(p[1] for p in points)
                    
                    results.append({
                        "barcode": barcode_data,
                        "type": barcode_type,
                        "box": [int(xmin), int(ymin), int(xmax), int(ymax)],
                        "reader": "pyzbar"
                    })
        
        except Exception as e:
            logger.error(f"EnhancedBarcodeReader: pyzbar error: {str(e)}")
        
        return results
    
    def _read_with_zxing(self, img: np.ndarray) -> List[Dict[str, Any]]:
        """Read barcodes using zxing (Java-based)."""
        results = []
        
        if not self.zxing_reader:
            return results
        
        try:
            # Save image to temp file for zxing
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                temp_path = tmp.name
                cv2.imwrite(temp_path, img)
            
            try:
                # Read with zxing
                barcodes = self.zxing_reader.decode(temp_path)
                
                if barcodes:
                    for barcode in barcodes:
                        results.append({
                            "barcode": barcode.parsed,
                            "type": barcode.format,
                            "box": [0, 0, 0, 0],  # zxing doesn't provide bbox
                            "reader": "zxing"
                        })
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        except Exception as e:
            logger.error(f"EnhancedBarcodeReader: zxing error: {str(e)}")
        
        return results
    
    def _resolve_product(self, barcode: str, db: Session) -> Optional[ProductModel]:
        """Resolve barcode to product from database."""
        try:
            product = db.query(ProductModel).filter(
                ProductModel.barcode == barcode
            ).first()
            return product
        except Exception as e:
            logger.error(f"EnhancedBarcodeReader: Error resolving product: {str(e)}")
            return None
    
    def read_single_barcode(
        self, 
        img: np.ndarray, 
        db: Optional[Session] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Read a single barcode from image.
        Returns the first barcode found or None.
        """
        results = self.read_barcodes(img, db)
        return results[0] if results else None
    
    def is_barcode_match(
        self, 
        img: np.ndarray, 
        target_barcode: str
    ) -> bool:
        """
        Check if the image contains a specific barcode.
        Returns True if target barcode is found.
        """
        results = self.read_barcodes(img)
        for result in results:
            if result["barcode"] == target_barcode:
                return True
        return False
