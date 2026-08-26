from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AIModelModel(Base):
    __tablename__ = "ai_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    primary_dataset_version_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dataset_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    current_version_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ai_model_versions.id", ondelete="SET NULL", use_alter=True), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions: Mapped[List["AIModelVersionModel"]]
    tags: Mapped[List["ModelTagModel"]]
    deployments: Mapped[List["ModelDeploymentModel"]]
    permissions: Mapped[List["ModelPermissionModel"]]

    versions = relationship(
        "AIModelVersionModel",
        back_populates="model",
        cascade="all, delete-orphan",
        foreign_keys=lambda: [AIModelVersionModel.model_id],
    )
    tags = relationship("ModelTagModel", back_populates="model", cascade="all, delete-orphan")
    deployments = relationship("ModelDeploymentModel", back_populates="model", cascade="all, delete-orphan")
    permissions = relationship("ModelPermissionModel", back_populates="model", cascade="all, delete-orphan")


class AIModelVersionModel(Base):
    __tablename__ = "ai_model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("ai_models.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    parent_version_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ai_model_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    dataset_version_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dataset_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    training_job_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    training_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    framework_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hyperparameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    metrics_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    git_commit: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    model: Mapped["AIModelModel"]
    parent_version: Mapped[Optional["AIModelVersionModel"]]
    artifacts: Mapped[List["ModelArtifactModel"]]
    metrics: Mapped[List["ModelMetricModel"]]
    reviews: Mapped[List["ModelReviewModel"]]
    deployments: Mapped[List["ModelDeploymentModel"]]
    tags: Mapped[List["ModelTagModel"]]

    model = relationship("AIModelModel", back_populates="versions", foreign_keys=[model_id])
    parent_version = relationship("AIModelVersionModel", remote_side=[id])
    artifacts = relationship("ModelArtifactModel", back_populates="version", cascade="all, delete-orphan")
    metrics = relationship("ModelMetricModel", back_populates="version", cascade="all, delete-orphan")
    reviews = relationship("ModelReviewModel", back_populates="version", cascade="all, delete-orphan")
    deployments = relationship("ModelDeploymentModel", back_populates="version", cascade="all, delete-orphan")
    tags = relationship("ModelTagModel", back_populates="version", cascade="all, delete-orphan")


class ModelArtifactModel(Base):
    __tablename__ = "model_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("ai_model_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    artifact_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    artifact_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    version: Mapped["AIModelVersionModel"] = relationship("AIModelVersionModel", back_populates="artifacts")


class ModelMetricModel(Base):
    __tablename__ = "model_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("ai_model_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Integer, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    version: Mapped["AIModelVersionModel"] = relationship("AIModelVersionModel", back_populates="metrics")


class ModelDeploymentModel(Base):
    __tablename__ = "model_deployments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("ai_models.id", ondelete="CASCADE"), nullable=False, index=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("ai_model_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    environment: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", index=True)
    deployed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    deployed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    endpoint_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rollback_of_id: Mapped[Optional[int]] = mapped_column(ForeignKey("model_deployments.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    model: Mapped["AIModelModel"] = relationship("AIModelModel", back_populates="deployments")
    version: Mapped["AIModelVersionModel"] = relationship("AIModelVersionModel", back_populates="deployments")
    history: Mapped[List["DeploymentHistoryModel"]]

    history = relationship("DeploymentHistoryModel", back_populates="deployment", cascade="all, delete-orphan")


class DeploymentHistoryModel(Base):
    __tablename__ = "deployment_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    deployment_id: Mapped[int] = mapped_column(ForeignKey("model_deployments.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    performed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    from_version_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ai_model_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    to_version_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ai_model_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    environment: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    deployment: Mapped["ModelDeploymentModel"] = relationship("ModelDeploymentModel", back_populates="history")


class ModelReviewModel(Base):
    __tablename__ = "model_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("ai_model_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    version: Mapped["AIModelVersionModel"] = relationship("AIModelVersionModel", back_populates="reviews")


class ModelTagModel(Base):
    __tablename__ = "model_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ai_models.id", ondelete="CASCADE"), nullable=True, index=True)
    version_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ai_model_versions.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    model: Mapped[Optional["AIModelModel"]] = relationship("AIModelModel", back_populates="tags")
    version: Mapped[Optional["AIModelVersionModel"]] = relationship("AIModelVersionModel", back_populates="tags")


class ModelPermissionModel(Base):
    __tablename__ = "model_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("ai_models.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_type: Mapped[str] = mapped_column(String(32), nullable=False)
    subject_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    permission: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    model: Mapped["AIModelModel"] = relationship("AIModelModel", back_populates="permissions")
