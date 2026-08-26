from typing import List, Dict, Optional
from pydantic import BaseModel


class DetectionOut(BaseModel):
    class_id: int
    class_name: str
    product_name: str
    confidence: float
    bbox: Dict[str, float]
    sku: Optional[str] = None
    barcode: Optional[str] = None
    track_id: Optional[int] = None
    category: Optional[str] = None
    detection_time_ms: Optional[int]


class InferenceResultOut(BaseModel):
    id: int
    source: Optional[str]
    model_id: Optional[int]
    model_version: Optional[str]
    detections: List[DetectionOut]


class StartJobResponse(BaseModel):
    job_id: int
    status: str
