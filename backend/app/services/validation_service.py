import os
import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import cv2
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging import logger
from app.data.models.dataset_model import DatasetImageModel, DatasetVideoModel
from app.data.models.annotation_model import AnnotationModel, AnnotationObjectModel
from app.data.repositories.sqlalchemy_dataset_repository import SQLAlchemyDatasetRepository
from app.data.repositories.sqlalchemy_annotation_repository import SQLAlchemyAnnotationRepository
from app.data.repositories.sqlalchemy_validation_repository import SQLAlchemyValidationRepository
from app.data.repositories.storage_repository import StorageRepository


def _local_path_from_url(file_url: str) -> Optional[str]:
    if file_url.startswith("/static/uploads/"):
        return os.path.join(settings.LOCAL_STORAGE_DIR, file_url.replace("/static/uploads/", ""))
    if file_url.startswith(settings.LOCAL_STORAGE_DIR):
        return file_url
    return None


def _calculate_image_hash(image_path: str) -> Optional[str]:
    if not os.path.exists(image_path):
        return None
    with open(image_path, "rb") as f:
        content = f.read()
    return hashlib.sha256(content).hexdigest()


def _score_blur(gray: Any) -> float:
    score = cv2.Laplacian(gray, cv2.CV_64F).var()
    return float(np.clip(score / 1000.0 * 100.0, 0, 100))


def _score_brightness(gray: Any) -> float:
    return float(np.clip(np.mean(gray) / 255.0 * 100.0, 0, 100))


def _score_contrast(gray: Any) -> float:
    return float(np.clip(np.std(gray) / 64.0 * 100.0, 0, 100))


def _score_noise(gray: Any) -> float:
    blur = cv2.GaussianBlur(gray, (5, 5), 0).astype(np.float32)
    noise = np.mean(np.abs(gray.astype(np.float32) - blur))
    return float(np.clip(100.0 - noise / 25.0 * 100.0, 0, 100))


def _score_resolution(width: int, height: int) -> float:
    return float(np.clip((width * height) / (1920.0 * 1080.0) * 100.0, 0, 100))


def _score_exposure(gray: Any) -> float:
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    low = np.sum(hist[:50])
    high = np.sum(hist[206:])
    ratio = float(low / (high + 1.0))
    return float(np.clip(100.0 - abs(ratio - 1.0) * 100.0, 0, 100))


def _score_color_balance(image: Any) -> float:
    if len(image.shape) != 3 or image.shape[2] != 3:
        return 50.0
    mean_b, mean_g, mean_r = cv2.mean(image)[:3]
    means = np.array([mean_b, mean_g, mean_r])
    balance = np.std(means) / (np.mean(means) + 1e-6)
    return float(np.clip(100.0 - balance * 100.0, 0, 100))


def _validate_bounding_box(bbox: Dict[str, Any], width: int, height: int) -> Tuple[bool, Optional[str]]:
    if bbox is None:
        return False, "Bounding box missing"
    x = bbox.get("x", 0)
    y = bbox.get("y", 0)
    w = bbox.get("width", 0)
    h = bbox.get("height", 0)
    if w <= 0 or h <= 0:
        return False, "Bounding box has zero or negative width/height"
    if x < 0 or y < 0 or x + w > width or y + h > height:
        return False, "Bounding box lies outside image boundaries"
    return True, None


def _validate_polygon(polygon: List[Dict[str, float]], width: int, height: int) -> Tuple[bool, Optional[str]]:
    if not polygon:
        return False, "Polygon data missing"
    for point in polygon:
        x = point.get("x", 0)
        y = point.get("y", 0)
        if x < 0 or y < 0 or x > width or y > height:
            return False, "Polygon point outside image boundaries"
    return True, None


def _validate_keypoints(keypoints: List[Dict[str, float]], width: int, height: int) -> Tuple[bool, Optional[str]]:
    if not keypoints:
        return False, "Keypoints missing"
    for point in keypoints:
        x = point.get("x", 0)
        y = point.get("y", 0)
        if x < 0 or y < 0 or x > width or y > height:
            return False, "Keypoint outside image boundaries"
    return True, None


