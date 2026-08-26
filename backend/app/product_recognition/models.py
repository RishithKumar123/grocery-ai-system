from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, DateTime, Float, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ProductMatchModel(Base):
    __tablename__ = "product_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # e.g., scan id or job id
    final_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    extras: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    product = relationship("ProductModel")
    candidates = relationship("MatchCandidateModel", back_populates="match", cascade="all, delete-orphan")
    scores = relationship("MatchScoreModel", cascade="all, delete-orphan")


class MatchCandidateModel(Base):
    __tablename__ = "match_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("product_matches.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    component: Mapped[str] = mapped_column(String(50), nullable=False)  # barcode/ocr/embedding/yolo/metadata
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    match = relationship("ProductMatchModel", back_populates="candidates")
    candidate = relationship("ProductModel")


class MatchScoreModel(Base):
    __tablename__ = "match_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("product_matches.id", ondelete="CASCADE"), nullable=False, index=True)
    component: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)


class RecognitionHistoryModel(Base):
    __tablename__ = "recognition_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    request_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    match_id: Mapped[Optional[int]] = mapped_column(ForeignKey("product_matches.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UnknownProductModel(Base):
    __tablename__ = "unknown_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    image_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    yolo_class: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metadata_blob: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed: Mapped[bool] = mapped_column(default=False)


class RecognitionFeedbackModel(Base):
    __tablename__ = "recognition_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("product_matches.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    correct_product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
