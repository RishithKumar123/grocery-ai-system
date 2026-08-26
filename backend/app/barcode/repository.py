from typing import Optional, List
from sqlalchemy.orm import Session
from app.barcode import models


class SQLAlchemyBarcodeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_scan(self, source: Optional[str] = None, scanned_by_id: Optional[int] = None) -> models.BarcodeScanModel:
        s = models.BarcodeScanModel(source=source, scanned_by_id=scanned_by_id)
        self.db.add(s)
        self.db.commit()
        self.db.refresh(s)
        return s

    def add_result(self, scan_id: int, value: str, barcode_type_id: Optional[int], confidence: Optional[float], bbox: Optional[dict], rotation: Optional[float]):
        r = models.BarcodeResultModel(scan_id=scan_id, value=value, barcode_type_id=barcode_type_id, confidence=confidence, bbox=bbox, rotation=rotation)
        self.db.add(r)
        self.db.commit()
        self.db.refresh(r)
        return r

    def queue_unknown(self, value: str, source_scan_id: Optional[int], metadata: Optional[dict] = None):
        u = models.UnknownBarcodeModel(value=value, source_scan_id=source_scan_id, metadata_blob=metadata)
        self.db.add(u)
        self.db.commit()
        self.db.refresh(u)
        return u

    def list_history(self, limit: int = 50) -> List[models.BarcodeResultModel]:
        return self.db.query(models.BarcodeResultModel).order_by(models.BarcodeResultModel.created_at.desc()).limit(limit).all()

    def list_unknowns(self, limit: int = 50):
        return self.db.query(models.UnknownBarcodeModel).filter(models.UnknownBarcodeModel.reviewed == False).order_by(models.UnknownBarcodeModel.queued_at.desc()).limit(limit).all()

    def mark_unknown_reviewed(self, unknown_id: int, approved: bool):
        u = self.db.get(models.UnknownBarcodeModel, unknown_id)
        if u:
            u.reviewed = True
            u.approved = approved
            self.db.commit()
            self.db.refresh(u)
        return u
