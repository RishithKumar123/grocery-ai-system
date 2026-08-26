from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.inventory import InventoryItem


class InventoryRepositoryInterface(ABC):
    @abstractmethod
    def get_by_id(self, item_id: int) -> Optional[InventoryItem]:
        pass

    @abstractmethod
    def get_by_sku(self, sku: str) -> Optional[InventoryItem]:
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[InventoryItem]:
        pass

    @abstractmethod
    def create(self, item: InventoryItem) -> InventoryItem:
        pass

    @abstractmethod
    def update(self, item: InventoryItem) -> InventoryItem:
        pass

    @abstractmethod
    def delete(self, item_id: int) -> bool:
        pass
