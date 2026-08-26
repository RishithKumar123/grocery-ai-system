import re
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.data.models.product_model import ProductModel


class OCRMatchingEngine:
    """
    OCR-based product matching engine with fuzzy string matching.
    
    Matches extracted OCR text against product database using:
    - Product name matching
    - Brand matching
    - Keyword matching
    - Alias matching
    - Weight/variant matching
    
    Uses fuzzy matching algorithms for robust matching.
    """
    
    def __init__(self):
        self._product_cache = {}
        self._cache_expiry = 300  # 5 minutes
    
    def match_product(
        self,
        ocr_details: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Match OCR extracted details to a product from the database.
        
        Args:
            ocr_details: Dict with product_name, brand, weight, variant, etc.
            db: Database session
        
        Returns:
            {
                "product_id": int or None,
                "product_name": str,
                "brand": str,
                "confidence": float,
                "matching_criteria": str
            }
        """
        # Extract OCR data
        ocr_product_name = ocr_details.get("product_name", "").strip()
        ocr_brand = ocr_details.get("brand", "").strip()
        ocr_weight = ocr_details.get("weight", "").strip()
        ocr_variant = ocr_details.get("variant", "").strip()
        
        if not ocr_product_name:
            return {
                "product_id": None,
                "product_name": "Unknown",
                "brand": "Unknown",
                "confidence": 0.0,
                "matching_criteria": "No OCR text"
            }
        
        # Get all products from database
        products = db.query(ProductModel).all()
        
        if not products:
            return {
                "product_id": None,
                "product_name": ocr_product_name,
                "brand": ocr_brand or "Unknown",
                "confidence": 0.0,
                "matching_criteria": "Empty product catalog"
            }
        
        best_match = None
        best_score = 0.0
        matching_criteria = ""
        
        for product in products:
            score = 0.0
            criteria_parts = []
            
            # 1. Product name similarity (highest weight)
            name_similarity = self._calculate_string_similarity(
                ocr_product_name, 
                product.name
            )
            score += name_similarity * 0.5
            if name_similarity > 0.5:
                criteria_parts.append(f"Name: {name_similarity:.2f}")
            
            # 2. Brand match
            if ocr_brand and product.brand:
                brand_similarity = self._calculate_string_similarity(
                    ocr_brand,
                    product.brand
                )
                if brand_similarity > 0.7:
                    score += 0.2
                    criteria_parts.append(f"Brand: {brand_similarity:.2f}")
            
            # 3. Weight match
            if ocr_weight and product.weight:
                weight_match = self._compare_weights(ocr_weight, product.weight)
                if weight_match:
                    score += 0.1
                    criteria_parts.append("Weight")
            
            # 4. Variant match
            if ocr_variant and product.variant:
                variant_similarity = self._calculate_string_similarity(
                    ocr_variant,
                    product.variant
                )
                if variant_similarity > 0.6:
                    score += 0.1
                    criteria_parts.append(f"Variant: {variant_similarity:.2f}")
            
            # 5. Alias matching
            if product.aliases:
                aliases = json.loads(product.aliases) if isinstance(product.aliases, str) else product.aliases
                if isinstance(aliases, list):
                    for alias in aliases:
                        alias_similarity = self._calculate_string_similarity(
                            ocr_product_name,
                            alias
                        )
                        if alias_similarity > 0.8:
                            score += 0.15
                            criteria_parts.append(f"Alias: {alias}")
                            break
            
            # 6. OCR keywords matching
            if product.ocr_keywords:
                keywords = json.loads(product.ocr_keywords) if isinstance(product.ocr_keywords, str) else product.ocr_keywords
                if isinstance(keywords, list):
                    for keyword in keywords:
                        if keyword.lower() in ocr_product_name.lower():
                            score += 0.05
                            criteria_parts.append(f"Keyword: {keyword}")
            
            # Update best match
            if score > best_score:
                best_score = score
                best_match = product
                matching_criteria = ", ".join(criteria_parts) if criteria_parts else "General similarity"
        
        # Threshold for accepting match
        if best_score >= 0.6 and best_match:
            return {
                "product_id": best_match.id,
                "product_name": best_match.name,
                "brand": best_match.brand or "Unknown",
                "confidence": round(best_score, 2),
                "matching_criteria": matching_criteria
            }
        else:
            return {
                "product_id": None,
                "product_name": ocr_product_name,
                "brand": ocr_brand or "Unknown",
                "confidence": round(best_score, 2) if best_match else 0.0,
                "matching_criteria": "Below threshold"
            }
    
    def _calculate_string_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate similarity between two strings using multiple methods.
        
        Uses:
        - Word overlap (Jaccard-like)
        - Levenshtein distance (simplified)
        - Substring matching
        """
        if not s1 or not s2:
            return 0.0
        
        s1_lower = s1.lower().strip()
        s2_lower = s2.lower().strip()
        
        # Exact match
        if s1_lower == s2_lower:
            return 1.0
        
        # Substring match
        if s1_lower in s2_lower or s2_lower in s1_lower:
            return 0.9
        
        # Word overlap similarity
        words1 = set(re.findall(r"\w+", s1_lower))
        words2 = set(re.findall(r"\w+", s2_lower))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        jaccard = len(intersection) / len(union) if union else 0.0
        
        # Levenshtein-like character similarity
        char_similarity = self._character_similarity(s1_lower, s2_lower)
        
        # Combine scores
        combined = (jaccard * 0.6) + (char_similarity * 0.4)
        
        return round(combined, 2)
    
    def _character_similarity(self, s1: str, s2: str) -> float:
        """Calculate character-level similarity."""
        if len(s1) == 0 and len(s2) == 0:
            return 1.0
        if len(s1) == 0 or len(s2) == 0:
            return 0.0
        
        # Simple character overlap
        set1 = set(s1)
        set2 = set(s2)
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _compare_weights(self, weight1: str, weight2: str) -> bool:
        """Compare weight strings for similarity."""
        # Normalize weight strings
        w1_norm = re.sub(r"[^\d.]", "", weight1.lower())
        w2_norm = re.sub(r"[^\d.]", "", weight2.lower())
        
        if w1_norm == w2_norm:
            return True
        
        # Try to parse as numbers
        try:
            w1_num = float(w1_norm)
            w2_num = float(w2_norm)
            
            # Allow small tolerance
            return abs(w1_num - w2_num) < 0.1
        except (ValueError, TypeError):
            return False
    
    def match_multiple_products(
        self,
        ocr_details_list: List[Dict[str, Any]],
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Match multiple OCR results to products.
        
        Args:
            ocr_details_list: List of OCR detail dicts
            db: Database session
        
        Returns:
            List of match results
        """
        results = []
        for ocr_details in ocr_details_list:
            match = self.match_product(ocr_details, db)
            results.append(match)
        return results
    
    def search_products_by_keywords(
        self,
        keywords: str,
        db: Session,
        limit: int = 10
    ) -> List[ProductModel]:
        """
        Search products by OCR keywords or aliases.
        
        Args:
            keywords: Search keywords
            db: Database session
            limit: Max results
        
        Returns:
            List of matching products
        """
        keywords_lower = keywords.lower()
        
        products = db.query(ProductModel).all()
        matches = []
        
        for product in products:
            score = 0.0
            
            # Check product name
            if keywords_lower in product.name.lower():
                score += 1.0
            
            # Check brand
            if product.brand and keywords_lower in product.brand.lower():
                score += 0.8
            
            # Check aliases
            if product.aliases:
                aliases = json.loads(product.aliases) if isinstance(product.aliases, str) else product.aliases
                if isinstance(aliases, list):
                    for alias in aliases:
                        if keywords_lower in alias.lower():
                            score += 0.7
                            break
            
            # Check OCR keywords
            if product.ocr_keywords:
                ocr_keywords = json.loads(product.ocr_keywords) if isinstance(product.ocr_keywords, str) else product.ocr_keywords
                if isinstance(ocr_keywords, list):
                    for keyword in ocr_keywords:
                        if keywords_lower in keyword.lower():
                            score += 0.6
                            break
            
            if score > 0:
                matches.append((product, score))
        
        # Sort by score and return top matches
        matches.sort(key=lambda x: x[1], reverse=True)
        return [m[0] for m in matches[:limit]]
