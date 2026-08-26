from datetime import datetime
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

DatasetType = Literal["training", "validation", "testing", "production", "experimental", "benchmark"]
DatasetStatus = Literal["active", "inactive", "archived", "deleted"]
VisibilityType = Literal["public", "private", "team"]
AssetType = Literal["image", "video"]


class DatasetBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    dataset_type: DatasetType = "training"
    status: DatasetStatus = "active"
    visibility: VisibilityType = "private"
    owner_id: Optional[int] = None
    version: Optional[str] = None
    tags: List[str] = []


class DatasetCreate(DatasetBase):
    pass


class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    dataset_type: Optional[DatasetType] = None
    status: Optional[DatasetStatus] = None
    visibility: Optional[VisibilityType] = None
    owner_id: Optional[int] = None
    version: Optional[str] = None
    tags: Optional[List[str]] = None


class DatasetOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    dataset_type: str
    status: str
    visibility: str
    owner_id: Optional[int] = None
    created_by_id: int
    current_version: Optional[str] = None
    is_archived: bool
    is_deleted: bool
    archived_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatasetAssetCreate(BaseModel):
    dataset_id: int
    asset_type: AssetType = "image"
    product_id: Optional[int] = None
    brand_id: Optional[int] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    store_id: Optional[int] = None
    shelf_id: Optional[int] = None
    location: Optional[str] = None
    original_filename: str
    file_url: str
    width: Optional[int] = None
    height: Optional[int] = None
    aspect_ratio: Optional[str] = None
    file_size: int
    capture_date: Optional[datetime] = None
    gps_coordinates: Optional[str] = None
    camera_info: Optional[str] = None
    color_space: Optional[str] = None
    hash: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    resolution: Optional[str] = None
    fps: Optional[float] = None
    frame_count: Optional[int] = None
    metadata: Optional[Dict[str, str]] = None

    model_config = ConfigDict(from_attributes=True)


class DatasetAssetOut(BaseModel):
    id: int
    dataset_id: int
    asset_type: AssetType
    product_id: Optional[int] = None
    brand_id: Optional[int] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    store_id: Optional[int] = None
    shelf_id: Optional[int] = None
    location: Optional[str] = None
    original_filename: str
    file_url: str
    width: Optional[int] = None
    height: Optional[int] = None
    aspect_ratio: Optional[str] = None
    file_size: int
    capture_date: Optional[datetime] = None
    gps_coordinates: Optional[str] = None
    camera_info: Optional[str] = None
    color_space: Optional[str] = None
    hash: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    resolution: Optional[str] = None
    fps: Optional[float] = None
    frame_count: Optional[int] = None
    metadata: Optional[Dict[str, str]] = None

    model_config = ConfigDict(from_attributes=True)


class DatasetVersionOut(BaseModel):
    id: int
    dataset_id: int
    version_tag: str
    archive_url: str
    file_count: int
    size_bytes: int
    created_by_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatasetStatisticsOut(BaseModel):
    dataset_id: int
    total_images: int
    total_videos: int
    total_annotations: int
    total_size_bytes: int
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardSummaryOut(BaseModel):
    total_datasets: int
    total_images: int
    total_videos: int
    total_versions: int
    total_storage_bytes: int
    dataset_version_count: int

    model_config = ConfigDict(from_attributes=True)
