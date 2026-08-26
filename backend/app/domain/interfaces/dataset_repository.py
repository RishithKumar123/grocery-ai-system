from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class DatasetRepositoryInterface(ABC):
    @abstractmethod
    def create_dataset(self, payload: Dict[str, Any], creator_id: int) -> Any:
        pass

    @abstractmethod
    def get_dataset(self, dataset_id: int, include_deleted: bool = False) -> Any:
        pass

    @abstractmethod
    def list_datasets(self, filters: Dict[str, Any], offset: int = 0, limit: int = 50) -> List[Any]:
        pass

    @abstractmethod
    def search_datasets(self, filters: Dict[str, Any], offset: int = 0, limit: int = 50) -> List[Any]:
        pass

    @abstractmethod
    def update_dataset(self, dataset_id: int, payload: Dict[str, Any]) -> Any:
        pass

    @abstractmethod
    def soft_delete_dataset(self, dataset_id: int) -> bool:
        pass

    @abstractmethod
    def restore_dataset(self, dataset_id: int) -> Any:
        pass

    @abstractmethod
    def archive_dataset(self, dataset_id: int) -> Any:
        pass

    @abstractmethod
    def create_dataset_asset(self, dataset_id: int, asset_payload: Dict[str, Any]) -> Any:
        pass

    @abstractmethod
    def get_dataset_statistics(self, dataset_id: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_dashboard_summary(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_dataset_version(self, dataset_id: int, payload: Dict[str, Any]) -> Any:
        pass

    @abstractmethod
    def get_dataset_versions(self, dataset_id: int) -> List[Any]:
        pass

    @abstractmethod
    def clone_dataset(self, dataset_id: int, creator_id: int) -> Any:
        pass

    @abstractmethod
    def get_dataset_assets(self, dataset_id: int) -> List[Any]:
        pass
