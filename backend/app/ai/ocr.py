import re
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import numpy as np
import cv2
from app.core.config import settings
from app.core.logging import logger

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False
    logger.warning("easyocr package is missing or not installed.")


class ExpiryOCR:
    def __init__(self):
        self.languages = settings.OCR_LANGUAGES.split(",")
        self.reader = None
        if HAS_EASYOCR:
            try:
                # Initialize reader on GPU if available, fallback to CPU
                import torch
                use_gpu = torch.cuda.is_available()
                self.reader = easyocr.Reader(self.languages, gpu=use_gpu)
                logger.info(f"EasyOCR Reader initialized successfully (GPU={use_gpu}) for languages: {self.languages}")
            except Exception as e:
                logger.error(f"Error initializing EasyOCR Reader: {str(e)}")
        else:
            logger.info("EasyOCR not loaded (package missing). Running in Mock/Dry-Run mode.")

    def extract_text(self, img_np: np.ndarray) -> List[str]:
        """Extracts all text lines found in the image array."""
        if self.reader:
            try:
                results = self.reader.readtext(img_np)
                # results format: [([[x,y], [x,y]...], "text", confidence), ...]
                text_lines = [text for (_, text, _) in results]
                logger.debug(f"EasyOCR extracted lines: {text_lines}")
                return text_lines
            except Exception as e:
                logger.error(f"EasyOCR readtext error: {str(e)}")
                return []
        else:
            # High-end mockup returning diverse text patterns
            import random
            mock_names = ["Premium Oats", "Greek Yogurt", "Diet Cola", "Whole Wheat Bread"]
            mock_weights = ["500g", "1kg", "250ml", "400g"]
            mock_mrps = ["Rs. 120", "MRP: 45.00", "Price: 99.0", "MRP 150.00"]
            mock_dates = ["EXP: 12/2026", "BB: 15/09/2026", "EXPIRY 31/12/2026"]
            mock_mfg = ["MFD 01/2026", "MFG: 10/2025", "PKD 05/2026"]
            mock_batches = ["BATCH B99", "B.No. A412", "LOT: 990"]
            
            return [
                random.choice(mock_names),
                random.choice(mock_weights),
                random.choice(mock_mrps),
                random.choice(mock_dates),
                random.choice(mock_mfg),
                random.choice(mock_batches)
            ]

    def parse_product_details(self, text_list: List[str]) -> Dict[str, Any]:
        """
        Parses extracted OCR text lines to identify:
        Product Name, MRP, Expiry Date, Manufacturing Date, Batch Number, Weight.
        """
        details = {
            "product_name": None,
            "mrp": None,
            "expiry_date": None,
            "mfg_date": None,
            "batch_no": None,
            "weight": None
        }

        # Date regexes
        date_patterns = [
            r"(\d{4})[-/](\d{2})[-/](\d{2})",  # YYYY-MM-DD
            r"(\d{2})[-/](\d{2})[-/](\d{4})",  # DD-MM-YYYY or MM-DD-YYYY
            r"(\d{2})[-/](\d{2})[-/](\d{2})",  # DD-MM-YY
            r"(\d{2})[-/](\d{4})",             # MM/YYYY
        ]

        # Filters for categorization
        for text in text_list:
            text_clean = text.strip()
            text_upper = text_clean.upper().replace(" ", "")

            # 1. Parse MRP
            mrp_match = re.search(r"(?:MRP|PRICE|RS\.?|M\.R\.P\.?)\s*:?\s*(\d+(?:\.\d{2})?)", text_upper)
            if mrp_match and not details["mrp"]:
                try:
                    details["mrp"] = float(mrp_match.group(1))
                except ValueError:
                    pass

            # 2. Parse Weight
            weight_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:G|KG|ML|L|OZ|NET\s*WT)", text_upper)
            if weight_match and not details["weight"]:
                details["weight"] = text_clean

            # 3. Parse Batch Number
            batch_match = re.search(r"(?:BATCH|B\.?NO\.?|LOT|B\.?\s*NO)\s*:?\s*([A-Z0-9\-]+)", text_upper)
            if batch_match and not details["batch_no"]:
                details["batch_no"] = batch_match.group(1)

            # 4. Parse Expiry Date
            if any(indicator in text_upper for indicator in ["EXP", "EXPIRY", "USEBY", "BESTBEFORE", "BB", "EXP.DATE"]):
                for pattern in date_patterns:
                    match = re.search(pattern, text_upper)
                    if match:
                        details["expiry_date"] = text_clean
                        break

            # 5. Parse Manufacturing Date
            if any(indicator in text_upper for indicator in ["MFG", "MFD", "PACKED", "PKD", "MFG.DATE", "MFD.DATE"]):
                for pattern in date_patterns:
                    match = re.search(pattern, text_upper)
                    if match:
                        details["mfg_date"] = text_clean
                        break

        # 6. Parse Product Name
        # If any line contains mostly alphabetic text and is NOT categorized as price, date, weight, batch, etc.
        for text in text_list:
            text_clean = text.strip()
            text_upper = text_clean.upper().replace(" ", "")
            if len(text_clean) < 4:
                continue
            
            # Check exclusions
            is_excluded = any(x in text_upper for x in ["EXP", "MFG", "MFD", "BATCH", "B.NO", "LOT", "PRICE", "MRP", "RS"])
            has_digits = any(char.isdigit() for char in text_clean)
            
            # If it's pure letters and not excluded, select it as the Product Name
            if not is_excluded and not has_digits:
                details["product_name"] = text_clean
                break
        
        # Fallback Product Name if not set
        if not details["product_name"] and len(text_list) > 0:
            details["product_name"] = text_list[0]

        return details

    def parse_expiry_date(self, text_list: List[str]) -> Optional[date]:
        """
        Parses expiry date using standard regex rules from list of strings.
        Example formats: YYYY-MM-DD, DD/MM/YYYY, MM-DD-YYYY
        """
        # Common date patterns
        patterns = [
            r"(\d{4})[-/](\d{2})[-/](\d{2})",  # YYYY-MM-DD
            r"(\d{2})[-/](\d{2})[-/](\d{4})",  # DD-MM-YYYY or MM-DD-YYYY
            r"(\d{2})[-/](\d{2})[-/](\d{2})",  # DD-MM-YY
        ]
        
        for text in text_list:
            text_clean = text.upper().replace(" ", "")
            # Look for indicators like EXP, EXPIRY, BB, BEST BEFORE, B.B.
            for pattern in patterns:
                matches = re.search(pattern, text_clean)
                if matches:
                    groups = matches.groups()
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
