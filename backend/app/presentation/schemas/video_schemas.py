from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class VideoOut(BaseModel):
    id: int
    store_id: int
    camera_name: str
    video_url: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UploadCompletePayload(BaseModel):
    upload_id: str = Field(..., min_length=1)
    filename: str = Field(..., min_length=1)
    store_id: int = Field(...)
    camera_name: str = Field(..., min_length=1)
