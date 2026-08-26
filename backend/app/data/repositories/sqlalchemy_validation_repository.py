from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.data.models.validation_model import (
    ValidationJobModel,
    DatasetQualityReportModel,
    ValidationErrorModel,
    QualityScoreModel,
    ClassDistributionModel,
    ReviewHistoryModel,
    DatasetApprovalModel,
)


class SQLAlchemyValidationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_validation_job(self, payload: Dict[str, Any], requested_by_id: int) -> ValidationJobModel:
        job = ValidationJobModel(
            dataset_id=payload["dataset_id"],
            requested_by_id=requested_by_id,
            status=payload.get("status", "pending_validation"),
            validation_type=payload.get("validation_type", "dataset_quality"),
            version_tag=payload.get("version_tag"),
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_job(self, job_id: int) -> Optional[ValidationJobModel]:
        return self.db.query(ValidationJobModel).filter(ValidationJobModel.id == job_id).first()

    def list_jobs(self, dataset_id: Optional[int] = None, status: Optional[str] = None) -> List[ValidationJobModel]:
        query = self.db.query(ValidationJobModel)
        if dataset_id is not None:
            query = query.filter(ValidationJobModel.dataset_id == dataset_id)
        if status is not None:
            query = query.filter(ValidationJobModel.status == status)
        return query.order_by(ValidationJobModel.created_at.desc()).all()

    def update_job_status(self, job_id: int, status: str, processed_assets: Optional[int] = None, failed_checks: Optional[int] = None, warning_count: Optional[int] = None, overall_score: Optional[float] = None) -> Optional[ValidationJobModel]:
        job = self.get_job(job_id)
        if not job:
            return None
        job.status = status
        if processed_assets is not None:
            job.processed_assets = processed_assets
        if failed_checks is not None:
            job.failed_checks = failed_checks
        if warning_count is not None:
            job.warning_count = warning_count
        if overall_score is not None:
            job.overall_score = overall_score
        job.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
        return job

    def cancel_job(self, job_id: int) -> bool:
        job = self.get_job(job_id)
        if not job or job.status not in ["pending_validation", "running", "pending_review"]:
            return False
        job.is_cancelled = True
        job.status = "cancelled"
        job.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def add_validation_error(self, payload: Dict[str, Any]) -> ValidationErrorModel:
        error = ValidationErrorModel(
            job_id=payload["job_id"],
            dataset_id=payload["dataset_id"],
            asset_type=payload["asset_type"],
            asset_id=payload.get("asset_id"),
            asset_url=payload.get("asset_url"),
            error_type=payload["error_type"],
            severity=payload.get("severity", "medium"),
            message=payload["message"],
            details=payload.get("details") or {},
        )
        self.db.add(error)
        self.db.commit()
        self.db.refresh(error)
        return error

    def add_class_distribution(self, payload: Dict[str, Any]) -> ClassDistributionModel:
        entry = ClassDistributionModel(
            job_id=payload["job_id"],
            dataset_id=payload["dataset_id"],
            label_name=payload.get("label_name"),
            product_id=payload.get("product_id"),
            count=payload.get("count", 0),
            percentage=payload.get("percentage", 0.0),
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def save_quality_report(self, payload: Dict[str, Any]) -> DatasetQualityReportModel:
        report = DatasetQualityReportModel(
            job_id=payload["job_id"],
            dataset_id=payload["dataset_id"],
            image_quality_score=payload.get("image_quality_score", 0.0),
            annotation_quality_score=payload.get("annotation_quality_score", 0.0),
            completeness_score=payload.get("completeness_score", 0.0),
            balance_score=payload.get("balance_score", 0.0),
            metadata_score=payload.get("metadata_score", 0.0),
            integrity_score=payload.get("integrity_score", 0.0),
            overall_score=payload.get("overall_score", 0.0),
            recommendations=payload.get("recommendations") or {},
            report_payload=payload.get("report_payload") or {},
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def add_quality_score(self, payload: Dict[str, Any]) -> QualityScoreModel:
        score = QualityScoreModel(
            job_id=payload["job_id"],
            score_type=payload["score_type"],
            score_value=payload["score_value"],
            details=payload.get("details") or {},
        )
        self.db.add(score)
        self.db.commit()
        self.db.refresh(score)
        return score

    def add_review_history(self, payload: Dict[str, Any]) -> ReviewHistoryModel:
        history = ReviewHistoryModel(
            job_id=payload["job_id"],
            dataset_id=payload["dataset_id"],
            reviewer_id=payload["reviewer_id"],
            action=payload["action"],
            comment=payload.get("comment"),
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def add_dataset_approval(self, payload: Dict[str, Any]) -> DatasetApprovalModel:
        approval = DatasetApprovalModel(
            job_id=payload["job_id"],
            dataset_id=payload["dataset_id"],
            approved_by_id=payload["approved_by_id"],
            status=payload.get("status", "approved"),
            comment=payload.get("comment"),
        )
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def list_errors(self, job_id: Optional[int] = None, dataset_id: Optional[int] = None, severity: Optional[str] = None, asset_type: Optional[str] = None) -> List[ValidationErrorModel]:
        query = self.db.query(ValidationErrorModel)
        if job_id is not None:
            query = query.filter(ValidationErrorModel.job_id == job_id)
        if dataset_id is not None:
            query = query.filter(ValidationErrorModel.dataset_id == dataset_id)
        if severity is not None:
            query = query.filter(ValidationErrorModel.severity == severity)
        if asset_type is not None:
            query = query.filter(ValidationErrorModel.asset_type == asset_type)
        return query.order_by(ValidationErrorModel.created_at.desc()).all()

    def get_analytics_summary(self) -> Dict[str, Any]:
        total_datasets = self.db.query(func.count(ValidationJobModel.id)).scalar() or 0
        approved_datasets = self.db.query(func.count(ValidationJobModel.id)).filter(ValidationJobModel.status == "approved").scalar() or 0
        rejected_datasets = self.db.query(func.count(ValidationJobModel.id)).filter(ValidationJobModel.status == "rejected").scalar() or 0
        pending_review = self.db.query(func.count(ValidationJobModel.id)).filter(ValidationJobModel.status == "pending_review").scalar() or 0
        average_quality_score = self.db.query(func.avg(DatasetQualityReportModel.overall_score)).scalar() or 0.0
        failed_validation_count = self.db.query(func.count(ValidationJobModel.id)).filter(ValidationJobModel.status == "validation_failed").scalar() or 0
        last_validation_date = self.db.query(func.max(ValidationJobModel.completed_at)).scalar()
        pass_rate = 0.0
        if total_datasets > 0:
            pass_rate = round((approved_datasets / total_datasets) * 100.0, 2)
        return {
            "total_datasets": total_datasets,
            "approved_datasets": approved_datasets,
            "rejected_datasets": rejected_datasets,
            "pending_review": pending_review,
            "average_quality_score": round(float(average_quality_score or 0.0), 2),
            "pass_rate": pass_rate,
            "failed_validation_count": failed_validation_count,
            "last_validation_date": last_validation_date,
        }
