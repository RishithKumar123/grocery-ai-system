import re
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import numpy as np
import cv2
from app.core.config import settings
from app.core.logging import logger

try:
    from paddleocr import PaddleOCR
    HAS_PADDLEOCR = True
except ImportError:
    HAS_PADDLEOCR = False
    logger.warning("paddleocr package is missing or not installed.")


class PaddleOCREngine:
    """
    PaddleOCR-based text extraction for product verification.
    
    Extracts:
    - Brand
    - Product Name
    - Weight
    - MRP
    - Manufacturing Date
    - Expiry Date
    - Batch Number
    """
    
    def __init__(self, use_gpu: bool = True, lang: str = 'en'):
        self.use_gpu = use_gpu
        self.lang = lang
        self.ocr = None
        
        if HAS_PADDLEOCR:
            try:
                # Initialize PaddleOCR
                # use_angle_cls=True for rotated text detection
                # lang='en' for English, can be 'ch' for Chinese, etc.
                self.ocr = PaddleOCR(
                    use_angle_cls=True, 
                    lang=lang, 
                    use_gpu=use_gpu,
                    show_log=False
                )
                logger.info(f"PaddleOCREngine: Initialized successfully (GPU={use_gpu}, lang={lang})")
            except Exception as e:
                logger.error(f"PaddleOCREngine: Failed to initialize: {str(e)}")
                self.ocr = None
        else:
            logger.info("PaddleOCREngine: Not loaded (package missing).")
    
    def extract_text(self, img_np: np.ndarray) -> List[Dict[str, Any]]:
        """
        Extract text from image with bounding boxes and confidence scores.
        
        Returns list of dicts with:
        - text: str
        - bbox: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        - confidence: float
        """
        if self.ocr is None:
            logger.warning("PaddleOCREngine: OCR not initialized")
            return []
        
        try:
            result = self.ocr.ocr(img_np, cls=True)
            
            if not result or not result[0]:
                return []
            
            text_results = []
            for line in result[0]:
                if line:
                    bbox = line[0]
                    text_info = line[1]
                    text = text_info[0]
                    confidence = text_info[1]
                    
                    text_results.append({
                        "text": text,
                        "bbox": bbox,
                        "confidence": confidence
                    })
            
            logger.debug(f"PaddleOCREngine: Extracted {len(text_results)} text lines")
            return text_results
            
        except Exception as e:
            logger.error(f"PaddleOCREngine: Error extracting text: {str(e)}")
            return []
    
    def parse_product_details(self, text_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse extracted text to identify product details.
        
        Returns:
        {
            "product_name": str,
            "brand": str,
            "mrp": float,
            "weight": str,
            "expiry_date": str,
            "mfg_date": str,
            "batch_no": str,
            "variant": str
        }
        """
        details = {
            "product_name": None,
            "brand": None,
            "mrp": None,
            "weight": None,
            "expiry_date": None,
            "mfg_date": None,
            "batch_no": None,
            "variant": None
        }
        
        # Combine all text for analysis
        all_text = " ".join([item["text"] for item in text_results])
        text_upper = all_text.upper()
        
        # Date patterns
        date_patterns = [
            r"(\d{4})[-/](\d{2})[-/](\d{2})",  # YYYY-MM-DD
            r"(\d{2})[-/](\d{2})[-/](\d{4})",  # DD-MM-YYYY or MM-DD-YYYY
            r"(\d{2})[-/](\d{2})[-/](\d{2})",  # DD-MM-YY
            r"(\d{2})[-/](\d{4})",             # MM/YYYY
        ]
        
        # Parse each text line
        for item in text_results:
            text = item["text"].strip()
            text_upper_line = text.upper()
            
            # 1. Parse MRP
            mrp_match = re.search(r"(?:MRP|PRICE|RS\.?|M\.R\.P\.?|₹|INR)\s*:?\s*(\d+(?:\.\d{2})?)", text_upper_line)
            if mrp_match and not details["mrp"]:
                try:
                    details["mrp"] = float(mrp_match.group(1))
                except ValueError:
                    pass
            
            # 2. Parse Weight
            weight_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:G|KG|ML|L|OZ|GM|LTR)\b", text_upper_line)
            if weight_match and not details["weight"]:
                details["weight"] = text.strip()
            
            # 3. Parse Batch Number
            batch_match = re.search(r"(?:BATCH|B\.?NO\.?|LOT|B\.?\s*NO|BATCH\s*NO)\s*:?\s*([A-Z0-9\-]+)", text_upper_line)
            if batch_match and not details["batch_no"]:
                details["batch_no"] = batch_match.group(1)
            
            # 4. Parse Expiry Date
            if any(indicator in text_upper_line for indicator in ["EXP", "EXPIRY", "USEBY", "BESTBEFORE", "BB", "EXP.DATE", "BEST BEFORE"]):
                for pattern in date_patterns:
                    match = re.search(pattern, text_upper_line)
                    if match and not details["expiry_date"]:
                        details["expiry_date"] = text.strip()
                        break
            
            # 5. Parse Manufacturing Date
            if any(indicator in text_upper_line for indicator in ["MFG", "MFD", "PACKED", "PKD", "MFG.DATE", "MFD.DATE", "MANUFACTURED"]):
                for pattern in date_patterns:
                    match = re.search(pattern, text_upper_line)
                    if match and not details["mfg_date"]:
                        details["mfg_date"] = text.strip()
                        break
            
            # 6. Parse Brand (common brand names)
            common_brands = [
                "PATANJALI", "TATA", "AMUL", "NESTLE", "HUL", "ITC", 
                "BRITANNIA", "PARLE", "CADBURY", "KELLOGG'S", "SURF EXCEL",
                "RIN", "ARIEL", "GILLETTE", "COLGATE", "PEPSODENT",
                "DOVE", "LUX", "SUNSILK", "CLINIC PLUS", "HEAD & SHOULDERS"
            ]
            for brand in common_brands:
                if brand in text_upper_line and not details["brand"]:
                    details["brand"] = brand
                    break
        
        # 7. Parse Product Name (longest alphabetic text that's not a date/price/weight)
        for item in text_results:
            text = item["text"].strip()
            if len(text) < 4:
                continue
            
            text_upper_line = text.upper()
            
            # Skip if it's clearly a price, date, weight, or batch
            is_excluded = any(x in text_upper_line for x in [
                "EXP", "MFG", "MFD", "BATCH", "B.NO", "LOT", 
                "PRICE", "MRP", "RS", "₹", "INR", "BEST BEFORE"
            ])
            
            # Skip if it's mostly numbers
            has_digits = sum(c.isdigit() for c in text) / len(text) > 0.3
            
            if not is_excluded and not has_digits and not details["product_name"]:
                # Prefer longer text for product name
                if len(text) > 5:
                    details["product_name"] = text
                    break
        
        # Fallback: use first non-excluded text
        if not details["product_name"] and text_results:
            for item in text_results:
                text = item["text"].strip()
                text_upper_line = text.upper()
                is_excluded = any(x in text_upper_line for x in [
                    "EXP", "MFG", "MFD", "BATCH", "B.NO", "LOT", 
                    "PRICE", "MRP", "RS", "₹", "INR"
                ])
                if not is_excluded and len(text) > 3:
                    details["product_name"] = text
                    break
        
        # 8. Parse Variant (often in parentheses or after product name)
        if details["product_name"]:
            variant_match = re.search(r"\(([^)]+)\)", details["product_name"])
            if variant_match:
                details["variant"] = variant_match.group(1)
                # Remove variant from product name
                details["product_name"] = re.sub(r"\s*\([^)]+\)", "", details["product_name"]).strip()
        
        return details
    
    def parse_expiry_date(self, text_results: List[Dict[str, Any]]) -> Optional[date]:
        """
        Parse expiry date from OCR results.
        """
        date_patterns = [
            r"(\d{4})[-/](\d{2})[-/](\d{2})",  # YYYY-MM-DD
            r"(\d{2})[-/](\d{2})[-/](\d{4})",  # DD-MM-YYYY or MM-DD-YYYY
            r"(\d{2})[-/](\d{2})[-/](\d{2})",  # DD-MM-YY
        ]
        
        for item in text_results:
            text = item["text"].upper()
            # Look for expiry indicators
            if any(indicator in text for indicator in ["EXP", "EXPIRY", "USEBY", "BESTBEFORE", "BB"]):
                for pattern in date_patterns:
                    match = re.search(pattern, text)
                    if match:
                        groups = match.groups()
                        try:
                            if len(groups[0]) == 4:  # YYYY-MM-DD
                                return datetime.strptime(f"{groups[0]}-{groups[1]}-{groups[2]}", "%Y-%m-%d").date()
                            elif len(groups[2]) == 4:  # DD/MM/YYYY
                                day_or_month_1 = int(groups[0])
                                day_or_month_2 = int(groups[1])
                                year = int(groups[2])
                                if day_or_month_1 > 12:  # DD/MM/YYYY
                                    return date(year, day_or_month_2, day_or_month_1)
                                else:  # Assume MM/DD/YYYY
                                    return date(year, day_or_month_1, day_or_month_2)
                        except ValueError:
                            continue
        return None
    
    def get_text_lines(self, text_results: List[Dict[str, Any]]) -> List[str]:
        """Extract just the text lines from results."""
        return [item["text"] for item in text_results]
