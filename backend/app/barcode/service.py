from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from app.barcode import repository
from app.data.models.product_model import ProductModel


class BarcodeEngineError(Exception):
    pass


class BarcodeService:
    """High-level barcode detection and decoding service.

    Uses multiple backends to decode 1D/2D barcodes and returns structured results.
    """

    def __init__(self, db_session):
        self.db = db_session
        self.repo = repository.SQLAlchemyBarcodeRepository(self.db)

    def _preprocess(self, image: Any) -> Any:
        import cv2
        # local import to avoid heavy import-time dependency
        np = __import__("numpy")
        # grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # CLAHE contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        # denoise
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        return gray

    def _find_candidate_regions(self, gray: Any) -> List[Tuple[int, int, int, int]]:
        import cv2
        np = __import__("numpy")
        # Sobel gradient and morphological ops to find rectangular barcode-like contours
        gradX = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=3)
        gradY = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=0, dy=1, ksize=3)
        grad = cv2.subtract(np.abs(gradX), np.abs(gradY))
        grad = cv2.convertScaleAbs(grad)
        blurred = cv2.GaussianBlur(grad, (9, 9), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        closed = cv2.erode(closed, None, iterations=4)
        closed = cv2.dilate(closed, None, iterations=4)
        contours, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        rects = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if w > 30 and h > 10:
                rects.append((x, y, w, h))
        return rects

    def _crop_region(self, image: Any, rect: Tuple[int, int, int, int]) -> Any:
        x, y, w, h = rect
        pad = int(0.1 * max(w, h))
        x0 = max(0, x - pad)
        y0 = max(0, y - pad)
        x1 = min(image.shape[1], x + w + pad)
        y1 = min(image.shape[0], y + h + pad)
        return image[y0:y1, x0:x1]

    def _decode_region(self, region: Any) -> List[Dict[str, Any]]:
        results = []
        # Try pyzbar
        try:
            from pyzbar import pyzbar
            decoded = pyzbar.decode(region)
            for d in decoded:
                val = d.data.decode("utf-8")
                typ = d.type
                results.append({"value": val, "type": typ, "confidence": None})
        except Exception:
            pass

        # Try pylibdmtx for DataMatrix
        try:
            from pylibdmtx.pylibdmtx import decode as dmtx_decode
            d2 = dmtx_decode(region)
            for d in d2:
                val = d.data.decode("utf-8")
                results.append({"value": val, "type": "DATAMATRIX", "confidence": None})
        except Exception:
            pass

        return results

    def _validate_checksum(self, value: str) -> bool:
        # Basic EAN-13 / UPC-A checksum validation
        if len(value) == 13 and value.isdigit():
            digits = list(map(int, value))
            check = digits[-1]
            s = sum(digits[i] for i in range(0, 12, 2)) + 3 * sum(digits[i] for i in range(1, 12, 2))
            calc = (10 - (s % 10)) % 10
            return calc == check
        if len(value) == 12 and value.isdigit():
            # UPC-A
            digits = list(map(int, value))
            check = digits[-1]
            s = 3 * sum(digits[i] for i in range(0, 11, 2)) + sum(digits[i] for i in range(1, 11, 2))
            calc = (10 - (s % 10)) % 10
            return calc == check
        return True

    def lookup_catalog(self, barcode_value: str) -> Optional[dict]:
        # Read-only lookup in product catalog
        prod = self.db.query(ProductModel).filter(ProductModel.barcode == barcode_value).first()
        if not prod:
            return None
        return {"product_id": prod.id, "sku": prod.sku, "name": prod.name, "brand_id": prod.brand_id}

    def analyze_image_file(self, image_path: str, scanned_by_id: Optional[int] = None) -> Dict[str, Any]:
        img = cv2.imread(image_path)
        if img is None:
            raise BarcodeEngineError("Failed to load image")
        scan = self.repo.create_scan(source=image_path, scanned_by_id=scanned_by_id)
        detections = self.process_frame(scan.id, img)
        return {"scan_id": scan.id, "detections": detections}

    def process_frame(self, scan_id: int, frame: Any, scanned_by_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Process a single frame (numpy array). Returns list of detections and persists results to DB.

        This method is optimized for streaming scenarios where many frames are processed.
        """
        # local imports
        import cv2
        np = __import__("numpy")

        gray = self._preprocess(frame)
        rects = self._find_candidate_regions(gray)
        detections = []
        for r in rects:
            region = self._crop_region(frame, r)
            decs = self._decode_region(region)
            for d in decs:
                value = d["value"]
                typ = d.get("type")
                conf = d.get("confidence")
                valid = self._validate_checksum(value)
                product = self.lookup_catalog(value)
                if not product:
                    self.repo.queue_unknown(value, scan_id, metadata={"bbox": {"x": r[0], "y": r[1], "w": r[2], "h": r[3]}})
                res = self.repo.add_result(scan_id, value, None, conf, {"x": r[0], "y": r[1], "w": r[2], "h": r[3]}, 0.0)
                detections.append({"value": value, "type": typ, "confidence": conf, "bbox": {"x": r[0], "y": r[1], "w": r[2], "h": r[3]}, "valid": valid, "product": product})

        return detections
