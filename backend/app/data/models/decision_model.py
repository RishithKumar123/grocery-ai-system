import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class DecisionResultModel(Base):
    __tablename__ = "decision_results"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="SET NULL"), nullable=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="SET NULL"), nullable=True)
    selected_product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    raw_yolo_label = Column(String, nullable=True)
    raw_ocr_text = Column(String, nullable=True)
    raw_barcode = Column(String, nullable=True)
    final_confidence = Column(Float, default=0.0)
    status = Column(String, default="Pending Review")  # "Pending Review", "Approved", "Rejected", "Corrected"
    explanation = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    product = relationship("ProductModel")
    candidates = relationship("DecisionCandidateModel", back_populates="decision", cascade="all, delete-orphan")
    feedback = relationship("DecisionFeedbackModel", back_populates="decision", cascade="all, delete-orphan")


class DecisionCandidateModel(Base):
    __tablename__ = "decision_candidates"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(Integer, ForeignKey("decision_results.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    product_name = Column(String, nullable=False)
    yolo_score = Column(Float, default=0.0)
    ocr_score = Column(Float, default=0.0)
    barcode_score = Column(Float, default=0.0)
    embedding_score = Column(Float, default=0.0)
    combined_score = Column(Float, default=0.0)

    # Relationships
    decision = relationship("DecisionResultModel", back_populates="candidates")
    product = relationship("ProductModel")


class DecisionRuleModel(Base):
    __tablename__ = "decision_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_key = Column(String, unique=True, index=True, nullable=False)
    rule_name = Column(String, nullable=False)
    rule_type = Column(String, default="boolean")  # "boolean", "numeric"
    value = Column(String, nullable=False)  # "true", "false", "0.95"
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)


class DecisionWeightModel(Base):
    __tablename__ = "decision_weights"

    id = Column(Integer, primary_key=True, index=True)
    yolo_weight = Column(Float, default=0.25)
    ocr_weight = Column(Float, default=0.25)
    barcode_weight = Column(Float, default=0.30)
    embedding_weight = Column(Float, default=0.20)
    historical_weight = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)


class DecisionFeedbackModel(Base):
    __tablename__ = "decision_feedback"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(Integer, ForeignKey("decision_results.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    corrected_product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    decision = relationship("DecisionResultModel", back_populates="feedback")
    corrected_product = relationship("ProductModel")
