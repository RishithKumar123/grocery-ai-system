from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

AnnotationStatus = Literal["draft", "in_progress", "pending_review", "approved", "rejected", "archived"]
AnnotationType = Literal[
    "bounding_box",
    "polygon",
    "instance_segmentation",
    "semantic_segmentation",
    "keypoints",
    "classification",
    "ocr_text",
    "barcode_region",
]
ObjectType = Literal[
    "bounding_box",
    "polygon",
    "keypoints",
    "segmentation",
    "classification",
    "text_region",
    "barcode",
]


class AnnotationObjectBase(BaseModel):
    object_type: ObjectType
    label_name: str
    category: Optional[str] = None
    product_id: Optional[int] = None
    brand_id: Optional[int] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    store_id: Optional[int] = None
    shelf_id: Optional[int] = None
    bbox: Optional[Dict[str, float]] = None
    polygon: Optional[List[Dict[str, float]]] = None
    keypoints: Optional[List[Dict[str, float]]] = None
    attributes: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    is_ai_suggestion: bool = False


class AnnotationObjectCreate(AnnotationObjectBase):
    pass


class AnnotationObjectOut(AnnotationObjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnnotationLabelBase(BaseModel):
    name: str = Field(..., min_length=1)
    alias_names: List[str] = []
    color: Optional[str] = "#FF5733"
    parent_label_id: Optional[int] = None
    is_active: bool = True


class AnnotationLabelCreate(AnnotationLabelBase):
    pass


class AnnotationLabelOut(AnnotationLabelBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnnotationReviewCreate(BaseModel):
    reviewer_id: int
    status: AnnotationStatus
    comment: Optional[str] = None
    quality_score: Optional[float] = None
    consensus_score: Optional[float] = None


class AnnotationReviewOut(AnnotationReviewCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnnotationCommentCreate(BaseModel):
    comment: str = Field(..., min_length=1)
    parent_comment_id: Optional[int] = None


class AnnotationCommentOut(AnnotationCommentCreate):
    id: int
    author_id: int
    is_resolved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnnotationTaskCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    status: Optional[str] = "new"
    priority: Optional[str] = None
    assigned_to_id: Optional[int] = None
    due_date: Optional[datetime] = None


class AnnotationTaskOut(AnnotationTaskCreate):
    id: int
    dataset_id: int
    annotation_id: Optional[int] = None
    created_by_id: int
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnnotationCreate(BaseModel):
    dataset_id: int
    asset_type: Literal["image", "video"]
    asset_id: int
    asset_url: str
    annotation_type: AnnotationType
    title: Optional[str] = None
    description: Optional[str] = None
    status: AnnotationStatus = "draft"
    assigned_to_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    ai_assisted: bool = False
    suggestion_payload: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    labels: Optional[List[AnnotationLabelCreate]] = []
    objects: Optional[List[AnnotationObjectCreate]] = []


class AnnotationUpdate(BaseModel):
    annotation_type: Optional[AnnotationType] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[AnnotationStatus] = None
    assigned_to_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    review_status: Optional[AnnotationStatus] = None
    quality_score: Optional[float] = None
    consensus_score: Optional[float] = None
    ai_assisted: Optional[bool] = None
    suggestion_payload: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    labels: Optional[List[AnnotationLabelCreate]] = None
    objects: Optional[List[AnnotationObjectCreate]] = None


class AnnotationOut(BaseModel):
    id: int
    dataset_id: int
    asset_type: str
    asset_id: int
    asset_url: str
    annotation_type: str
    title: Optional[str]
    description: Optional[str]
    status: str
    assigned_to_id: Optional[int]
    reviewer_id: Optional[int]
    review_status: str
    quality_score: Optional[float]
    consensus_score: Optional[float]
    ai_assisted: bool
    suggestion_payload: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    created_by_id: int
    updated_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime]
    rejected_at: Optional[datetime]
    version_tag: Optional[str]
    is_archived: bool
    is_deleted: bool
    deleted_at: Optional[datetime]
    objects: List[AnnotationObjectOut] = []
    labels: List[AnnotationLabelOut] = []
    reviews: List[AnnotationReviewOut] = []
    comments: List[AnnotationCommentOut] = []

    model_config = ConfigDict(from_attributes=True)


class AnnotationSearchFilters(BaseModel):
    dataset_id: Optional[int] = None
    product_id: Optional[int] = None
    brand_id: Optional[int] = None
    category_id: Optional[int] = None
    label_name: Optional[str] = None
    status: Optional[AnnotationStatus] = None
    reviewer_id: Optional[int] = None
    assigned_to_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AnnotationStatisticsOut(BaseModel):
    total_annotations: int
    pending_annotations: int
    approved_annotations: int
    rejected_annotations: int
    draft_annotations: int
    in_progress_annotations: int
    archived_annotations: int
    total_images: int
    total_videos: int
    annotator_count: int
    reviewer_count: int
    average_annotation_time_seconds: Optional[float]


class AnnotationExportRequest(BaseModel):
    export_format: Literal["yolo", "coco", "pascal_voc", "labelme", "csv", "json"]
    dataset_id: int
    version_tag: Optional[str] = None
    include_labels: Optional[bool] = True
    include_metadata: Optional[bool] = True


class AnnotationExportOut(BaseModel):
    export_url: str
    export_format: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
