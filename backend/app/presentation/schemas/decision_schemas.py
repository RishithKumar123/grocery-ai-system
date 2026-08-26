from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class DecisionPayload(BaseModel):
    yolo_label: Optional[str] = None
    ocr_text: Optional[str] = None
    barcode: Optional[str] = None
    embedding_similarity: Optional[float] = None
    video_id: Optional[int] = None
    store_id: Optional[int] = None


class BatchDecisionPayload(BaseModel):
    store_id: int
    video_id: Optional[int] = None
    items: List[DecisionPayload]


class CandidateOut(BaseModel):
    id: int
    product_id: Optional[int]
    product_name: str
    yolo_score: float
    ocr_score: float
    barcode_score: float
    embedding_score: float
    combined_score: float

    model_config = {"from_attributes": True}


class DecisionFeedbackOut(BaseModel):
    id: int
    corrected_product_id: Optional[int]
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class DecisionOut(BaseModel):
    id: int
    video_id: Optional[int]
    store_id: Optional[int]
    selected_product_id: Optional[int]
    raw_yolo_label: Optional[str]
    raw_ocr_text: Optional[str]
    raw_barcode: Optional[str]
    final_confidence: float
    status: str
    explanation: Optional[Dict[str, Any]]
    created_at: datetime
    candidates: List[CandidateOut] = []
    feedback: List[DecisionFeedbackOut] = []

    model_config = {"from_attributes": True}


class RuleOut(BaseModel):
    id: int
    rule_key: str
    rule_name: str
    rule_type: str
    value: str
    description: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}


class RuleUpdate(BaseModel):
    value: str
    is_active: Optional[bool] = True


class WeightsUpdate(BaseModel):
    yolo_weight: float = Field(..., ge=0.0, le=1.0)
    ocr_weight: float = Field(..., ge=0.0, le=1.0)
    barcode_weight: float = Field(..., ge=0.0, le=1.0)
    embedding_weight: float = Field(..., ge=0.0, le=1.0)


class WeightsOut(BaseModel):
    id: int
    yolo_weight: float
    ocr_weight: float
    barcode_weight: float
    embedding_weight: float
    historical_weight: float
    is_active: bool

    model_config = {"from_attributes": True}


class FeedbackSubmit(BaseModel):
    corrected_product_id: Optional[int] = None
    notes: Optional[str] = None
