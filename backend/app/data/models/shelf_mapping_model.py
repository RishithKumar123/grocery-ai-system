from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, DateTime, ForeignKey, Float, Integer, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class StoreMapModel(Base):
    __tablename__ = "store_maps"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    map_name: Mapped[str] = mapped_column(String(255), nullable=False)
    layout_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    width_meters: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    height_meters: Mapped[float] = mapped_column(Float, default=40.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    store: Mapped["StoreModel"] = relationship("StoreModel")
    aisles: Mapped[List["AisleMapModel"]] = relationship("AisleMapModel", back_populates="store_map", cascade="all, delete-orphan")


class AisleMapModel(Base):
    __tablename__ = "aisle_maps"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_map_id: Mapped[int] = mapped_column(ForeignKey("store_maps.id", ondelete="CASCADE"), nullable=False, index=True)
    aisle_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    start_x: Mapped[float] = mapped_column(Float, nullable=False)
    start_y: Mapped[float] = mapped_column(Float, nullable=False)
    end_x: Mapped[float] = mapped_column(Float, nullable=False)
    end_y: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    store_map: Mapped["StoreMapModel"] = relationship("StoreMapModel", back_populates="aisles")
    racks: Mapped[List["RackLocationModel"]] = relationship("RackLocationModel", back_populates="aisle_map", cascade="all, delete-orphan")


class RackLocationModel(Base):
    __tablename__ = "rack_locations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    aisle_map_id: Mapped[int] = mapped_column(ForeignKey("aisle_maps.id", ondelete="CASCADE"), nullable=False, index=True)
    rack_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    x_coordinate: Mapped[float] = mapped_column(Float, nullable=False)
    y_coordinate: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    aisle_map: Mapped["AisleMapModel"] = relationship("AisleMapModel", back_populates="racks")
    shelves: Mapped[List["ShelfMapModel"]] = relationship("ShelfMapModel", back_populates="rack_location", cascade="all, delete-orphan")


class ShelfMapModel(Base):
    __tablename__ = "shelf_maps"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    rack_location_id: Mapped[int] = mapped_column(ForeignKey("rack_locations.id", ondelete="CASCADE"), nullable=False, index=True)
    shelf_level: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. "Level 1"
    height_meters: Mapped[float] = mapped_column(Float, default=0.4, nullable=False)
    width_meters: Mapped[float] = mapped_column(Float, default=1.5, nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    rack_location: Mapped["RackLocationModel"] = relationship("RackLocationModel", back_populates="shelves")
    planograms: Mapped[List["PlanogramModel"]] = relationship("PlanogramModel", back_populates="shelf_map", cascade="all, delete-orphan")
    product_placements: Mapped[List["ProductLocationModel"]] = relationship("ProductLocationModel", back_populates="shelf_map", cascade="all, delete-orphan")
    empty_spots: Mapped[List["EmptyShelfModel"]] = relationship("EmptyShelfModel", back_populates="shelf_map", cascade="all, delete-orphan")
    stats: Mapped[List["OccupancyStatisticsModel"]] = relationship("OccupancyStatisticsModel", back_populates="shelf_map", cascade="all, delete-orphan")


class PlanogramModel(Base):
    __tablename__ = "planograms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    shelf_map_id: Mapped[int] = mapped_column(ForeignKey("shelf_maps.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    expected_position: Mapped[int] = mapped_column(Integer, nullable=False) # 1-indexed slot
    expected_facing_count: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    shelf_map: Mapped["ShelfMapModel"] = relationship("ShelfMapModel", back_populates="planograms")
    product: Mapped["ProductModel"] = relationship("ProductModel")


class ProductLocationModel(Base):
    __tablename__ = "product_locations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    shelf_map_id: Mapped[int] = mapped_column(ForeignKey("shelf_maps.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    x_relative: Mapped[float] = mapped_column(Float, nullable=False) # Meters from left
    y_relative: Mapped[float] = mapped_column(Float, nullable=False) # Meters from bottom
    facing_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    slot_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_misplaced: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    shelf_map: Mapped["ShelfMapModel"] = relationship("ShelfMapModel", back_populates="product_placements")
    product: Mapped["ProductModel"] = relationship("ProductModel")


class LocationHistoryModel(Base):
    __tablename__ = "location_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_shelf_map_id: Mapped[Optional[int]] = mapped_column(ForeignKey("shelf_maps.id", ondelete="SET NULL"), nullable=True)
    new_shelf_map_id: Mapped[int] = mapped_column(ForeignKey("shelf_maps.id", ondelete="CASCADE"), nullable=False)
    moved_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    product: Mapped["ProductModel"] = relationship("ProductModel")
    new_shelf_map: Mapped["ShelfMapModel"] = relationship("ShelfMapModel", foreign_keys=[new_shelf_map_id])


class MisplacedProductModel(Base):
    __tablename__ = "misplaced_products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    detected_shelf_map_id: Mapped[int] = mapped_column(ForeignKey("shelf_maps.id", ondelete="CASCADE"), nullable=False, index=True)
    expected_shelf_map_id: Mapped[Optional[int]] = mapped_column(ForeignKey("shelf_maps.id", ondelete="CASCADE"), nullable=True)
    detected_position: Mapped[str] = mapped_column(String(100), nullable=False) # e.g. "Slot 4"
    expected_position: Mapped[str] = mapped_column(String(100), nullable=False) # e.g. "Slot 2"
    severity: Mapped[str] = mapped_column(String(50), default="Low", nullable=False) # Low, Medium, High
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    product: Mapped["ProductModel"] = relationship("ProductModel")
    detected_shelf: Mapped["ShelfMapModel"] = relationship("ShelfMapModel", foreign_keys=[detected_shelf_map_id])
    expected_shelf: Mapped[Optional["ShelfMapModel"]] = relationship("ShelfMapModel", foreign_keys=[expected_shelf_map_id])


class EmptyShelfModel(Base):
    __tablename__ = "empty_shelves"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    shelf_map_id: Mapped[int] = mapped_column(ForeignKey("shelf_maps.id", ondelete="CASCADE"), nullable=False, index=True)
    empty_start_x: Mapped[float] = mapped_column(Float, nullable=False)
    empty_end_x: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_vacant_slots: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    shelf_map: Mapped["ShelfMapModel"] = relationship("ShelfMapModel", back_populates="empty_spots")


class OccupancyStatisticsModel(Base):
    __tablename__ = "occupancy_statistics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    shelf_map_id: Mapped[int] = mapped_column(ForeignKey("shelf_maps.id", ondelete="CASCADE"), nullable=False, index=True)
    occupancy_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unassigned_space_percentage: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    shelf_map: Mapped["ShelfMapModel"] = relationship("ShelfMapModel", back_populates="stats")
