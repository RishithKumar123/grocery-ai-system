import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.data.models.product_model import ProductModel
from app.data.models.decision_model import (
    DecisionResultModel,
    DecisionCandidateModel,
    DecisionRuleModel,
    DecisionWeightModel,
    DecisionFeedbackModel
)
from app.core.logging import logger


class DecisionEngineService:
    @staticmethod
    def get_or_create_weights(db: Session) -> DecisionWeightModel:
        """Fetch active weights or seed defaults for product verification system."""
        weights = db.query(DecisionWeightModel).filter(DecisionWeightModel.is_active == True).first()
        if not weights:
            # Product Verification System weights:
            # Barcode: 70% (highest priority - definitive match)
            # OCR: 15% (text matching)
            # Embeddings: 15% (visual similarity)
            weights = DecisionWeightModel(
                yolo_weight=0.00,  # Not used in product verification (generic detection only)
                ocr_weight=0.15,
                barcode_weight=0.70,
                embedding_weight=0.15,
                historical_weight=0.00
            )
            db.add(weights)
            db.commit()
            db.refresh(weights)
        return weights

    @staticmethod
    def get_or_create_rules(db: Session) -> List[DecisionRuleModel]:
        """Fetch active business rules or seed defaults for product verification."""
        rules = db.query(DecisionRuleModel).all()
        if not rules:
            default_rules = [
                DecisionRuleModel(
                    rule_key="barcode_exact_match_override",
                    rule_name="Barcode Exact Match Override",
                    rule_type="boolean",
                    value="true",
                    description="If barcode matches exactly, immediately return YES regardless of other signals."
                ),
                DecisionRuleModel(
                    rule_key="ocr_similarity_threshold",
                    rule_name="OCR Similarity Threshold",
                    rule_type="numeric",
                    value="0.60",
                    description="Minimum OCR similarity score to consider a match."
                ),
                DecisionRuleModel(
                    rule_key="embedding_similarity_threshold",
                    rule_name="Embedding Similarity Threshold",
                    rule_type="numeric",
                    value="0.75",
                    description="Minimum visual embedding similarity to consider a match."
                ),
                DecisionRuleModel(
                    rule_key="overall_confidence_threshold",
                    rule_name="Overall Confidence Threshold",
                    rule_type="numeric",
                    value="0.50",
                    description="Minimum combined confidence to return YES."
                ),
                DecisionRuleModel(
                    rule_key="reject_unregistered_products",
                    rule_name="Reject Unregistered Items",
                    rule_type="boolean",
                    value="true",
                    description="Return NO if product cannot be matched to catalog."
                ),
                DecisionRuleModel(
                    rule_key="admin_correction_preference",
                    rule_name="Prefer Admin Corrections",
                    rule_type="boolean",
                    value="true",
                    description="Prefer historical admin corrections for conflicting signatures."
                )
            ]
            for r in default_rules:
                db.add(r)
            db.commit()
            rules = db.query(DecisionRuleModel).all()
        return rules

    @staticmethod
    def calculate_similarity(s1: str, s2: str) -> float:
        """Calculates simple word intersection similarity between two strings (levenshtein substitute)."""
        if not s1 or not s2:
            return 0.0
        words1 = set(re.findall(r"\w+", s1.lower()))
        words2 = set(re.findall(r"\w+", s2.lower()))
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        return len(intersection) / max(len(words1), len(words2))

    def resolve_decision(
        self,
        db: Session,
        yolo_label: Optional[str],
        ocr_text: Optional[str],
        barcode: Optional[str],
        embedding_similarity: Optional[float] = None,
        video_id: Optional[int] = None,
        store_id: Optional[int] = None,
        target_product_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Product Verification Decision Engine.
        
        For a specific target product, determines if it's present in the image.
        
        Returns:
        {
            "present": bool,
            "confidence": float,
            "quantity": int,
            "bounding_boxes": List[Dict],
            "barcode_matched": bool,
            "ocr_matched": bool,
            "embedding_similarity": float,
            "detection_time_ms": float,
            "explanation": str
        }
        """
        import time
        start_time = time.perf_counter()
        
        logger.info(f"DecisionEngine: Verifying product ID {target_product_id} (Barcode={barcode}, OCR={ocr_text})")

        # 1. Fetch configurations
        weights = self.get_or_create_weights(db)
        rules = {r.rule_key: r for r in self.get_or_create_rules(db)}

        # Parse rule values safely with robust fallbacks
        rule_barcode_override = rules.get("barcode_exact_match_override")
        barcode_exact_override = rule_barcode_override.value.lower() == "true" if rule_barcode_override else True

        rule_ocr = rules.get("ocr_similarity_threshold")
        ocr_threshold = float(rule_ocr.value) if rule_ocr else 0.60

        rule_emb = rules.get("embedding_similarity_threshold")
        embedding_threshold = float(rule_emb.value) if rule_emb else 0.75

        rule_overall = rules.get("overall_confidence_threshold")
        overall_threshold = float(rule_overall.value) if rule_overall else 0.50

        rule_reject = rules.get("reject_unregistered_products")
        reject_unregistered = rule_reject.value.lower() == "true" if rule_reject else True

        # 2. Get target product
        target_product = None
        if target_product_id:
            target_product = db.query(ProductModel).filter(ProductModel.id == target_product_id).first()
        
        if not target_product and barcode:
            # Try to find product by barcode
            target_product = db.query(ProductModel).filter(ProductModel.barcode == barcode).first()
        
        if not target_product:
            return {
                "present": False,
                "confidence": 0.0,
                "quantity": 0,
                "bounding_boxes": [],
                "barcode_matched": False,
                "ocr_matched": False,
                "embedding_similarity": 0.0,
                "detection_time_ms": (time.perf_counter() - start_time) * 1000,
                "explanation": "Target product not found in catalog"
            }

        # 3. Calculate individual scores
        barcode_score = 0.0
        ocr_score = 0.0
        embedding_score = embedding_similarity or 0.0
        
        explanation_parts = []

        # Barcode matching (highest priority)
        if barcode and target_product.barcode == barcode:
            barcode_score = 1.0
            explanation_parts.append("Barcode exact match")
        
        # OCR matching
        if ocr_text:
            ocr_score = self.calculate_similarity(ocr_text, target_product.name)
            if ocr_score >= ocr_threshold:
                explanation_parts.append(f"OCR match: {ocr_score:.2f}")
            else:
                ocr_score = 0.0
        
        # Embedding similarity
        if embedding_score >= embedding_threshold:
            explanation_parts.append(f"Visual similarity: {embedding_score:.2f}")
        else:
            embedding_score = 0.0

        # 4. Calculate combined confidence with dynamic weight normalization
        if barcode_score == 1.0:
            combined_confidence = 1.0
        else:
            active_weights = weights.ocr_weight + weights.embedding_weight
            if active_weights > 0:
                norm_ocr = weights.ocr_weight / active_weights
                norm_emb = weights.embedding_weight / active_weights
                combined_confidence = (norm_ocr * ocr_score) + (norm_emb * embedding_score)
            else:
                combined_confidence = 0.0

        # 5. Apply barcode override rule
        if barcode_exact_override and barcode_score == 1.0:
            combined_confidence = 1.0
            explanation_parts.append("Barcode override applied")

        # 6. Final decision
        present = combined_confidence >= overall_threshold
        explanation = ", ".join(explanation_parts) if explanation_parts else "Low confidence match"

        detection_time = (time.perf_counter() - start_time) * 1000

        result = {
            "present": present,
            "confidence": round(combined_confidence, 4),
            "quantity": 1 if present else 0,  # Will be updated by caller with actual count
            "bounding_boxes": [],  # Will be populated by caller
            "barcode_matched": barcode_score == 1.0,
            "ocr_matched": ocr_score >= ocr_threshold,
            "embedding_similarity": embedding_score,
            "detection_time_ms": round(detection_time, 2),
            "explanation": explanation,
            "product_id": target_product.id,
            "product_name": target_product.name
        }

        logger.info(f"DecisionEngine: Product verification result - Present: {present}, Confidence: {combined_confidence:.2f}")
        
        return result
