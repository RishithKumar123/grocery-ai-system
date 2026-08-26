from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.data.repositories.sqlalchemy_model_registry_repository import SQLAlchemyModelRegistryRepository
from app.data.repositories.storage_repository import StorageRepository


class ModelRegistryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SQLAlchemyModelRegistryRepository(db)
        self.storage = StorageRepository()

    def register_model(self, payload: Dict[str, Any], user_id: int):
        return self.repo.create_model(payload, user_id)

    def upload_model_artifact(self, version_id: int, file_bytes: bytes, filename: str, artifact_type: str, metadata: Optional[Dict[str, Any]], is_primary: bool = False):
        checksum = self.repo.compute_checksum(file_bytes)
        file_url = self.storage.upload_file(file_bytes, filename, "application/octet-stream")
        size_bytes = len(file_bytes)
        artifact = self.repo.add_artifact({
            "version_id": version_id,
            "artifact_type": artifact_type,
            "file_url": file_url,
            "checksum": checksum,
            "metadata": metadata or {},
            "size_bytes": size_bytes,
            "is_primary": is_primary,
        })
        logger.info(f"Uploaded artifact for version_id={version_id}, type={artifact_type}, url={file_url}")
        return artifact

    def create_version(self, model_id: int, payload: Dict[str, Any], user_id: int):
        return self.repo.create_version(model_id, payload, user_id)

    def add_metric(self, payload: Dict[str, Any]):
        return self.repo.add_metric(payload)

    def approve_version(self, version_id: int, reviewer_id: int, comment: Optional[str] = None):
        return self.repo.approve_version(version_id, reviewer_id, comment)

    def reject_version(self, version_id: int, reviewer_id: int, comment: Optional[str] = None):
        return self.repo.reject_version(version_id, reviewer_id, comment)

    def deploy_version(self, model_id: int, payload: Dict[str, Any], deployed_by_id: int):
        payload["model_id"] = model_id
        payload["deployed_by_id"] = deployed_by_id
        deployment = self.repo.deploy_version(payload)
        version = self.repo.get_version(payload["version_id"])
        if version:
            version.status = "production" if payload["environment"] == "production" else "staging"
            self.db.commit()
            if deployment.environment == "production":
                model = self.repo.get_model(model_id)
                if model:
                    model.current_version_id = deployment.version_id
                    model.status = "production"
                    self.db.commit()
        return deployment

    def rollback_deployment(self, deployment_id: int, user_id: int, rollback_to_version_id: int, notes: Optional[str] = None):
        return self.repo.rollback_deployment(deployment_id, user_id, rollback_to_version_id, notes)

    def list_models(self, filters: Dict[str, Any], offset: int = 0, limit: int = 50):
        return self.repo.list_models(filters, offset, limit)

    def list_versions(self, model_id: int):
        return self.repo.list_versions(model_id)

    def get_model(self, model_id: int):
        return self.repo.get_model(model_id)

    def get_version(self, version_id: int):
        return self.repo.get_version(version_id)

    def get_dashboard_summary(self):
        return self.repo.get_model_dashboard_summary()

    def soft_delete_model(self, model_id: int):
        return self.repo.soft_delete_model(model_id)

    def restore_model(self, model_id: int):
        return self.repo.restore_model(model_id)
