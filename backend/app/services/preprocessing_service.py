import os
import json
import hashlib
import numpy as np
import cv2
from datetime import datetime
from typing import Any, Dict, Optional
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging import logger
from app.data.repositories.sqlalchemy_dataset_repository import SQLAlchemyDatasetRepository
from app.data.repositories.sqlalchemy_preprocessing_repository import SQLAlchemyPreprocessingRepository
from app.data.models.dataset_model import DatasetImageModel, DatasetVideoModel
from app.data.models.preprocessing_model import PipelineConfigurationModel
from app.data.repositories.storage_repository import StorageRepository


SUPPORTED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "bmp", "tiff"}
SUPPORTED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "webm"}


def _local_path_from_url(file_url: str) -> Optional[str]:
    if file_url.startswith("/static/uploads/"):
        return os.path.join(settings.LOCAL_STORAGE_DIR, file_url.replace("/static/uploads/", ""))
    if file_url.startswith(settings.LOCAL_STORAGE_DIR):
        return file_url
    return None


class PreprocessingService:
    def __init__(self, db: Any):
        self.db = db
        self.dataset_repo = SQLAlchemyDatasetRepository(db)
        self.repo = SQLAlchemyPreprocessingRepository(db)
        self.storage = StorageRepository()

    def _load_pipeline_settings(self, job: Any) -> Dict[str, Any]:
        settings_payload: Dict[str, Any] = {}
        config: Optional[PipelineConfigurationModel] = None
        if job.config_id is not None:
            config = self.repo.get_pipeline_configuration(job.config_id)
        if config is None:
            config = self.repo.get_default_configuration()

        if config is None:
            config = PipelineConfigurationModel(
                name="default",
                resize_width=1024,
                resize_height=1024,
                compression_level=85,
                quality_threshold=60,
                max_image_size_mb=8,
                frame_interval=30,
                target_video_width=1280,
                target_video_height=720,
                target_video_fps=30,
                accepted_image_formats=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
                accepted_video_formats=["mp4", "avi", "mov", "mkv", "webm"],
                enable_background_cleanup=False,
                max_video_duration_seconds=900,
            )

        settings_payload.update({
            "resize_width": config.resize_width,
            "resize_height": config.resize_height,
            "compression_level": config.compression_level,
            "quality_threshold": config.quality_threshold,
            "max_image_size_mb": config.max_image_size_mb,
            "frame_interval": config.frame_interval,
            "target_video_width": config.target_video_width,
            "target_video_height": config.target_video_height,
            "target_video_fps": config.target_video_fps,
            "accepted_image_formats": config.accepted_image_formats,
            "accepted_video_formats": config.accepted_video_formats,
            "enable_background_cleanup": config.enable_background_cleanup,
            "max_video_duration_seconds": config.max_video_duration_seconds,
        })

        if job.settings:
            settings_payload.update(job.settings)

        return settings_payload

    def _score_image(self, image: Any) -> Dict[str, Any]:
        if len(image.shape) == 2:
            gray = image
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        blur_score = float(np.clip(cv2.Laplacian(gray, cv2.CV_64F).var(), 0, 1000))
        blur_score = min(100.0, blur_score / 1000.0 * 100.0)
        brightness_score = float(np.clip(np.mean(gray) / 255.0 * 100.0, 0, 100))
        contrast_score = float(np.clip(np.std(gray) / 64.0 * 100.0, 0, 100))
        noise_estimate = np.mean(np.abs(gray.astype(np.float32) - cv2.GaussianBlur(gray, (5, 5), 0).astype(np.float32)))
        noise_score = float(np.clip(100.0 - noise_estimate / 25.0 * 100.0, 0, 100))
        height, width = gray.shape[:2]
        resolution_score = float(np.clip((width * height) / (1920.0 * 1080.0) * 100.0, 0, 100))
        overall_score = float(np.clip((blur_score + brightness_score + contrast_score + noise_score + resolution_score) / 5.0, 0, 100))

        return {
            "blur_score": round(blur_score, 2),
            "brightness_score": round(brightness_score, 2),
            "contrast_score": round(contrast_score, 2),
            "noise_score": round(noise_score, 2),
            "resolution_score": round(resolution_score, 2),
            "overall_score": round(overall_score, 2),
        }

    def _is_invalid_asset(self, image_asset: DatasetImageModel) -> Optional[str]:
        missing = [field for field in ["product_id", "brand_id", "category_id", "supplier_id", "store_id", "shelf_id"] if getattr(image_asset, field) is None]
        if missing:
            return f"Missing required product-centric metadata: {', '.join(missing)}"
        if image_asset.annotation_count == 0:
            return "Missing annotations or labels for image asset."
        return None

    def _resize_aspect(self, image: Any, width: int, height: int) -> Any:
        orig_h, orig_w = image.shape[:2]
        if orig_w == 0 or orig_h == 0:
            return image
        scale = min(width / orig_w, height / orig_h)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        if new_w == width and new_h == height:
            return resized
        top = (height - new_h) // 2
        bottom = height - new_h - top
        left = (width - new_w) // 2
        right = width - new_w - left
        return cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0])

    def _apply_image_enhancements(self, image: Any, config: Dict[str, Any]) -> Any:
        working = image.copy()
        working = self._resize_aspect(working, config["resize_width"], config["resize_height"])
        if config.get("enable_background_cleanup"):
            working = cv2.fastNlMeansDenoisingColored(working, None, 10, 10, 7, 21)
        alpha = 1.0 + ((config.get("quality_threshold", 60) - 50) / 200.0)
        beta = 0
        working = cv2.convertScaleAbs(working, alpha=alpha, beta=beta)
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], np.float32)
        working = cv2.filter2D(working, -1, kernel)
        if len(working.shape) == 3 and working.shape[2] == 3:
            lab = cv2.cvtColor(working, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            working = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)
        gamma = 1.0 + ((config.get("quality_threshold", 60) - 50) / 100.0)
        invGamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        working = cv2.LUT(working, table)
        return working

    def _is_duplicate_image(self, asset: DatasetImageModel) -> bool:
        duplicate = self.db.query(DatasetImageModel).filter(
            DatasetImageModel.dataset_id == asset.dataset_id,
            DatasetImageModel.hash == asset.hash,
            DatasetImageModel.id != asset.id
        ).first()
        return duplicate is not None

    def _write_local_file(self, path: str, data: bytes) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

    def _process_image_asset(self, job: Any, asset: DatasetImageModel, config: Dict[str, Any]) -> None:
        local_path = _local_path_from_url(asset.file_url)
        if local_path is None or not os.path.exists(local_path):
            self.repo.add_preprocessing_log({
                "job_id": job.id,
                "dataset_id": job.dataset_id,
                "asset_type": "image",
                "asset_id": asset.id,
                "asset_url": asset.file_url,
                "status": "failed",
                "message": "Unable to resolve local image source for preprocessing.",
            })
            self.repo.increment_job_counters(job.id, failed=1, errors=1)
            return

        image = cv2.imread(local_path, cv2.IMREAD_UNCHANGED)
        if image is None or image.size == 0:
            self.repo.add_preprocessing_log({
                "job_id": job.id,
                "dataset_id": job.dataset_id,
                "asset_type": "image",
                "asset_id": asset.id,
                "asset_url": asset.file_url,
                "status": "failed",
                "message": "Corrupted or unreadable image file.",
            })
            self.repo.increment_job_counters(job.id, failed=1, errors=1)
            return

        metrics = self._score_image(image)
        remarks = []
        invalid_reason = self._is_invalid_asset(asset)
        if invalid_reason:
            remarks.append(invalid_reason)

        if self._is_duplicate_image(asset):
            remarks.append("Detected duplicate image within dataset.")

        if metrics["blur_score"] < 20:
            remarks.append("Image is likely too blurry.")
        if metrics["brightness_score"] < 20:
            remarks.append("Image appears underexposed.")
        if metrics["brightness_score"] > 90:
            remarks.append("Image appears overexposed.")

        overall_valid = len(remarks) == 0 and metrics["overall_score"] >= config["quality_threshold"]
        if not overall_valid:
            status = "rejected"
            message = "; ".join(remarks) if remarks else "Image quality fell below configured threshold."
            self.repo.increment_job_counters(job.id, failed=1, warnings=1)
        else:
            status = "processed"
            message = "Image validated and preprocessed successfully."
            self.repo.increment_job_counters(job.id, processed=1)

        enhanced_image = self._apply_image_enhancements(image, config)
        output_name = f"preprocessed/images/job_{job.id}/image_{asset.id}.jpg"
        output_path = os.path.join(settings.LOCAL_STORAGE_DIR, output_name)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, enhanced_image, [int(cv2.IMWRITE_JPEG_QUALITY), int(config["compression_level"])])

        with open(output_path, "rb") as f:
            processed_url = self.storage.upload_file(f.read(), output_name, "image/jpeg")

        self.repo.add_image_quality({
            "job_id": job.id,
            "dataset_id": job.dataset_id,
            "image_id": asset.id,
            "blur_score": metrics["blur_score"],
            "brightness_score": metrics["brightness_score"],
            "contrast_score": metrics["contrast_score"],
            "noise_score": metrics["noise_score"],
            "resolution_score": metrics["resolution_score"],
            "overall_score": metrics["overall_score"],
            "is_valid": overall_valid,
            "remarks": message,
        })

        self.repo.add_preprocessing_log({
            "job_id": job.id,
            "dataset_id": job.dataset_id,
            "asset_type": "image",
            "asset_id": asset.id,
            "asset_url": asset.file_url,
            "status": status,
            "message": message,
            "quality_metrics": metrics,
        })

    def _compute_frame_distance(self, frame_a: Any, frame_b: Any) -> float:
        if frame_a is None or frame_b is None:
            return 1000.0
        resized_a = cv2.resize(frame_a, (320, 180))
        resized_b = cv2.resize(frame_b, (320, 180))
        diff = cv2.absdiff(resized_a, resized_b)
        return float(np.mean(diff))

    def _process_video_asset(self, job: Any, video: DatasetVideoModel, config: Dict[str, Any]) -> None:
        local_path = _local_path_from_url(video.file_url)
        if local_path is None or not os.path.exists(local_path):
            self.repo.add_preprocessing_log({
                "job_id": job.id,
                "dataset_id": job.dataset_id,
                "asset_type": "video",
                "asset_id": video.id,
                "asset_url": video.file_url,
                "status": "failed",
                "message": "Unable to resolve local video source for preprocessing.",
            })
            self.repo.increment_job_counters(job.id, failed=1, errors=1)
            return

        cap = cv2.VideoCapture(local_path)
        if not cap.isOpened():
            self.repo.add_preprocessing_log({
                "job_id": job.id,
                "dataset_id": job.dataset_id,
                "asset_type": "video",
                "asset_id": video.id,
                "asset_url": video.file_url,
                "status": "failed",
                "message": "Unable to open video file for preprocessing.",
            })
            self.repo.increment_job_counters(job.id, failed=1, errors=1)
            return

        original_fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration_seconds = frame_count / original_fps if original_fps else 0.0

        if duration_seconds > config["max_video_duration_seconds"]:
            self.repo.add_preprocessing_log({
                "job_id": job.id,
                "dataset_id": job.dataset_id,
                "asset_type": "video",
                "asset_id": video.id,
                "asset_url": video.file_url,
                "status": "rejected",
                "message": "Video exceeds the configured maximum duration.",
            })
            self.repo.increment_job_counters(job.id, failed=1, warnings=1)
            cap.release()
            return

        target_fps = min(original_fps if original_fps > 0 else config["target_video_fps"], config["target_video_fps"])
        target_width = config["target_video_width"]
        target_height = config["target_video_height"]
        output_name = f"preprocessed/videos/job_{job.id}/video_{video.id}.mp4"
        output_path = os.path.join(settings.LOCAL_STORAGE_DIR, output_name)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, target_fps, (target_width, target_height))

        duplicate_removed = 0
        scene_count = 0
        last_frame = None
        saved_frames = 0
        thumbnail_url = None
        frame_index = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_index % config["frame_interval"] != 0:
                frame_index += 1
                continue

            if last_frame is not None:
                distance = self._compute_frame_distance(last_frame, frame)
                if distance < 3.0:
                    duplicate_removed += 1
                    frame_index += 1
                    continue
                if distance > 20.0:
                    scene_count += 1

            resized = self._resize_aspect(frame, target_width, target_height)
            writer.write(resized)
            if thumbnail_url is None:
                thumb_path = os.path.join(settings.LOCAL_STORAGE_DIR, f"preprocessed/videos/job_{job.id}/thumbnail_{video.id}.jpg")
                cv2.imwrite(thumb_path, resized)
                with open(thumb_path, "rb") as f:
                    thumbnail_url = self.storage.upload_file(f.read(), f"preprocessed/videos/job_{job.id}/thumbnail_{video.id}.jpg", "image/jpeg")

            last_frame = frame
            saved_frames += 1
            frame_index += 1

            if self.repo.get_job(job.id).is_cancelled:
                break

        writer.release()
        cap.release()

        if saved_frames == 0:
            self.repo.add_preprocessing_log({
                "job_id": job.id,
                "dataset_id": job.dataset_id,
                "asset_type": "video",
                "asset_id": video.id,
                "asset_url": video.file_url,
                "status": "failed",
                "message": "No valid frames were extracted after sampling and duplicate removal.",
            })
            self.repo.increment_job_counters(job.id, failed=1, errors=1)
            return

        with open(output_path, "rb") as f:
            compressed_url = self.storage.upload_file(f.read(), output_name, "video/mp4")

        self.repo.add_video_processing({
            "job_id": job.id,
            "dataset_id": job.dataset_id,
            "video_id": video.id,
            "thumbnail_url": thumbnail_url,
            "compressed_file_url": compressed_url,
            "duration_seconds": duration_seconds,
            "original_resolution": f"{original_width}x{original_height}",
            "converted_resolution": f"{target_width}x{target_height}",
            "original_fps": original_fps,
            "converted_fps": target_fps,
            "frame_count": saved_frames,
            "scene_count": scene_count,
            "duplicate_frames_removed": duplicate_removed,
            "file_size": os.path.getsize(output_path),
            "status": "completed",
        })
        self.repo.increment_job_counters(job.id, processed=1)

    def _mark_job_failed(self, job: Any, message: str) -> None:
        job.status = "failed"
        job.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
        logger.error(message)

    def process_job(self, job_id: int) -> None:
        job = self.repo.get_job(job_id)
        if not job:
            logger.error(f"Preprocessing job {job_id} not found.")
            return

        if job.status not in ["pending", "cancelling", "failed", "completed"]:
            logger.info(f"Skipping job {job_id} because status is {job.status}.")
            return

        job.status = "running"
        self.db.commit()
        self.db.refresh(job)

        try:
            config = self._load_pipeline_settings(job)
            assets = self.dataset_repo.get_dataset_assets(job.dataset_id)
            image_assets = assets.get("images", []) if job.asset_type in ["all", "image"] else []
            video_assets = assets.get("videos", []) if job.asset_type in ["all", "video"] else []
            job.total_assets = len(image_assets) + len(video_assets)
            self.db.commit()

            for asset in image_assets:
                if job.is_cancelled:
                    break
                self._process_image_asset(job, asset, config)

            for asset in video_assets:
                if job.is_cancelled:
                    break
                self._process_video_asset(job, asset, config)

            if job.is_cancelled:
                job.status = "cancelled"
            elif job.errors_count > 0:
                job.status = "completed_with_errors"
            else:
                job.status = "completed"

            job.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(job)

        except Exception as exc:
            self._mark_job_failed(job, f"Job {job_id} failed: {str(exc)}")


def run_preprocessing_job_async(job_id: int):
    db = SessionLocal()
    try:
        service = PreprocessingService(db)
        service.process_job(job_id)
    finally:
        db.close()
