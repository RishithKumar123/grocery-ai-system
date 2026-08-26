import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, BackgroundTasks
from app.ai.pipeline import run_video_pipeline_async
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.logging import logger
from app.data.models.video_model import VideoModel
from app.data.repositories.storage_repository import StorageRepository
from app.domain.entities.user import User
from app.presentation.api.v1.auth import get_current_user
from app.presentation.schemas.video_schemas import VideoOut, UploadCompletePayload

router = APIRouter(prefix="/videos", tags=["video-upload"])
storage = StorageRepository()

# Temp directory to save chunks before merging
CHUNKS_DIR = os.path.join(os.getcwd(), "local_storage", "chunks")


@router.get("", response_model=List[VideoOut])
def list_videos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve list of all uploaded security footage videos."""
    videos = db.query(VideoModel).order_by(VideoModel.created_at.desc()).all()
    return videos


@router.post("/upload/chunk")
async def upload_video_chunk(
    request: Request,
    upload_id: str = Query(..., description="Client-generated unique upload session ID"),
    chunk_index: int = Query(..., description="0-based index of this chunk"),
    total_chunks: int = Query(..., description="Total count of chunks in the session"),
    current_user: User = Depends(get_current_user)
):
    """Endpoint accepting raw binary slices of video streams to support resumable uploads."""
    # Ensure temporary upload session directory exists
    session_dir = os.path.join(CHUNKS_DIR, upload_id)
    os.makedirs(session_dir, exist_ok=True)

    # Read binary payload chunk
    chunk_data = await request.body()
    chunk_file_path = os.path.join(session_dir, str(chunk_index))

    # Write chunk data to disk
    with open(chunk_file_path, "wb") as f:
        f.write(chunk_data)

    return {"message": f"Chunk {chunk_index + 1}/{total_chunks} uploaded successfully."}


@router.post("/upload/complete", response_model=VideoOut)
def complete_video_upload(
    payload: UploadCompletePayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Finalizes chunk transfers, merges files, saves to cloud, and registers DB entry."""
    session_dir = os.path.join(CHUNKS_DIR, payload.upload_id)

    if not os.path.exists(session_dir):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload session {payload.upload_id} not found. Try re-uploading the file."
        )

    # List all chunks and sort numerically to maintain block order
    chunk_files = sorted(os.listdir(session_dir), key=lambda x: int(x))
    
    # Target path for merging
    merged_file_name = f"merged-{payload.upload_id}-{payload.filename}"
    temp_merged_path = os.path.join(CHUNKS_DIR, merged_file_name)

    try:
        # Merge all chunks into one single file
        with open(temp_merged_path, "wb") as merged_file:
            for chunk_name in chunk_files:
                chunk_path = os.path.join(session_dir, chunk_name)
                with open(chunk_path, "rb") as chunk_file:
                    merged_file.write(chunk_file.read())

        # Upload final merged file to storage repository
        with open(temp_merged_path, "rb") as f:
            final_file_url = storage.upload_file(
                f.read(), 
                payload.filename, 
                "video/mp4" # Standard target type
            )

    except Exception as e:
        logger.error(f"Error during video chunks merge/upload: {str(e)}")
        # Clean up temp merged file if it exists
        if os.path.exists(temp_merged_path):
            os.remove(temp_merged_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finalizing video upload: {str(e)}"
        )

    finally:
        # Clean up chunks folder
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
        # Clean up temp merged file
        if os.path.exists(temp_merged_path):
            os.remove(temp_merged_path)

    # Create VideoModel record in DB
    video = VideoModel(
        store_id=payload.store_id,
        camera_name=payload.camera_name,
        video_url=final_file_url,
        status="Pending" # Pending AI scan processing
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    # Queue AI Processing Pipeline asynchronously
    background_tasks.add_task(run_video_pipeline_async, video.id)

    return video
