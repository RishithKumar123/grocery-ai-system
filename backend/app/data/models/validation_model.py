from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ValidationJobModel(Base):
    __tablename__ = "validation_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    validation_type: Mapped[str] = mapped_column(String(100), nullable=False, default="dataset_quality")
    version_tag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    total_assets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_assets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_checks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warning_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recommendation_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    errors: Mapped[List["ValidationErrorModel"]]
    report: Mapped[Optional["DatasetQualityReportModel"]]
    review_history: Mapped[List["ReviewHistoryModel"]]
    approvals: Mapped[List["DatasetApprovalModel"]]

    errors = relationship("ValidationErrorModel", back_populates="job", cascade="all, delete-orphan")
    report = relationship("DatasetQualityReportModel", back_populates="job", uselist=False, cascade="all, delete-orphan")
    review_history = relationship("ReviewHistoryModel", back_populates="job", cascade="all, delete-orphan")
    approvals = relationship("DatasetApprovalModel", back_populates="job", cascade="all, delete-orphan")


class DatasetQualityReportModel(Base):
    __tablename__ = "dataset_quality_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("validation_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    image_quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    annotation_quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    completeness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    balance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    metadata_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    integrity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recommendations: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    report_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["ValidationJobModel"] = relationship("ValidationJobModel", back_populates="report")


class ValidationErrorModel(Base):
    __tablename__ = "validation_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("validation_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(String(16), nullable=False)
    asset_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    asset_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    error_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default="medium")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["ValidationJobModel"] = relationship("ValidationJobModel", back_populates="errors")


class QualityScoreModel(Base):
    __tablename__ = "quality_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("validation_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    score_type: Mapped[str] = mapped_column(String(100), nullable=False)
    score_value: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["ValidationJobModel"] = relationship("ValidationJobModel")


class ClassDistributionModel(Base):
    __tablename__ = "class_distribution"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("validation_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    label_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["ValidationJobModel"] = relationship("ValidationJobModel")


class ReviewHistoryModel(Base):
    __tablename__ = "review_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("validation_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["ValidationJobModel"] = relationship("ValidationJobModel", back_populates="review_history")


class DatasetApprovalModel(Base):
    __tablename__ = "dataset_approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("validation_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    approved_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="approved")
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["ValidationJobModel"] = relationship("ValidationJobModel", back_populates="approvals")
