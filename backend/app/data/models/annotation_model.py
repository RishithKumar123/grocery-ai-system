from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, JSON, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AnnotationModel(Base):
    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(String(16), nullable=False)
    asset_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    asset_url: Mapped[str] = mapped_column(String(500), nullable=False)
    annotation_type: Mapped[str] = mapped_column(String(64), nullable=False, default="bounding_box")
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    assigned_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reviewer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    review_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending_review")
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    consensus_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_assisted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    suggestion_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    annotation_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    updated_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    version_tag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    objects: Mapped[List["AnnotationObjectModel"]]
    labels: Mapped[List["AnnotationLabelModel"]]
    reviews: Mapped[List["AnnotationReviewModel"]]
    versions: Mapped[List["AnnotationVersionModel"]]
    history: Mapped[List["AnnotationHistoryModel"]]
    comments: Mapped[List["AnnotationCommentModel"]]
    tasks: Mapped[List["AnnotationTaskModel"]]

    objects = relationship(
        "AnnotationObjectModel",
        back_populates="annotation",
        cascade="all, delete-orphan"
    )
    labels = relationship(
        "AnnotationLabelModel",
        back_populates="annotation",
        cascade="all, delete-orphan"
    )
    reviews = relationship(
        "AnnotationReviewModel",
        back_populates="annotation",
        cascade="all, delete-orphan"
    )
    versions = relationship(
        "AnnotationVersionModel",
        back_populates="annotation",
        cascade="all, delete-orphan"
    )
    history = relationship(
        "AnnotationHistoryModel",
        back_populates="annotation",
        cascade="all, delete-orphan"
    )
    comments = relationship(
        "AnnotationCommentModel",
        back_populates="annotation",
        cascade="all, delete-orphan"
    )
    tasks = relationship(
        "AnnotationTaskModel",
        back_populates="annotation",
        cascade="all, delete-orphan"
    )


class AnnotationObjectModel(Base):
    __tablename__ = "annotation_objects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    annotation_id: Mapped[int] = mapped_column(ForeignKey("annotations.id", ondelete="CASCADE"), nullable=False, index=True)
    object_type: Mapped[str] = mapped_column(String(50), nullable=False)
    label_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    label_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    brand_id: Mapped[Optional[int]] = mapped_column(ForeignKey("brands.id", ondelete="SET NULL"), nullable=True, index=True)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("product_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    supplier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("product_suppliers.supplier_id", ondelete="SET NULL"), nullable=True, index=True)
    store_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stores.id", ondelete="SET NULL"), nullable=True, index=True)
    shelf_id: Mapped[Optional[int]] = mapped_column(ForeignKey("shelves.id", ondelete="SET NULL"), nullable=True, index=True)
    bbox: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    polygon: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    keypoints: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    attributes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_ai_suggestion: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    annotation: Mapped["AnnotationModel"] = relationship("AnnotationModel", back_populates="objects")


class AnnotationLabelModel(Base):
    __tablename__ = "annotation_labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    annotation_id: Mapped[int] = mapped_column(ForeignKey("annotations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    alias_names: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    parent_label_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    annotation: Mapped["AnnotationModel"] = relationship("AnnotationModel", back_populates="labels")


class AnnotationReviewModel(Base):
    __tablename__ = "annotation_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    annotation_id: Mapped[int] = mapped_column(ForeignKey("annotations.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    consensus_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    annotation: Mapped["AnnotationModel"] = relationship("AnnotationModel", back_populates="reviews")


class AnnotationVersionModel(Base):
    __tablename__ = "annotation_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    annotation_id: Mapped[int] = mapped_column(ForeignKey("annotations.id", ondelete="CASCADE"), nullable=False, index=True)
    version_tag: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    annotation: Mapped["AnnotationModel"] = relationship("AnnotationModel", back_populates="versions")


class AnnotationHistoryModel(Base):
    __tablename__ = "annotation_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    annotation_id: Mapped[int] = mapped_column(ForeignKey("annotations.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    annotation: Mapped["AnnotationModel"] = relationship("AnnotationModel", back_populates="history")


class AnnotationCommentModel(Base):
    __tablename__ = "annotation_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    annotation_id: Mapped[int] = mapped_column(ForeignKey("annotations.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    parent_comment_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    annotation: Mapped["AnnotationModel"] = relationship("AnnotationModel", back_populates="comments")


class AnnotationTaskModel(Base):
    __tablename__ = "annotation_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    annotation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("annotations.id", ondelete="CASCADE"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="new")
    priority: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    assigned_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    annotation: Mapped["AnnotationModel"] = relationship("AnnotationModel", back_populates="tasks")
