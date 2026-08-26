from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class BoundingBoxSchema(BaseModel):
    xmin: float
    ymin: float
    xmax: float
    ymax: float


class RawDetectionPayload(BaseModel):
    yolo_label: Optional[str] = None
    ocr_text: Optional[str] = None
    barcode: Optional[str] = None
    confidence: float
    bounding_box: BoundingBoxSchema


class CountingImagePayload(BaseModel):
    store_id: int
    shelf_id: Optional[int] = None
    detections: List[RawDetectionPayload]


class CountingJobPayload(BaseModel):
    store_id: int
    video_id: Optional[int] = None
    config: Optional[Dict[str, Any]] = None


class CountingResultOut(BaseModel):
    id: int
    product_id: Optional[int] = None
    product_name: Optional[str] = "Unknown Product"
    raw_count: int
    verified_count: int
    duplicate_count: int
    rejected_count: int

    model_config = {"from_attributes": True}


class TrackedObjectOut(BaseModel):
    id: int
    track_id: int
    product_id: Optional[int] = None
    product_name: Optional[str] = "Unknown Product"
    confidence: float
    bounding_box: Dict[str, Any]
    start_frame: int
    end_frame: int
    status: str

    model_config = {"from_attributes": True}


class CountStatisticsOut(BaseModel):
    id: int
    total_products_counted: int
    average_counting_accuracy: float
    duplicate_detection_rate: float
    tracking_accuracy: float
    processing_speed: float
    products_per_minute: float

    model_config = {"from_attributes": True}


class CountValidationOut(BaseModel):
    id: int
    validation_rule_key: str
    value: str
    status: str
    validation_notes: Optional[str]

    model_config = {"from_attributes": True}


class CountingJobOut(BaseModel):
    id: int
    store_id: int
    video_id: Optional[int]
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    total_counted: int
    average_confidence: float
    created_at: datetime
    results: List[CountingResultOut] = []
    tracks: List[TrackedObjectOut] = []
    statistics: Optional[CountStatisticsOut] = None
    validations: List[CountValidationOut] = []

    model_config = {"from_attributes": True}


class CountHistoryOut(BaseModel):
    id: int
    product_id: Optional[int]
    product_name: str
    shelf_id: Optional[int]
    shelf_aisle: Optional[str]
    shelf_level: Optional[str]
    count: int
    verified_at: datetime
    job_id: int

    model_config = {"from_attributes": True}


class CountHistoryVerifyPayload(BaseModel):
    notes: Optional[str] = None
