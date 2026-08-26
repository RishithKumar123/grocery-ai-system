from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class YOLODetection(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: Dict[str, float]


class OCRResult(BaseModel):
    text: str
    confidence: Optional[float]


class BarcodeResult(BaseModel):
    value: str
    type: Optional[str]


class RecognizeRequest(BaseModel):
    yolo: Optional[List[YOLODetection]] = None
    ocr: Optional[List[OCRResult]] = None
    barcode: Optional[List[BarcodeResult]] = None
    metadata: Optional[Dict[str, Any]] = None
    embeddings: Optional[List[float]] = None
    source_id: Optional[str] = None


class CandidateOut(BaseModel):
    product_id: Optional[int]
    name: Optional[str]
    score: float
    component: str
    details: Optional[Dict[str, Any]] = None


class RecognizeResponse(BaseModel):
    match_product_id: Optional[int]
    match_name: Optional[str]
    confidence: float
    candidates: List[CandidateOut]
    reason: Optional[str]
