from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ShelfModel(Base):
    __tablename__ = "shelves"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    aisle: Mapped[str] = mapped_column(String(100), index=True, nullable=False) # e.g. "Aisle 3"
    shelf_level: Mapped[str] = mapped_column(String(50), nullable=False)        # e.g. "Level 2"
    section: Mapped[str] = mapped_column(String(100), nullable=False)          # e.g. "Section B"
    bin_rack: Mapped[str] = mapped_column(String(100), nullable=False)         # e.g. "Rack 1"
    capacity: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    store: Mapped["StoreModel"] = relationship("StoreModel", back_populates="shelves")
    inventory_items: Mapped[list["InventoryModel"]] = relationship("InventoryModel", back_populates="shelf")
