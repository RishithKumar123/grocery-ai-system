from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class NearestStoreInfo(BaseModel):
    store_id: int
    store_name: str
    branch: Optional[str] = None
    available_quantity: int
    distance_km: Optional[float] = 2.5


class AvailabilityCheckOut(BaseModel):
    status: str  # YES or NO
    reason: Optional[str] = None
    
    # Detailed product info (populated if YES)
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    available_quantity: Optional[int] = None
    unit: Optional[str] = "pcs"
    
    # Location info (populated if YES)
    store_id: int
    store_name: Optional[str] = None
    branch: Optional[str] = None
    aisle: Optional[str] = None
    rack: Optional[str] = None
    shelf: Optional[str] = None
    bin: Optional[str] = None
    
    # AI Scan Verification Metadata
    last_scan_time: Optional[datetime] = None
    last_inventory_update: Optional[datetime] = None
    confidence_score: Optional[float] = 1.0
    product_image: Optional[str] = None
    
    # Multi-store Fallback (populated if NO and found in another branch)
    nearest_available_store: Optional[NearestStoreInfo] = None
    
    # Telemetry
    search_time_ms: float = 0.0


class AvailabilityBatchPayload(BaseModel):
    store_id: int = 1
    queries: List[str]


class AvailabilityHistoryOut(BaseModel):
    id: int
    product_id: Optional[int]
    product_name: Optional[str]
    store_id: int
    search_query: str
    search_method: str
    status: str
    reason: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AvailabilityStatsOut(BaseModel):
    total_searches: int
    available_products: int
    unavailable_products: int
    search_success_rate: float
    average_search_time_ms: float
    most_searched_products: List[Dict[str, Any]]
