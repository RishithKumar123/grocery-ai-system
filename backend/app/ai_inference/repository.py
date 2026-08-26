from typing import List, Optional
from sqlalchemy.orm import Session
from app.ai_inference import models


class SQLAlchemyInferenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_job(self, job_type: str, created_by_id: Optional[int] = None) -> models.InferenceJobModel:
        job = models.InferenceJobModel(job_type=job_type, status="pending", created_by_id=created_by_id)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_job_status(self, job_id: int, status: str):
        job = self.db.get(models.InferenceJobModel, job_id)
        if job:
            job.status = status
            self.db.commit()
            self.db.refresh(job)
        return job

    def add_result(self, job_id: int, source: str, model_id: Optional[int], model_version: Optional[str], result_metadata: Optional[dict] = None):
        res = models.InferenceResultModel(job_id=job_id, source=source, model_id=model_id, model_version=model_version, result_metadata=result_metadata)
        self.db.add(res)
        self.db.commit()
        self.db.refresh(res)
        return res

    def add_detection(self, result_id: int, class_id: int, class_name: str, confidence: float, bbox: dict, detection_time_ms: Optional[int] = None):
        det = models.DetectionModel(result_id=result_id, class_id=class_id, class_name=class_name, confidence=confidence, bbox=bbox, detection_time_ms=detection_time_ms)
        self.db.add(det)
        self.db.commit()
        self.db.refresh(det)
        return det

    def get_results_for_job(self, job_id: int) -> List[models.InferenceResultModel]:
        return self.db.query(models.InferenceResultModel).filter(models.InferenceResultModel.job_id == job_id).all()
