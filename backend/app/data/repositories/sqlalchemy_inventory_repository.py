from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.entities.inventory import InventoryItem
from app.domain.interfaces.inventory_repository import InventoryRepositoryInterface
from app.data.models.inventory_model import InventoryModel


class SQLAlchemyInventoryRepository(InventoryRepositoryInterface):
    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: InventoryModel) -> InventoryItem:
        return InventoryItem(
            id=model.id,
            name=model.name,
            sku=model.sku,
            quantity=model.quantity,
            available_stock=model.available_stock,
            reserved_stock=model.reserved_stock,
            damaged_stock=model.damaged_stock,
            min_stock=model.min_stock,
            max_stock=model.max_stock,
            reorder_level=model.reorder_level,
            expiry_date=model.expiry_date,
            confidence=model.confidence,
            image_url=model.image_url,
            stock_valuation=model.stock_valuation,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def get_by_id(self, item_id: int) -> Optional[InventoryItem]:
        model = self.db.query(InventoryModel).filter(InventoryModel.id == item_id).first()
        return self._to_entity(model) if model else None

    def get_by_sku(self, sku: str) -> Optional[InventoryItem]:
        model = self.db.query(InventoryModel).filter(InventoryModel.sku == sku).first()
        return self._to_entity(model) if model else None

    def get_all(self, skip: int = 0, limit: int = 100) -> List[InventoryItem]:
        models = self.db.query(InventoryModel).offset(skip).limit(limit).all()
        return [self._to_entity(model) for model in models]

    def create(self, item: InventoryItem) -> InventoryItem:
        model = InventoryModel(
            name=item.name,
            sku=item.sku,
            quantity=item.quantity,
            available_stock=item.available_stock,
            reserved_stock=item.reserved_stock,
            damaged_stock=item.damaged_stock,
            min_stock=item.min_stock,
            max_stock=item.max_stock,
            reorder_level=item.reorder_level,
            expiry_date=item.expiry_date,
            confidence=item.confidence,
            image_url=item.image_url
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def update(self, item: InventoryItem) -> InventoryItem:
        model = self.db.query(InventoryModel).filter(InventoryModel.id == item.id).first()
        if not model:
            raise ValueError(f"Inventory item with id {item.id} not found for updates.")
        
        model.name = item.name
        model.sku = item.sku
        model.quantity = item.quantity
        model.available_stock = item.available_stock
        model.reserved_stock = item.reserved_stock
        model.damaged_stock = item.damaged_stock
        model.min_stock = item.min_stock
        model.max_stock = item.max_stock
        model.reorder_level = item.reorder_level
        model.expiry_date = item.expiry_date
        model.confidence = item.confidence
        model.image_url = item.image_url
        
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def delete(self, item_id: int) -> bool:
        model = self.db.query(InventoryModel).filter(InventoryModel.id == item_id).first()
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True
