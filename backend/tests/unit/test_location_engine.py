import pytest
from sqlalchemy.orm import Session
from app.data.models.product_model import ProductModel
from app.data.models.shelf_mapping_model import (
    StoreMapModel,
    AisleMapModel,
    RackLocationModel,
    ShelfMapModel,
    PlanogramModel,
    ProductLocationModel,
    MisplacedProductModel,
    EmptyShelfModel,
    OccupancyStatisticsModel
)
from app.services.location_service import LocationIntelligenceService


def test_location_assignment_and_planogram_compliance(db_session: Session):
    service = LocationIntelligenceService()

    # 1. Seed store layout hierarchy
    store_map = StoreMapModel(store_id=1, map_name="Test Map", width_meters=20, height_meters=20)
    db_session.add(store_map)
    db_session.commit()

    aisle = AisleMapModel(store_map_id=store_map.id, aisle_name="Test Aisle 1", start_x=1.0, start_y=1.0, end_x=1.0, end_y=10.0)
    db_session.add(aisle)
    db_session.commit()

    rack = RackLocationModel(aisle_map_id=aisle.id, rack_number="R1", x_coordinate=1.0, y_coordinate=3.0)
    db_session.add(rack)
    db_session.commit()

    shelf = ShelfMapModel(rack_location_id=rack.id, shelf_level="Level 1", width_meters=1.5, height_meters=0.4, max_capacity=20)
    db_session.add(shelf)
    db_session.commit()

    # Seed products
    prod1 = ProductModel(name="Aetheria Coffee 200g", barcode="1111111111111", sku="COF-200G", category="Beverages", price=250.0)
    prod2 = ProductModel(name="Aetheria Tea 100g", barcode="2222222222222", sku="TEA-100G", category="Beverages", price=150.0)
    db_session.add_all([prod1, prod2])
    db_session.commit()

    # Planogram: expect prod1 at slot 1, expect prod2 at slot 2 on Level 1 shelf
    plan1 = PlanogramModel(shelf_map_id=shelf.id, product_id=prod1.id, expected_position=1, expected_facing_count=2)
    plan2 = PlanogramModel(shelf_map_id=shelf.id, product_id=prod2.id, expected_position=2, expected_facing_count=2)
    db_session.add_all([plan1, plan2])
    db_session.commit()

    # 2. Test Correct Placement assignment
    placement1 = service.assign_product_location(
        db=db_session,
        shelf_map_id=shelf.id,
        product_id=prod1.id,
        x_relative=0.20,
        y_relative=0.10,
        facing_count=2,
        slot_number=1
    )

    assert placement1.is_misplaced is False
    assert db_session.query(MisplacedProductModel).count() == 0

    # 3. Test Misplaced Position assignment (wrong slot)
    placement2 = service.assign_product_location(
        db=db_session,
        shelf_map_id=shelf.id,
        product_id=prod2.id,
        x_relative=0.80,
        y_relative=0.10,
        facing_count=2,
        slot_number=5 # Expected slot 2, detected slot 5
    )

    assert placement2.is_misplaced is True
    misplaced = db_session.query(MisplacedProductModel).filter(MisplacedProductModel.product_id == prod2.id).first()
    assert misplaced is not None
    assert misplaced.severity == "Low"


def test_empty_shelf_gaps_calculation(db_session: Session):
    service = LocationIntelligenceService()

    # Seed mock layout
    rack = RackLocationModel(aisle_map_id=1, rack_number="R2", x_coordinate=5.0, y_coordinate=5.0)
    db_session.add(rack)
    db_session.commit()

    shelf = ShelfMapModel(rack_location_id=rack.id, shelf_level="Level 2", width_meters=1.5, height_meters=0.4, max_capacity=20)
    db_session.add(shelf)
    db_session.commit()

    prod = ProductModel(name="Aetheria Cola 500ml", barcode="3333333333333", sku="COLA-500ML", category="Beverages", price=50.0)
    db_session.add(prod)
    db_session.commit()

    # Place a single product at center (x = 0.70m, facing_count = 1) on 1.5m shelf
    # Gaps should occur: left gap (0.0 to 0.70), right gap (0.78 to 1.50)
    service.assign_product_location(
        db=db_session,
        shelf_map_id=shelf.id,
        product_id=prod.id,
        x_relative=0.70,
        y_relative=0.10,
        facing_count=1,
        slot_number=1
    )

    empty_spots = db_session.query(EmptyShelfModel).filter(EmptyShelfModel.shelf_map_id == shelf.id).all()
    # Left gap (0.0 to 0.70m) is 70cm >= 20cm threshold
    # Right gap (0.78 to 1.50m) is 72cm >= 20cm threshold
    assert len(empty_spots) == 2
    
    # Check statistics
    stats = db_session.query(OccupancyStatisticsModel).filter(OccupancyStatisticsModel.shelf_map_id == shelf.id).first()
    assert stats is not None
    # 0.08 / 1.5 = ~5.33% occupancy
    assert stats.occupancy_percentage == 5.33
