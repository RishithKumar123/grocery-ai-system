from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from app.data.models.dataset_model import (
    DatasetModel,
    DatasetTagModel,
    DatasetVersionModel,
    DatasetStatisticsModel,
    DatasetImageModel,
    DatasetVideoModel,
    DatasetMetadataModel,
)


class SQLAlchemyDatasetRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_dataset(self, payload: Dict[str, Any], creator_id: int) -> DatasetModel:
        dataset = DatasetModel(
            name=payload["name"],
            description=payload.get("description"),
            dataset_type=payload.get("dataset_type", "training"),
            status=payload.get("status", "active"),
            visibility=payload.get("visibility", "private"),
            owner_id=payload.get("owner_id", creator_id),
            created_by_id=creator_id,
            current_version=payload.get("version"),
        )
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)

        tags = payload.get("tags") or []
        for tag in tags:
            self.db.add(DatasetTagModel(dataset_id=dataset.id, name=tag.strip()))
        self.db.commit()
        self.db.refresh(dataset)
        return dataset

    def get_dataset(self, dataset_id: int, include_deleted: bool = False) -> Optional[DatasetModel]:
        query = self.db.query(DatasetModel).filter(DatasetModel.id == dataset_id)
        if not include_deleted:
            query = query.filter(DatasetModel.is_deleted == False)
        return query.first()

    def list_datasets(self, filters: Dict[str, Any], offset: int = 0, limit: int = 50) -> List[DatasetModel]:
        query = self.db.query(DatasetModel).filter(DatasetModel.is_deleted == False)

        if filters.get("dataset_type"):
            query = query.filter(DatasetModel.dataset_type == filters["dataset_type"])
        if filters.get("status"):
            query = query.filter(DatasetModel.status == filters["status"])
        if filters.get("owner_id"):
            query = query.filter(DatasetModel.owner_id == filters["owner_id"])
        if filters.get("visibility"):
            query = query.filter(DatasetModel.visibility == filters["visibility"])
        if filters.get("tag"):
            query = query.join(DatasetTagModel).filter(DatasetTagModel.name == filters["tag"])

        return query.order_by(DatasetModel.updated_at.desc()).offset(offset).limit(limit).all()

    def search_datasets(self, filters: Dict[str, Any], offset: int = 0, limit: int = 50) -> List[DatasetModel]:
        query = self.db.query(DatasetModel).filter(DatasetModel.is_deleted == False)
        search_text = filters.get("query")
        if search_text:
            search_pattern = f"%{search_text}%"
            query = query.filter(
                or_(
                    DatasetModel.name.ilike(search_pattern),
                    DatasetModel.description.ilike(search_pattern),
                )
            )
        if filters.get("dataset_type"):
            query = query.filter(DatasetModel.dataset_type == filters["dataset_type"])
        if filters.get("status"):
            query = query.filter(DatasetModel.status == filters["status"])
        return query.order_by(DatasetModel.updated_at.desc()).offset(offset).limit(limit).all()

    def update_dataset(self, dataset_id: int, payload: Dict[str, Any]) -> Optional[DatasetModel]:
        dataset = self.db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
        if not dataset:
            return None

        for field in ["name", "description", "dataset_type", "status", "visibility", "current_version"]:
            if field in payload:
                setattr(dataset, field, payload[field])

        if payload.get("owner_id") is not None:
            dataset.owner_id = payload["owner_id"]

        if payload.get("tags") is not None:
            self.db.query(DatasetTagModel).filter(DatasetTagModel.dataset_id == dataset_id).delete()
            for tag in payload["tags"]:
                self.db.add(DatasetTagModel(dataset_id=dataset.id, name=tag.strip()))

        self.db.commit()
        self.db.refresh(dataset)
        return dataset

    def soft_delete_dataset(self, dataset_id: int) -> bool:
        dataset = self.db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
        if not dataset or dataset.is_deleted:
            return False
        dataset.is_deleted = True
        dataset.deleted_at = datetime.utcnow()
        self.db.commit()
        return True

    def restore_dataset(self, dataset_id: int) -> Optional[DatasetModel]:
        dataset = self.db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
        if not dataset or not dataset.is_deleted:
            return None
        dataset.is_deleted = False
        dataset.deleted_at = None
        self.db.commit()
        self.db.refresh(dataset)
        return dataset

    def archive_dataset(self, dataset_id: int) -> Optional[DatasetModel]:
        dataset = self.db.query(DatasetModel).filter(DatasetModel.id == dataset_id, DatasetModel.is_deleted == False).first()
        if not dataset:
            return None
        dataset.status = "archived"
        dataset.is_archived = True
        dataset.archived_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(dataset)
        return dataset

    def _recalculate_statistics(self, dataset_id: int) -> DatasetStatisticsModel:
        total_images = self.db.query(func.count(DatasetImageModel.id)).filter(DatasetImageModel.dataset_id == dataset_id).scalar() or 0
        total_videos = self.db.query(func.count(DatasetVideoModel.id)).filter(DatasetVideoModel.dataset_id == dataset_id).scalar() or 0
        total_annotations = self.db.query(func.sum(DatasetImageModel.annotation_count)).filter(DatasetImageModel.dataset_id == dataset_id).scalar() or 0
        total_size = self.db.query(func.sum(DatasetImageModel.file_size)).filter(DatasetImageModel.dataset_id == dataset_id).scalar() or 0
        total_size += self.db.query(func.sum(DatasetVideoModel.file_size)).filter(DatasetVideoModel.dataset_id == dataset_id).scalar() or 0

        stats = self.db.query(DatasetStatisticsModel).filter(DatasetStatisticsModel.dataset_id == dataset_id).first()
        if not stats:
            stats = DatasetStatisticsModel(
                dataset_id=dataset_id,
                total_images=total_images,
                total_videos=total_videos,
                total_annotations=total_annotations,
                total_size_bytes=total_size,
            )
            self.db.add(stats)
        else:
            stats.total_images = total_images
            stats.total_videos = total_videos
            stats.total_annotations = total_annotations
            stats.total_size_bytes = total_size
        self.db.commit()
        self.db.refresh(stats)
        return stats

    def create_dataset_asset(self, dataset_id: int, asset_payload: Dict[str, Any]) -> Any:
        if asset_payload.get("asset_type") == "video":
            asset = DatasetVideoModel(
                dataset_id=dataset_id,
                product_id=asset_payload.get("product_id"),
                brand_id=asset_payload.get("brand_id"),
                category_id=asset_payload.get("category_id"),
                supplier_id=asset_payload.get("supplier_id"),
                store_id=asset_payload.get("store_id"),
                shelf_id=asset_payload.get("shelf_id"),
                location=asset_payload.get("location"),
                original_filename=asset_payload["original_filename"],
                file_url=asset_payload["file_url"],
                thumbnail_url=asset_payload.get("thumbnail_url"),
                duration_seconds=asset_payload.get("duration_seconds"),
                resolution=asset_payload.get("resolution"),
                fps=asset_payload.get("fps"),
                frame_count=asset_payload.get("frame_count"),
                file_size=asset_payload["file_size"],
            )
        else:
            asset = DatasetImageModel(
                dataset_id=dataset_id,
                product_id=asset_payload.get("product_id"),
                brand_id=asset_payload.get("brand_id"),
                category_id=asset_payload.get("category_id"),
                supplier_id=asset_payload.get("supplier_id"),
                store_id=asset_payload.get("store_id"),
                shelf_id=asset_payload.get("shelf_id"),
                location=asset_payload.get("location"),
                original_filename=asset_payload["original_filename"],
                file_url=asset_payload["file_url"],
                width=asset_payload["width"],
                height=asset_payload["height"],
                aspect_ratio=asset_payload["aspect_ratio"],
                file_size=asset_payload["file_size"],
                capture_date=asset_payload.get("capture_date"),
                gps_coordinates=asset_payload.get("gps_coordinates"),
                camera_info=asset_payload.get("camera_info"),
                color_space=asset_payload.get("color_space"),
                hash=asset_payload["hash"],
                annotation_count=asset_payload.get("annotation_count", 0),
            )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        self._recalculate_statistics(dataset_id)

        for key, value in (asset_payload.get("metadata") or {}).items():
            self.db.add(DatasetMetadataModel(
                dataset_id=dataset_id,
                asset_type=asset_payload.get("asset_type", "image"),
                asset_id=asset.id,
                key=key,
                value=str(value) if value is not None else None,
            ))
        self.db.commit()
        return asset

    def find_image_by_hash(self, dataset_id: int, hash_value: str) -> Optional[DatasetImageModel]:
        return self.db.query(DatasetImageModel).filter(
            DatasetImageModel.dataset_id == dataset_id,
            DatasetImageModel.hash == hash_value,
        ).first()

    def find_video_by_hash(self, dataset_id: int, hash_value: str) -> Optional[DatasetVideoModel]:
        return self.db.query(DatasetVideoModel).filter(
            DatasetVideoModel.dataset_id == dataset_id,
            DatasetVideoModel.file_url == hash_value,
        ).first()

    def create_dataset_version(self, dataset_id: int, payload: Dict[str, Any]) -> DatasetVersionModel:
        version = DatasetVersionModel(
            dataset_id=dataset_id,
            version_tag=payload["version_tag"],
            archive_url=payload["archive_url"],
            file_count=payload["file_count"],
            size_bytes=payload["size_bytes"],
            created_by_id=payload["created_by_id"],
        )
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)

        dataset = self.db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
        if dataset:
            dataset.current_version = payload["version_tag"]
            self.db.commit()
            self.db.refresh(dataset)

        return version

    def get_dataset_versions(self, dataset_id: int) -> List[DatasetVersionModel]:
        return self.db.query(DatasetVersionModel).filter(DatasetVersionModel.dataset_id == dataset_id).order_by(DatasetVersionModel.created_at.desc()).all()

    def get_dataset_statistics(self, dataset_id: int) -> Dict[str, Any]:
        stats = self._recalculate_statistics(dataset_id)
        return {
            "dataset_id": dataset_id,
            "total_images": stats.total_images,
            "total_videos": stats.total_videos,
            "total_annotations": stats.total_annotations,
            "total_size_bytes": stats.total_size_bytes,
            "last_updated": stats.last_updated,
        }

    def get_dashboard_summary(self) -> Dict[str, Any]:
        total_datasets = self.db.query(func.count(DatasetModel.id)).filter(DatasetModel.is_deleted == False).scalar() or 0
        total_images = self.db.query(func.count(DatasetImageModel.id)).scalar() or 0
        total_videos = self.db.query(func.count(DatasetVideoModel.id)).scalar() or 0
        total_versions = self.db.query(func.count(DatasetVersionModel.id)).scalar() or 0
        total_size = self.db.query(func.sum(DatasetStatisticsModel.total_size_bytes)).scalar() or 0

        return {
            "total_datasets": total_datasets,
            "total_images": total_images,
            "total_videos": total_videos,
            "total_versions": total_versions,
            "total_storage_bytes": total_size,
            "dataset_version_count": total_versions,
        }

    def get_dataset_assets(self, dataset_id: int) -> Dict[str, List[Any]]:
        images = self.db.query(DatasetImageModel).filter(DatasetImageModel.dataset_id == dataset_id).all()
        videos = self.db.query(DatasetVideoModel).filter(DatasetVideoModel.dataset_id == dataset_id).all()
        return {"images": images, "videos": videos}

    def clone_dataset(self, dataset_id: int, creator_id: int) -> Optional[DatasetModel]:
        dataset = self.get_dataset(dataset_id, include_deleted=True)
        if not dataset:
            return None
        clone = DatasetModel(
            name=f"{dataset.name} (Clone)",
            description=dataset.description,
            dataset_type=dataset.dataset_type,
            status="active",
            visibility=dataset.visibility,
            owner_id=dataset.owner_id,
            created_by_id=creator_id,
            current_version=dataset.current_version,
        )
        self.db.add(clone)
        self.db.commit()
        self.db.refresh(clone)

        for tag in dataset.tags:
            self.db.add(DatasetTagModel(dataset_id=clone.id, name=tag.name))

        for image in dataset.images:
            self.db.add(DatasetImageModel(
                dataset_id=clone.id,
                product_id=image.product_id,
                brand_id=image.brand_id,
                category_id=image.category_id,
                supplier_id=image.supplier_id,
                store_id=image.store_id,
                shelf_id=image.shelf_id,
                location=image.location,
                original_filename=image.original_filename,
                file_url=image.file_url,
                width=image.width,
                height=image.height,
                aspect_ratio=image.aspect_ratio,
                file_size=image.file_size,
                capture_date=image.capture_date,
                gps_coordinates=image.gps_coordinates,
                camera_info=image.camera_info,
                color_space=image.color_space,
                hash=image.hash,
                annotation_count=image.annotation_count,
            ))

        for video in dataset.videos:
            self.db.add(DatasetVideoModel(
                dataset_id=clone.id,
                product_id=video.product_id,
                brand_id=video.brand_id,
                category_id=video.category_id,
                supplier_id=video.supplier_id,
                store_id=video.store_id,
                shelf_id=video.shelf_id,
                location=video.location,
                original_filename=video.original_filename,
                file_url=video.file_url,
                thumbnail_url=video.thumbnail_url,
                duration_seconds=video.duration_seconds,
                resolution=video.resolution,
                fps=video.fps,
                frame_count=video.frame_count,
                file_size=video.file_size,
            ))

        self.db.commit()
        self._recalculate_statistics(clone.id)
        self.db.refresh(clone)
        return clone
