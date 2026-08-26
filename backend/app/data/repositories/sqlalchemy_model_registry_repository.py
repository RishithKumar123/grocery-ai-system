import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.data.models.model_registry_model import (
    AIModelModel,
    AIModelVersionModel,
    ModelArtifactModel,
    ModelMetricModel,
    ModelDeploymentModel,
    DeploymentHistoryModel,
    ModelReviewModel,
    ModelTagModel,
    ModelPermissionModel,
)


class SQLAlchemyModelRegistryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_model(self, payload: Dict[str, Any], creator_id: int) -> AIModelModel:
        model = AIModelModel(
            name=payload["name"],
            description=payload.get("description"),
            model_type=payload["model_type"],
            owner_id=payload.get("owner_id"),
            created_by_id=creator_id,
            status=payload.get("status", "draft"),
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        self._save_tags(model.id, None, payload.get("tags", []))
        return model

    def get_model(self, model_id: int) -> Optional[AIModelModel]:
        return self.db.query(AIModelModel).filter(AIModelModel.id == model_id, AIModelModel.is_deleted == False).first()

    def list_models(self, filters: Dict[str, Any], offset: int = 0, limit: int = 50) -> List[AIModelModel]:
        query = self.db.query(AIModelModel).filter(AIModelModel.is_deleted == False)
        if filters.get("model_type"):
            query = query.filter(AIModelModel.model_type == filters["model_type"])
        if filters.get("status"):
            query = query.filter(AIModelModel.status == filters["status"])
        if filters.get("name"):
            query = query.filter(AIModelModel.name.ilike(f"%{filters['name']}%"))
        if filters.get("owner_id"):
            query = query.filter(AIModelModel.owner_id == filters["owner_id"])
        return query.order_by(AIModelModel.updated_at.desc()).offset(offset).limit(limit).all()

    def update_model(self, model_id: int, payload: Dict[str, Any]) -> Optional[AIModelModel]:
        model = self.get_model(model_id)
        if not model:
            return None
        for field in ["name", "description", "model_type", "owner_id", "status"]:
            if field in payload:
                setattr(model, field, payload[field])
        self.db.commit()
        self.db.refresh(model)
        if payload.get("tags") is not None:
            self._save_tags(model.id, None, payload.get("tags", []))
        return model

    def soft_delete_model(self, model_id: int) -> bool:
        model = self.get_model(model_id)
        if not model or model.is_deleted:
            return False
        model.is_deleted = True
        self.db.commit()
        return True

    def restore_model(self, model_id: int) -> Optional[AIModelModel]:
        model = self.db.query(AIModelModel).filter(AIModelModel.id == model_id, AIModelModel.is_deleted == True).first()
        if not model:
            return None
        model.is_deleted = False
        self.db.commit()
        self.db.refresh(model)
        return model

    def create_version(self, model_id: int, payload: Dict[str, Any], author_id: int) -> AIModelVersionModel:
        version = AIModelVersionModel(
            model_id=model_id,
            version_number=payload["version_number"],
            parent_version_id=payload.get("parent_version_id"),
            dataset_version_id=payload.get("dataset_version_id"),
            training_job_id=payload.get("training_job_id"),
            training_config=payload.get("training_config") or {},
            framework_version=payload.get("framework_version"),
            hyperparameters=payload.get("hyperparameters") or {},
            metrics_summary=payload.get("metrics_summary") or {},
            status=payload.get("status", "draft"),
            author_id=author_id,
            description=payload.get("description"),
            git_commit=payload.get("git_commit"),
        )
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        self._save_tags(model_id, version.id, payload.get("tags", []))
        return version

    def get_version(self, version_id: int) -> Optional[AIModelVersionModel]:
        return self.db.query(AIModelVersionModel).filter(AIModelVersionModel.id == version_id).first()

    def list_versions(self, model_id: int) -> List[AIModelVersionModel]:
        return self.db.query(AIModelVersionModel).filter(AIModelVersionModel.model_id == model_id).order_by(AIModelVersionModel.created_at.desc()).all()

    def add_artifact(self, payload: Dict[str, Any]) -> ModelArtifactModel:
        artifact = ModelArtifactModel(
            version_id=payload["version_id"],
            artifact_type=payload["artifact_type"],
            file_url=payload["file_url"],
            checksum=payload.get("checksum"),
            artifact_metadata=payload.get("metadata") or {},
            size_bytes=payload.get("size_bytes", 0),
            is_primary=payload.get("is_primary", False),
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def add_metric(self, payload: Dict[str, Any]) -> ModelMetricModel:
        metric = ModelMetricModel(
            version_id=payload["version_id"],
            metric_name=payload["metric_name"],
            value=payload["value"],
            details=payload.get("details") or {},
        )
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def approve_version(self, version_id: int, reviewer_id: int, comment: Optional[str] = None) -> Optional[ModelReviewModel]:
        version = self.get_version(version_id)
        if not version:
            return None
        version.status = "approved"
        self.db.commit()
        review = ModelReviewModel(
            version_id=version_id,
            reviewer_id=reviewer_id,
            status="approved",
            comment=comment,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def reject_version(self, version_id: int, reviewer_id: int, comment: Optional[str] = None) -> Optional[ModelReviewModel]:
        version = self.get_version(version_id)
        if not version:
            return None
        version.status = "rejected"
        self.db.commit()
        review = ModelReviewModel(
            version_id=version_id,
            reviewer_id=reviewer_id,
            status="rejected",
            comment=comment,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def deploy_version(self, payload: Dict[str, Any]) -> ModelDeploymentModel:
        deployment = ModelDeploymentModel(
            model_id=payload["model_id"],
            version_id=payload["version_id"],
            environment=payload["environment"],
            status=payload.get("status", "active"),
            deployed_by_id=payload.get("deployed_by_id"),
            endpoint_url=payload.get("endpoint_url"),
            notes=payload.get("notes"),
            rollback_of_id=payload.get("rollback_of_id"),
            is_active=True,
        )
        self.db.add(deployment)
        self.db.commit()
        self.db.refresh(deployment)
        self.add_deployment_history({
            "deployment_id": deployment.id,
            "action": "deploy",
            "performed_by_id": payload.get("deployed_by_id"),
            "from_version_id": payload.get("from_version_id"),
            "to_version_id": payload["version_id"],
            "environment": payload["environment"],
            "notes": payload.get("notes"),
            "status": deployment.status,
        })
        return deployment

    def rollback_deployment(self, deployment_id: int, performed_by_id: int, rollback_to_version_id: int, notes: Optional[str] = None) -> Optional[ModelDeploymentModel]:
        deployment = self.db.query(ModelDeploymentModel).filter(ModelDeploymentModel.id == deployment_id).first()
        if not deployment:
            return None
        deployment.is_active = False
        deployment.status = "rolled_back"
        self.db.commit()
        rollback_deployment = ModelDeploymentModel(
            model_id=deployment.model_id,
            version_id=rollback_to_version_id,
            environment=deployment.environment,
            status="active",
            deployed_by_id=performed_by_id,
            endpoint_url=deployment.endpoint_url,
            notes=notes,
            rollback_of_id=deployment.id,
            is_active=True,
        )
        self.db.add(rollback_deployment)
        self.db.commit()
        self.db.refresh(rollback_deployment)
        self.add_deployment_history({
            "deployment_id": rollback_deployment.id,
            "action": "rollback",
            "performed_by_id": performed_by_id,
            "from_version_id": deployment.version_id,
            "to_version_id": rollback_to_version_id,
            "environment": deployment.environment,
            "notes": notes,
            "status": rollback_deployment.status,
        })
        return rollback_deployment

    def add_deployment_history(self, payload: Dict[str, Any]) -> DeploymentHistoryModel:
        history = DeploymentHistoryModel(
            deployment_id=payload["deployment_id"],
            action=payload["action"],
            performed_by_id=payload.get("performed_by_id"),
            from_version_id=payload.get("from_version_id"),
            to_version_id=payload.get("to_version_id"),
            environment=payload["environment"],
            notes=payload.get("notes"),
            status=payload.get("status", "completed"),
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def get_deployment_history(self, model_id: Optional[int] = None) -> List[DeploymentHistoryModel]:
        query = self.db.query(DeploymentHistoryModel)
        if model_id is not None:
            query = query.join(ModelDeploymentModel).filter(ModelDeploymentModel.model_id == model_id)
        return query.order_by(DeploymentHistoryModel.created_at.desc()).all()

    def get_model_dashboard_summary(self) -> Dict[str, Any]:
        total_models = self.db.query(func.count(AIModelModel.id)).scalar() or 0
        production_models = self.db.query(func.count(AIModelModel.id)).filter(AIModelModel.status == "production").scalar() or 0
        staging_models = self.db.query(func.count(AIModelModel.id)).filter(AIModelModel.status == "staging").scalar() or 0
        archived_models = self.db.query(func.count(AIModelModel.id)).filter(AIModelModel.is_archived == True).scalar() or 0
        average_map = self.db.query(func.avg(ModelMetricModel.value)).filter(ModelMetricModel.metric_name.ilike("%mAP%") ).scalar() or 0.0
        average_precision = self.db.query(func.avg(ModelMetricModel.value)).filter(ModelMetricModel.metric_name.ilike("%precision%") ).scalar() or 0.0
        return {
            "total_models": total_models,
            "production_models": production_models,
            "staging_models": staging_models,
            "archived_models": archived_models,
            "average_map": round(float(average_map), 4),
            "average_precision": round(float(average_precision), 4),
        }

    def _save_tags(self, model_id: Optional[int], version_id: Optional[int], tags: List[str]) -> None:
        if model_id is not None:
            self.db.query(ModelTagModel).filter(ModelTagModel.model_id == model_id, ModelTagModel.version_id == None).delete()
        if version_id is not None:
            self.db.query(ModelTagModel).filter(ModelTagModel.version_id == version_id).delete()
        for tag in tags or []:
            self.db.add(ModelTagModel(model_id=model_id, version_id=version_id, name=tag.strip()))
        self.db.commit()

    def compute_checksum(self, file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()
