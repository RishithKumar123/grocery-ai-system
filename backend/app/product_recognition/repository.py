from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.product_recognition import models
from app.data.models.product_model import ProductModel


class SQLAlchemyProductRecognitionRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_barcode(self, barcode: str) -> Optional[ProductModel]:
        return self.db.query(ProductModel).filter((ProductModel.barcode == barcode) | (ProductModel.qr_code == barcode)).first()

    def search_by_name(self, text: str, limit: int = 10) -> List[ProductModel]:
        q = text.lower()
        return self.db.query(ProductModel).filter(ProductModel.name.ilike(f"%{q}%") | ProductModel.aliases.ilike(f"%{q}%")).limit(limit).all()

    def get_product(self, product_id: int) -> Optional[ProductModel]:
        return self.db.get(ProductModel, product_id)

    def create_match(self, product_id: Optional[int], source_id: Optional[str], final_score: float, extras: Optional[dict] = None):
        m = models.ProductMatchModel(product_id=product_id, source_id=source_id, final_score=final_score, extras=extras)
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return m

    def add_candidate(self, match_id: int, candidate_product_id: Optional[int], component: str, score: float, details: Optional[dict] = None):
        c = models.MatchCandidateModel(match_id=match_id, candidate_product_id=candidate_product_id, component=component, score=score, details=details)
        self.db.add(c)
        self.db.commit()
        self.db.refresh(c)
        return c

    def log_history(self, source_id: Optional[str], payload: dict, match_id: Optional[int] = None):
        h = models.RecognitionHistoryModel(source_id=source_id, request_payload=payload, match_id=match_id)
        self.db.add(h)
        self.db.commit()
        self.db.refresh(h)
        return h

    def create_unknown(self, image_path: Optional[str], ocr_text: Optional[str], barcode: Optional[str], yolo_class: Optional[str], confidence: Optional[float], metadata: Optional[dict] = None):
        u = models.UnknownProductModel(image_path=image_path, ocr_text=ocr_text, barcode=barcode, yolo_class=yolo_class, confidence=confidence, metadata_blob=metadata)
        self.db.add(u)
        self.db.commit()
        self.db.refresh(u)
        return u

    def add_feedback(self, match_id: int, user_id: Optional[int], correct_product_id: Optional[int], comment: Optional[str] = None):
        f = models.RecognitionFeedbackModel(match_id=match_id, user_id=user_id, correct_product_id=correct_product_id, comment=comment)
        self.db.add(f)
        self.db.commit()
        self.db.refresh(f)
        return f
