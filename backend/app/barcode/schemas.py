from typing import Optional, List, Dict
from pydantic import BaseModel


class DetectionSchema(BaseModel):
    value: str
    barcode_type: Optional[str]
    confidence: Optional[float]
    bbox: Optional[Dict[str, float]]
    rotation: Optional[float]


class ScanResultSchema(BaseModel):
    scan_id: int
    detections: List[DetectionSchema]


class StartScanResponse(BaseModel):
    scan_id: int
    status: str
