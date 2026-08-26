from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ModelBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    model_type: str = Field(..., min_length=1)
    owner_id: Optional[int] = None
    tags: List[str] = []


class ModelCreate(ModelBase):
    status: Optional[str] = "draft"


class ModelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    model_type: Optional[str] = None
    owner_id: Optional[int] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


class ModelOut(ModelBase):
    id: int
    status: str
    is_archived: bool
    is_deleted: bool
    created_by_id: int
    current_version_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VersionBase(BaseModel):
    version_number: str = Field(..., min_length=1)
    parent_version_id: Optional[int] = None
    dataset_version_id: Optional[int] = None
    training_job_id: Optional[int] = None
    training_config: Optional[Dict[str, Any]] = None
    framework_version: Optional[str] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    metrics_summary: Optional[Dict[str, Any]] = None
    status: Optional[str] = "draft"
    description: Optional[str] = None
    git_commit: Optional[str] = None
    tags: List[str] = []


class VersionCreate(VersionBase):
    pass


class VersionOut(VersionBase):
    id: int
    model_id: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArtifactUploadRequest(BaseModel):
    version_id: int
    artifact_type: str = Field(..., min_length=1)
    checksum: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_primary: bool = False


class ArtifactOut(BaseModel):
    id: int
    version_id: int
    artifact_type: str
    file_url: str
    checksum: Optional[str]
    metadata: Optional[Dict[str, Any]] = Field(alias="artifact_metadata")
    size_bytes: int
    is_primary: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MetricCreate(BaseModel):
    version_id: int
    metric_name: str = Field(..., min_length=1)
    value: float
    details: Optional[Dict[str, Any]] = None


class MetricOut(BaseModel):
    id: int
    version_id: int
    metric_name: str
    value: float
    details: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewRequest(BaseModel):
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    id: int
    version_id: int
    reviewer_id: Optional[int]
    status: str
    comment: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeploymentRequest(BaseModel):
    version_id: int
    environment: str = Field(..., min_length=1)
    endpoint_url: Optional[str] = None
    notes: Optional[str] = None
    from_version_id: Optional[int] = None


class DeploymentOut(BaseModel):
    id: int
    model_id: int
    version_id: int
    environment: str
    status: str
    deployed_by_id: Optional[int]
    deployed_at: datetime
    endpoint_url: Optional[str]
    notes: Optional[str]
    rollback_of_id: Optional[int]
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class DeploymentHistoryOut(BaseModel):
    id: int
    deployment_id: int
    action: str
    performed_by_id: Optional[int]
    from_version_id: Optional[int]
    to_version_id: Optional[int]
    environment: str
    notes: Optional[str]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModelRegistrySummaryOut(BaseModel):
    total_models: int
    production_models: int
    staging_models: int
    archived_models: int
    average_map: float
    average_precision: float

    model_config = ConfigDict(from_attributes=True)
