from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class DetectionOut(BaseModel):
    id: int
    scan_id: int
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    confidence: float
    bounding_box: Dict[str, Any]
    raw_ocr_text: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScanOut(BaseModel):
    id: int
    video_id: Optional[int] = None
    store_id: int
    image_url: str
    status: str
    created_at: datetime
    detections: List[DetectionOut] = []
    
    # Timing fields
    scan_start_time: Optional[datetime] = None
    scan_end_time: Optional[datetime] = None
    scan_duration: Optional[float] = None
    frames_processed: Optional[int] = None
    fps: Optional[float] = None
    progress_percentage: Optional[int] = 0
    progress_stage: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
