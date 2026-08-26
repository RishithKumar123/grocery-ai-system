import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from app.core.config import settings
from app.data.models.annotation_model import (
    AnnotationModel,
    AnnotationObjectModel,
    AnnotationLabelModel,
    AnnotationReviewModel,
    AnnotationVersionModel,
    AnnotationHistoryModel,
    AnnotationCommentModel,
    AnnotationTaskModel,
)


class SQLAlchemyAnnotationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_annotation(self, payload: Dict[str, Any], creator_id: int) -> AnnotationModel:
        annotation = AnnotationModel(
            dataset_id=payload["dataset_id"],
            asset_type=payload["asset_type"],
            asset_id=payload["asset_id"],
            asset_url=payload["asset_url"],
            annotation_type=payload.get("annotation_type", "bounding_box"),
            title=payload.get("title"),
            description=payload.get("description"),
            status=payload.get("status", "draft"),
            assigned_to_id=payload.get("assigned_to_id"),
            reviewer_id=payload.get("reviewer_id"),
            review_status=payload.get("review_status", "pending_review"),
            quality_score=payload.get("quality_score"),
            consensus_score=payload.get("consensus_score"),
            ai_assisted=payload.get("ai_assisted", False),
            suggestion_payload=payload.get("suggestion_payload") or {},
            annotation_metadata=payload.get("metadata") or {},
            created_by_id=creator_id,
            updated_by_id=creator_id,
            version_tag=payload.get("version_tag"),
        )
        self.db.add(annotation)
        self.db.commit()
        self.db.refresh(annotation)

        for obj in payload.get("objects", []):
            self.db.add(AnnotationObjectModel(
                annotation_id=annotation.id,
                object_type=obj.get("object_type"),
                label_name=obj.get("label_name"),
                category=obj.get("category"),
                product_id=obj.get("product_id"),
                brand_id=obj.get("brand_id"),
                category_id=obj.get("category_id"),
                supplier_id=obj.get("supplier_id"),
                store_id=obj.get("store_id"),
                shelf_id=obj.get("shelf_id"),
                bbox=obj.get("bbox") or {},
                polygon=obj.get("polygon") or [],
                keypoints=obj.get("keypoints") or [],
                attributes=obj.get("attributes") or {},
                confidence=obj.get("confidence"),
                is_ai_suggestion=obj.get("is_ai_suggestion", False),
            ))

        for label in payload.get("labels", []):
            self.db.add(AnnotationLabelModel(
                annotation_id=annotation.id,
                name=label.get("name"),
                alias_names=label.get("alias_names") or [],
                color=label.get("color"),
                parent_label_id=label.get("parent_label_id"),
                is_active=label.get("is_active", True),
            ))

        self.db.commit()
        self.db.refresh(annotation)
        return annotation

    def get_annotation(self, annotation_id: int) -> Optional[AnnotationModel]:
        return self.db.query(AnnotationModel).filter(AnnotationModel.id == annotation_id, AnnotationModel.is_deleted == False).first()

    def update_annotation(self, annotation_id: int, payload: Dict[str, Any], updater_id: int) -> Optional[AnnotationModel]:
        annotation = self.get_annotation(annotation_id)
        if not annotation:
            return None

        for field in [
            "annotation_type",
            "title",
            "description",
            "status",
            "assigned_to_id",
            "reviewer_id",
            "review_status",
            "quality_score",
            "consensus_score",
            "ai_assisted",
            "version_tag",
        ]:
            if field in payload:
                setattr(annotation, field, payload[field])

        if payload.get("suggestion_payload") is not None:
            annotation.suggestion_payload = json.dumps(payload["suggestion_payload"])
        if payload.get("metadata") is not None:
            annotation.annotation_metadata = json.dumps(payload["metadata"])

        if payload.get("objects") is not None:
            self.db.query(AnnotationObjectModel).filter(AnnotationObjectModel.annotation_id == annotation_id).delete()
            for obj in payload["objects"]:
                self.db.add(AnnotationObjectModel(
                    annotation_id=annotation.id,
                    object_type=obj.get("object_type"),
                    label_name=obj.get("label_name"),
                    category=obj.get("category"),
                    product_id=obj.get("product_id"),
                    brand_id=obj.get("brand_id"),
                    category_id=obj.get("category_id"),
                    supplier_id=obj.get("supplier_id"),
                    store_id=obj.get("store_id"),
                    shelf_id=obj.get("shelf_id"),
                    bbox=json.dumps(obj.get("bbox") or {}),
                    polygon=json.dumps(obj.get("polygon") or []),
                    keypoints=json.dumps(obj.get("keypoints") or []),
                    attributes=json.dumps(obj.get("attributes") or {}),
                    confidence=obj.get("confidence"),
                    is_ai_suggestion=obj.get("is_ai_suggestion", False),
                ))

        if payload.get("labels") is not None:
            self.db.query(AnnotationLabelModel).filter(AnnotationLabelModel.annotation_id == annotation_id).delete()
            for label in payload["labels"]:
                self.db.add(AnnotationLabelModel(
                    annotation_id=annotation.id,
                    name=label.get("name"),
                    alias_names=json.dumps(label.get("alias_names") or []),
                    color=label.get("color"),
                    parent_label_id=label.get("parent_label_id"),
                    is_active=label.get("is_active", True),
                ))

        annotation.updated_by_id = updater_id
        self.db.commit()
        self.db.refresh(annotation)
        return annotation

    def delete_annotation(self, annotation_id: int, deleter_id: int) -> bool:
        annotation = self.get_annotation(annotation_id)
        if not annotation:
            return False
        annotation.is_deleted = True
        annotation.deleted_at = datetime.utcnow()
        self.db.commit()
        return True

    def create_annotation_review(self, annotation_id: int, payload: Dict[str, Any], reviewer_id: int) -> Optional[AnnotationReviewModel]:
        annotation = self.get_annotation(annotation_id)
        if not annotation:
            return None

        review = AnnotationReviewModel(
            annotation_id=annotation_id,
            reviewer_id=reviewer_id,
            status=payload["status"],
            comment=payload.get("comment"),
            quality_score=payload.get("quality_score"),
            consensus_score=payload.get("consensus_score"),
        )
        self.db.add(review)
        if payload["status"] == "approved":
            annotation.status = "approved"
            annotation.approved_at = datetime.utcnow()
            annotation.review_status = "approved"
        elif payload["status"] == "rejected":
            annotation.status = "rejected"
            annotation.rejected_at = datetime.utcnow()
            annotation.review_status = "rejected"
        else:
            annotation.review_status = payload["status"]
        self.db.commit()
        self.db.refresh(review)
        self.db.refresh(annotation)
        return review

    def search_annotations(self, filters: Dict[str, Any], offset: int = 0, limit: int = 50) -> List[AnnotationModel]:
        query = self.db.query(AnnotationModel).filter(AnnotationModel.is_deleted == False)

        if filters.get("dataset_id") is not None:
            query = query.filter(AnnotationModel.dataset_id == filters["dataset_id"])
        if filters.get("status") is not None:
            query = query.filter(AnnotationModel.status == filters["status"])
        if filters.get("reviewer_id") is not None:
            query = query.filter(AnnotationModel.reviewer_id == filters["reviewer_id"])
        if filters.get("assigned_to_id") is not None:
            query = query.filter(AnnotationModel.assigned_to_id == filters["assigned_to_id"])
        if filters.get("query"):
            query_text = f"%{filters['query']}%"
            query = query.filter(
                or_(
                    AnnotationModel.title.ilike(query_text),
                    AnnotationModel.description.ilike(query_text),
                    AnnotationModel.asset_url.ilike(query_text),
                )
            )

        return query.order_by(AnnotationModel.updated_at.desc()).offset(offset).limit(limit).all()

    def get_annotation_statistics(self, dataset_id: Optional[int] = None) -> Dict[str, Any]:
        query = self.db.query(AnnotationModel).filter(AnnotationModel.is_deleted == False)
        if dataset_id is not None:
            query = query.filter(AnnotationModel.dataset_id == dataset_id)

        total = query.count()
        pending = query.filter(AnnotationModel.status == "pending_review").count()
        approved = query.filter(AnnotationModel.status == "approved").count()
        rejected = query.filter(AnnotationModel.status == "rejected").count()
        draft = query.filter(AnnotationModel.status == "draft").count()
        in_progress = query.filter(AnnotationModel.status == "in_progress").count()
        archived = query.filter(AnnotationModel.status == "archived").count()
        total_images = self.db.query(func.count(AnnotationModel.id)).filter(AnnotationModel.asset_type == "image").scalar() or 0
        total_videos = self.db.query(func.count(AnnotationModel.id)).filter(AnnotationModel.asset_type == "video").scalar() or 0
        annotator_count = self.db.query(func.count(func.distinct(AnnotationModel.assigned_to_id))).filter(AnnotationModel.assigned_to_id != None).scalar() or 0
        reviewer_count = self.db.query(func.count(func.distinct(AnnotationModel.reviewer_id))).filter(AnnotationModel.reviewer_id != None).scalar() or 0

        return {
            "total_annotations": total,
            "pending_annotations": pending,
            "approved_annotations": approved,
            "rejected_annotations": rejected,
            "draft_annotations": draft,
            "in_progress_annotations": in_progress,
            "archived_annotations": archived,
            "total_images": total_images,
            "total_videos": total_videos,
            "annotator_count": annotator_count,
            "reviewer_count": reviewer_count,
            "average_annotation_time_seconds": None,
        }

    def _build_yolo_export(self, annotations: List[AnnotationModel]) -> Dict[str, Any]:
        yolo_export = {"images": [], "annotations": [], "categories": []}
        category_map: Dict[str, int] = {}
        annotation_id = 1

        for annotation in annotations:
            image_record = {
                "id": annotation.asset_id,
                "file_name": annotation.asset_url.split("/")[-1],
                "width": 0,
                "height": 0,
            }
            yolo_export["images"].append(image_record)
            for obj in annotation.objects:
                label = obj.label_name
                if label not in category_map:
                    category_map[label] = len(category_map) + 1
                    yolo_export["categories"].append({"id": category_map[label], "name": label})
                bbox = obj.bbox or {}
                yolo_export["annotations"].append({
                    "id": annotation_id,
                    "image_id": annotation.asset_id,
                    "category_id": category_map[label],
                    "bbox": [bbox.get("x", 0), bbox.get("y", 0), bbox.get("width", 0), bbox.get("height", 0)],
                    "score": obj.confidence or 0.0,
                    "iscrowd": 0,
                })
                annotation_id += 1
        return yolo_export

    def _build_coco_export(self, annotations: List[AnnotationModel]) -> Dict[str, Any]:
        coco_export = {
            "info": {"description": "Annotation export", "version": "1.0"},
            "images": [],
            "annotations": [],
            "categories": [],
        }
        category_map: Dict[str, int] = {}
        ann_id = 1

        for annotation in annotations:
            coco_export["images"].append({
                "id": annotation.asset_id,
                "file_name": annotation.asset_url.split("/")[-1],
                "width": 0,
                "height": 0,
            })
            for obj in annotation.objects:
                label = obj.label_name
                if label not in category_map:
                    category_map[label] = len(category_map) + 1
                    coco_export["categories"].append({"id": category_map[label], "name": label, "supercategory": obj.category or "none"})
                bbox = obj.bbox or {}
                coco_export["annotations"].append({
                    "id": ann_id,
                    "image_id": annotation.asset_id,
                    "category_id": category_map[label],
                    "bbox": [bbox.get("x", 0), bbox.get("y", 0), bbox.get("width", 0), bbox.get("height", 0)],
                    "area": bbox.get("width", 0) * bbox.get("height", 0),
                    "iscrowd": 0,
                })
                ann_id += 1
        return coco_export

    def export_annotations(self, dataset_id: int, export_format: str, version_tag: Optional[str] = None) -> str:
        annotations = self.db.query(AnnotationModel).filter(AnnotationModel.dataset_id == dataset_id, AnnotationModel.is_deleted == False).all()
        export_dir = os.path.join(settings.LOCAL_STORAGE_DIR, "annotation_exports")
        os.makedirs(export_dir, exist_ok=True)
        filename = f"annotation_export_{dataset_id}_{export_format}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
        path = os.path.join(export_dir, filename)

        if export_format == "yolo":
            payload = self._build_yolo_export(annotations)
        elif export_format == "coco":
            payload = self._build_coco_export(annotations)
        else:
            payload = {"annotations": [
                {
                    "id": annotation.id,
                    "asset_type": annotation.asset_type,
                    "asset_id": annotation.asset_id,
                    "asset_url": annotation.asset_url,
                    "annotation_type": annotation.annotation_type,
                    "status": annotation.status,
                    "metadata": annotation.annotation_metadata or {},
                }
                for annotation in annotations
            ]}

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return path
