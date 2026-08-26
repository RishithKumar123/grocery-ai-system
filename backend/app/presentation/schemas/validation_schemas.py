from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

ValidationStatus = Literal["draft", "pending_validation", "running", "validation_failed", "pending_review", "approved", "rejected", "cancelled", "archived"]
ValidationSeverity = Literal["low", "medium", "high", "critical"]
AssetType = Literal["image", "video"]


class ValidationJobCreate(BaseModel):
    dataset_id: int
    validation_type: Optional[str] = "dataset_quality"
    version_tag: Optional[str] = None


class ValidationJobOut(BaseModel):
    id: int
    dataset_id: int
    requested_by_id: int
    status: str
    validation_type: str
    version_tag: Optional[str]
    total_assets: int
    processed_assets: int
    failed_checks: int
    warning_count: int
    overall_score: Optional[float]
    recommendation_summary: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ValidationErrorOut(BaseModel):
    id: int
    job_id: int
    dataset_id: int
    asset_type: str
    asset_id: Optional[int]
    asset_url: Optional[str]
    error_type: str
    severity: str
    message: str
    details: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClassDistributionOut(BaseModel):
    id: int
    job_id: int
    dataset_id: int
    label_name: Optional[str]
    product_id: Optional[int]
    count: int
    percentage: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewHistoryCreate(BaseModel):
    comment: Optional[str] = None


class ReviewHistoryOut(BaseModel):
    id: int
    job_id: int
    dataset_id: int
    reviewer_id: int
    action: str
    comment: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatasetApprovalCreate(BaseModel):
    comment: Optional[str] = None


class DatasetApprovalOut(BaseModel):
    id: int
    job_id: int
    dataset_id: int
    approved_by_id: int
    status: str
    comment: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatasetQualityReportOut(BaseModel):
    id: int
    job_id: int
    dataset_id: int
    image_quality_score: float
    annotation_quality_score: float
    completeness_score: float
    balance_score: float
    metadata_score: float
    integrity_score: float
    overall_score: float
    recommendations: Optional[Dict[str, Any]]
    report_payload: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ValidationAnalyticsOut(BaseModel):
    total_datasets: int
    approved_datasets: int
    rejected_datasets: int
    pending_review: int
    average_quality_score: float
    pass_rate: float
    failed_validation_count: int
    last_validation_date: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ValidationErrorListRequest(BaseModel):
    job_id: Optional[int] = None
    dataset_id: Optional[int] = None
    severity: Optional[ValidationSeverity] = None
    asset_type: Optional[AssetType] = None
    error_type: Optional[str] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0
