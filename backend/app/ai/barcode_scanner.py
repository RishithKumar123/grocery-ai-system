import cv2
import numpy as np
from typing import List, Dict, Any, Optional
from app.core.logging import logger
from sqlalchemy.orm import Session
from app.data.models.product_model import ProductModel


class BarcodeScanner:
    def __init__(self):
        try:
            self.barcode_detector = cv2.barcode.BarcodeDetector()
            self.qr_detector = cv2.QRCodeDetector()
            self.has_opencv_detectors = True
            logger.info("BarcodeScanner: OpenCV BarcodeDetector and QRCodeDetector initialized.")
        except Exception as e:
            self.has_opencv_detectors = False
            logger.error(f"BarcodeScanner initialization failed: {str(e)}")

    def scan_image(self, img: np.ndarray, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """
        Scans a frame numpy array for EAN-13, EAN-8, UPC, and QR barcodes.
        Resolves associated product models if a db session is provided.
        """
        results = []

        if self.has_opencv_detectors:
            try:
                # 1. Scan for standard Barcodes (EAN-13, EAN-8, UPC)
                retval_info, retval_type, corners = self.barcode_detector.detectAndDecode(img)
                
                # If corners is not None and matches dimensions
                if corners is not None and len(corners) > 0:
                    # Depending on OpenCV version, decoded_info can be a string or list
                    decoded_info_list = [retval_info] if isinstance(retval_info, str) else list(retval_info)
                    decoded_type_list = [retval_type] if isinstance(retval_type, str) else list(retval_type)
                    
                    for idx, info in enumerate(decoded_info_list):
                        if not info:
                            continue
                        
                        # Get barcode corner bounding box coordinates
                        pts = corners[idx]
                        xmin = int(min(p[0] for p in pts))
                        ymin = int(min(p[1] for p in pts))
                        xmax = int(max(p[0] for p in pts))
                        ymax = int(max(p[1] for p in pts))
                        
                        raw_type = decoded_type_list[idx] if idx < len(decoded_type_list) else "BARCODE"
                        
                        # Normalize type name
                        norm_type = "EAN-13"
                        if "EAN13" in str(raw_type).upper():
                            norm_type = "EAN-13"
                        elif "EAN8" in str(raw_type).upper():
                            norm_type = "EAN-8"
                        elif "UPC" in str(raw_type).upper():
                            norm_type = "UPC"
                        else:
                            norm_type = str(raw_type)

                        results.append({
                            "barcode": info,
                            "type": norm_type,
                            "box": [xmin, ymin, xmax, ymax]
                        })
            except Exception as e:
                logger.error(f"BarcodeScanner: Error during OpenCV Barcode scanning: {str(e)}")

            try:
                # 2. Scan for QR Codes
                retval, decoded_info, corners, _ = self.qr_detector.detectAndDecodeMulti(img)
                if retval and corners is not None:
                    for idx, info in enumerate(decoded_info):
                        if not info:
                            continue
                        
                        pts = corners[idx]
                        xmin = int(min(p[0] for p in pts))
                        ymin = int(min(p[1] for p in pts))
                        xmax = int(max(p[0] for p in pts))
                        ymax = int(max(p[1] for p in pts))

                        results.append({
                            "barcode": info,
                            "type": "QR",
                            "box": [xmin, ymin, xmax, ymax]
                        })
            except Exception as e:
                logger.error(f"BarcodeScanner: Error during OpenCV QR scanning: {str(e)}")

        # --- Automatic Product Identification & Seeding/Catalog lookup ---
        final_results = []
        for item in results:
            barcode_str = item["barcode"]
            barcode_type = item["type"]
            box = item["box"]

            product_id = None
            product_name = f"Unknown Product ({barcode_str})"
            category = "Grocery Products"
            sku = None

            if db:
                # Query product catalog by barcode
                prod = db.query(ProductModel).filter(
                    ProductModel.barcode == barcode_str
                ).first()
                
                if prod:
                    product_id = prod.id
                    product_name = prod.name
                    category = prod.category
                    sku = prod.sku
                    logger.info(f"BarcodeScanner: Identified product '{product_name}' (ID: {product_id}) via barcode '{barcode_str}'")

            final_results.append({
                "barcode": barcode_str,
                "type": barcode_type,
                "box": box,
                "product_id": product_id,
                "product_name": product_name,
                "category": category,
                "sku": sku
            })

        # No fallback demo products. If no barcode is detected, return zero results.
        return final_results