class ValidationService:
    def __init__(self, db: Session):
        self.db = db
        self.dataset_repo = SQLAlchemyDatasetRepository(db)
        self.annotation_repo = SQLAlchemyAnnotationRepository(db)
        self.repo = SQLAlchemyValidationRepository(db)
        self.storage = StorageRepository()

    def _record_error(self, job_id: int, dataset_id: int, asset_type: str, message: str, error_type: str, severity: str = "medium", asset_id: Optional[int] = None, asset_url: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        self.repo.add_validation_error({
            "job_id": job_id,
            "dataset_id": dataset_id,
            "asset_type": asset_type,
            "asset_id": asset_id,
            "asset_url": asset_url,
            "error_type": error_type,
            "severity": severity,
            "message": message,
            "details": details or {},
        })

    def _calculate_quality_score(self, components: Dict[str, float], weights: Dict[str, float]) -> float:
        weighted = sum(components.get(k, 0.0) * weights.get(k, 0.0) for k in weights)
        total_weight = sum(weights.values())
        return float(round(weighted / total_weight, 2)) if total_weight > 0 else 0.0

    def _load_dataset_images(self, dataset_id: int) -> List[DatasetImageModel]:
        return self.db.query(DatasetImageModel).filter(DatasetImageModel.dataset_id == dataset_id).all()

    def _load_annotations(self, dataset_id: int) -> List[AnnotationModel]:
        return self.db.query(AnnotationModel).filter(AnnotationModel.dataset_id == dataset_id, AnnotationModel.is_deleted == False).all()

    def _find_duplicate_hashes(self, dataset_id: int) -> Dict[str, List[int]]:
        images = self._load_dataset_images(dataset_id)
        hash_map: Dict[str, List[int]] = {}
        for image in images:
            local_path = _local_path_from_url(image.file_url)
            if local_path is None or not os.path.exists(local_path):
                continue
            current_hash = _calculate_image_hash(local_path)
            if current_hash:
                hash_map.setdefault(current_hash, []).append(image.id)
        return {h: ids for h, ids in hash_map.items() if len(ids) > 1}

    def _analyze_class_distribution(self, job_id: int, dataset_id: int, annotations: List[AnnotationModel]) -> Dict[str, Any]:
        label_counts: Dict[str, int] = {}
        product_counts: Dict[int, int] = {}
        total = 0
        for annotation in annotations:
            for obj in annotation.objects:
                label = obj.label_name or "unknown"
                label_counts[label] = label_counts.get(label, 0) + 1
                if obj.product_id:
                    product_counts[obj.product_id] = product_counts.get(obj.product_id, 0) + 1
                total += 1

        distribution: Dict[str, Any] = {"labels": [], "products": []}
        for label, count in label_counts.items():
            percentage = float(round((count / total) * 100.0, 2)) if total > 0 else 0.0
            self.repo.add_class_distribution({
                "job_id": job_id,
                "dataset_id": dataset_id,
                "label_name": label,
                "product_id": None,
                "count": count,
                "percentage": percentage,
            })
            distribution["labels"].append({"label": label, "count": count, "percentage": percentage})
        for product_id, count in product_counts.items():
            percentage = float(round((count / total) * 100.0, 2)) if total > 0 else 0.0
            self.repo.add_class_distribution({
                "job_id": job_id,
                "dataset_id": dataset_id,
                "label_name": None,
                "product_id": product_id,
                "count": count,
                "percentage": percentage,
            })
            distribution["products"].append({"product_id": product_id, "count": count, "percentage": percentage})
        return distribution

    def _validate_product_catalog(self, job_id: int, annotation: AnnotationModel) -> None:
        for obj in annotation.objects:
            if obj.product_id is None and obj.label_name.lower() != "unknown":
                self._record_error(
                    job_id,
                    annotation.dataset_id,
                    annotation.asset_type,
                    "Annotation missing product mapping for labeled object.",
                    "missing_product_mapping",
                    "high",
                    asset_id=annotation.asset_id,
                    asset_url=annotation.asset_url,
                    details={"object_label": obj.label_name},
                )
            if obj.label_name is None or obj.label_name.strip() == "":
                self._record_error(
                    job_id,
                    annotation.dataset_id,
                    annotation.asset_type,
                    "Annotation object missing class label.",
                    "missing_class_label",
                    "high",
                    asset_id=annotation.asset_id,
                    asset_url=annotation.asset_url,
                )

    def _validate_annotation_objects(self, job_id: int, annotation: AnnotationModel, width: int, height: int) -> Dict[str, Any]:
        issues: Dict[str, int] = {"invalid_boxes": 0, "invalid_polygons": 0, "invalid_keypoints": 0, "duplicate_objects": 0}
        box_seen: set = set()
        for obj in annotation.objects:
            if obj.bbox:
                valid, reason = _validate_bounding_box(obj.bbox, width, height)
                if not valid:
                    issues["invalid_boxes"] += 1
                    self._record_error(
                        job_id,
                        annotation.dataset_id,
                        annotation.asset_type,
                        reason,
                        "invalid_bounding_box",
                        "high",
                        asset_id=annotation.asset_id,
                        asset_url=annotation.asset_url,
                        details={"bbox": obj.bbox},
                    )
                else:
                    box_key = (obj.bbox.get("x"), obj.bbox.get("y"), obj.bbox.get("width"), obj.bbox.get("height"))
                    if box_key in box_seen:
                        issues["duplicate_objects"] += 1
                        self._record_error(
                            job_id,
                            annotation.dataset_id,
                            annotation.asset_type,
                            "Duplicate annotation object detected.",
                            "duplicate_annotation",
                            "medium",
                            asset_id=annotation.asset_id,
                            asset_url=annotation.asset_url,
                            details={"bbox": obj.bbox},
                        )
                    box_seen.add(box_key)
            if obj.polygon:
                valid, reason = _validate_polygon(obj.polygon, width, height)
                if not valid:
                    issues["invalid_polygons"] += 1
                    self._record_error(
                        job_id,
                        annotation.dataset_id,
                        annotation.asset_type,
                        reason,
                        "invalid_polygon",
                        "high",
                        asset_id=annotation.asset_id,
                        asset_url=annotation.asset_url,
                        details={"polygon": obj.polygon},
                    )
            if obj.keypoints:
                valid, reason = _validate_keypoints(obj.keypoints, width, height)
                if not valid:
                    issues["invalid_keypoints"] += 1
                    self._record_error(
                        job_id,
                        annotation.dataset_id,
                        annotation.asset_type,
                        reason,
                        "invalid_keypoint",
                        "high",
                        asset_id=annotation.asset_id,
                        asset_url=annotation.asset_url,
                        details={"keypoints": obj.keypoints},
                    )
        return issues

    def validate_dataset(self, job_id: int) -> None:
        job = self.repo.get_job(job_id)
        if not job:
            logger.error(f"Validation job {job_id} not found")
            return

        job.status = "running"
        job.started_at = datetime.utcnow()
        self.db.commit()

        dataset = self.dataset_repo.get_dataset(job.dataset_id, include_deleted=False)
        if not dataset:
            self.repo.update_job_status(job.id, "validation_failed", overall_score=0.0)
            logger.error(f"Dataset {job.dataset_id} not found for validation")
            return

        images = self._load_dataset_images(dataset.id)
        annotations = self._load_annotations(dataset.id)
        total_assets = len(images)
        job.total_assets = total_assets
        self.db.commit()

        if total_assets == 0:
            self._record_error(job.id, dataset.id, "dataset", "Dataset contains no image assets.", "empty_dataset", "critical", None, None)

        duplicate_hashes = self._find_duplicate_hashes(dataset.id)
        for hash_value, image_ids in duplicate_hashes.items():
            for image_id in image_ids:
                image = next((img for img in images if img.id == image_id), None)
                if image:
                    self._record_error(
                        job.id,
                        dataset.id,
                        "image",
                        "Exact duplicate image detected within dataset.",
                        "duplicate_image",
                        "high",
                        asset_id=image.id,
                        asset_url=image.file_url,
                        details={"duplicate_group": image_ids},
                    )

        annotation_map = {annotation.asset_id: [] for annotation in annotations}
        for annotation in annotations:
            annotation_map.setdefault(annotation.asset_id, []).append(annotation)

        image_quality_scores: List[float] = []
        annotation_quality_scores: List[float] = []
        completeness_warnings = 0
        balance_penalties = 0

        for image in images:
            local_path = _local_path_from_url(image.file_url)
            if not local_path or not os.path.exists(local_path):
                self._record_error(job.id, dataset.id, "image", "Image file is missing or inaccessible.", "missing_image", "critical", image.id, image.file_url)
                continue

            img = cv2.imread(local_path)
            if img is None:
                self._record_error(job.id, dataset.id, "image", "Image file is corrupted or unreadable.", "corrupted_image", "critical", image.id, image.file_url)
                continue

            height, width = img.shape[:2]
            if width <= 0 or height <= 0:
                self._record_error(job.id, dataset.id, "image", "Image dimensions are invalid.", "invalid_dimensions", "critical", image.id, image.file_url)
                continue

            if image.original_filename and not image.original_filename.lower().endswith(tuple([".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"])):
                self._record_error(job.id, dataset.id, "image", "Unsupported image format.", "unsupported_format", "high", image.id, image.file_url)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur = _score_blur(gray)
            brightness = _score_brightness(gray)
            contrast = _score_contrast(gray)
            noise = _score_noise(gray)
            resolution = _score_resolution(width, height)
            exposure = _score_exposure(gray)
            color_balance = _score_color_balance(img)

            image_score = self._calculate_quality_score(
                {
                    "blur": blur,
                    "brightness": brightness,
                    "contrast": contrast,
                    "noise": noise,
                    "resolution": resolution,
                    "exposure": exposure,
                    "color_balance": color_balance,
                },
                {
                    "blur": 0.15,
                    "brightness": 0.15,
                    "contrast": 0.15,
                    "noise": 0.15,
                    "resolution": 0.15,
                    "exposure": 0.15,
                    "color_balance": 0.1,
                }
            )
            image_quality_scores.append(image_score)

            if image_score < 40:
                self._record_error(job.id, dataset.id, "image", "Low overall image quality detected.", "low_quality", "medium", image.id, image.file_url, details={"quality_score": image_score})

            image_annotations = annotation_map.get(image.id, [])
            if not image_annotations:
                self._record_error(job.id, dataset.id, "annotation", "Image asset has no associated annotations.", "missing_annotations", "high", image.id, image.file_url)
                completeness_warnings += 1

            for annotation in image_annotations:
                self._validate_product_catalog(job.id, annotation)
                issues = self._validate_annotation_objects(job.id, annotation, width, height)
                error_count = issues.get("invalid_boxes", 0) + issues.get("invalid_polygons", 0) + issues.get("invalid_keypoints", 0) + issues.get("duplicate_objects", 0)
                annotation_quality_scores.append(max(0.0, 100.0 - error_count * 20.0))

        if not annotations:
            self._record_error(job.id, dataset.id, "annotation", "No annotations found in dataset.", "empty_annotation_set", "high")
        else:
            self._analyze_class_distribution(job.id, dataset.id, annotations)

        average_image_quality = float(round(sum(image_quality_scores) / len(image_quality_scores), 2)) if image_quality_scores else 0.0
        average_annotation_quality = float(round(sum(annotation_quality_scores) / len(annotation_quality_scores), 2)) if annotation_quality_scores else 0.0
        completeness_score = float(max(0.0, 100.0 - completeness_warnings * 10.0))
        balance_score = float(max(0.0, 100.0 - balance_penalties * 10.0))
        metadata_score = float(100.0 if dataset.name and dataset.description else 70.0)
        integrity_score = float(100.0 if not duplicate_hashes else 60.0)

        overall_score = self._calculate_quality_score(
            {
                "image_quality": average_image_quality,
                "annotation_quality": average_annotation_quality,
                "completeness": completeness_score,
                "balance": balance_score,
                "metadata": metadata_score,
                "integrity": integrity_score,
            },
            {
                "image_quality": 0.25,
                "annotation_quality": 0.25,
                "completeness": 0.15,
                "balance": 0.15,
                "metadata": 0.1,
                "integrity": 0.1,
            }
        )

        recommendations = {
            "image_quality": "Improve lighting, reduce blur, or replace low-resolution assets." if average_image_quality < 70 else "Image quality is acceptable.",
            "annotation_quality": "Review objects with invalid boundaries and label mappings." if average_annotation_quality < 70 else "Annotation quality is acceptable.",
            "duplicates": f"Found {len(duplicate_hashes)} duplicate image groups." if duplicate_hashes else "No exact duplicates detected.",
            "data_completeness": "Add annotations for unannotated images." if completeness_warnings else "Dataset metadata and annotations are complete.",
        }

        self.repo.save_quality_report({
            "job_id": job.id,
            "dataset_id": dataset.id,
            "image_quality_score": average_image_quality,
            "annotation_quality_score": average_annotation_quality,
            "completeness_score": completeness_score,
            "balance_score": balance_score,
            "metadata_score": metadata_score,
            "integrity_score": integrity_score,
            "overall_score": overall_score,
            "recommendations": recommendations,
            "report_payload": {
                "image_quality_scores": image_quality_scores,
                "annotation_quality_scores": annotation_quality_scores,
                "duplicate_image_count": len(duplicate_hashes),
                "annotation_count": len(annotations),
            },
        })

        if job.is_cancelled:
            job.status = "cancelled"
        elif overall_score < 60 or self.repo.list_errors(job_id=job.id):
            job.status = "pending_review"
        else:
            job.status = "approved"

        job.overall_score = overall_score
        job.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)


def run_validation_job_async(job_id: int):
    db = SessionLocal()
    try:
        service = ValidationService(db)
        service.validate_dataset(job_id)
    finally:
        db.close()
