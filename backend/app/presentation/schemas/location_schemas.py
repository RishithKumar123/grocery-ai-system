from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class MapShelfPayload(BaseModel):
    rack_location_id: int
    shelf_level: str
    height_meters: float = Field(0.4, ge=0.1)
    width_meters: float = Field(1.5, ge=0.2)
    max_capacity: int = Field(30, ge=1)


class LocateProductPayload(BaseModel):
    shelf_map_id: int
    product_id: int
    x_relative: float = Field(..., ge=0.0)
    y_relative: float = Field(..., ge=0.0)
    facing_count: int = Field(1, ge=1)
    slot_number: int = Field(1, ge=1)


class ProductLocationOut(BaseModel):
    id: int
    shelf_map_id: int
    product_id: int
    product_name: str
    sku: str
    x_relative: float
    y_relative: float
    facing_count: int
    slot_number: int
    is_misplaced: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ShelfMapOut(BaseModel):
    id: int
    rack_location_id: int
    shelf_level: str
    height_meters: float
    width_meters: float
    max_capacity: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RackLocationOut(BaseModel):
    id: int
    aisle_map_id: int
    rack_number: str
    x_coordinate: float
    y_coordinate: float
    created_at: datetime
    shelves: List[ShelfMapOut] = []

    model_config = {"from_attributes": True}


class AisleMapOut(BaseModel):
    id: int
    store_map_id: int
    aisle_name: str
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    created_at: datetime
    racks: List[RackLocationOut] = []

    model_config = {"from_attributes": True}


class StoreMapOut(BaseModel):
    id: int
    store_id: int
    map_name: str
    layout_image_url: Optional[str]
    width_meters: float
    height_meters: float
    created_at: datetime
    aisles: List[AisleMapOut] = []

    model_config = {"from_attributes": True}


class PlanogramOut(BaseModel):
    id: int
    shelf_map_id: int
    product_id: int
    product_name: str
    expected_position: int
    expected_facing_count: int

    model_config = {"from_attributes": True}


class MisplacedProductOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    sku: str
    detected_shelf_map_id: int
    detected_shelf_name: str
    expected_shelf_map_id: Optional[int]
    expected_shelf_name: Optional[str]
    detected_position: str
    expected_position: str
    severity: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EmptyShelfOut(BaseModel):
    id: int
    shelf_map_id: int
    empty_start_x: float
    empty_end_x: float
    estimated_vacant_slots: int
    created_at: datetime

    model_config = {"from_attributes": True}


class OccupancyStatsOut(BaseModel):
    id: int
    shelf_map_id: int
    shelf_name: str
    occupancy_percentage: float
    unassigned_space_percentage: float
    created_at: datetime

    model_config = {"from_attributes": True}
