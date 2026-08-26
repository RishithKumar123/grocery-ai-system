import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.data.models.product_model import ProductModel
from app.data.models.shelf_mapping_model import (
    StoreMapModel,
    AisleMapModel,
    RackLocationModel,
    ShelfMapModel,
    PlanogramModel,
    ProductLocationModel,
    LocationHistoryModel,
    MisplacedProductModel,
    EmptyShelfModel,
    OccupancyStatisticsModel
)

logger = logging.getLogger("grocery_system")


class LocationIntelligenceService:
    """Enterprise Shelf Mapping & Location Intelligence Engine pipeline layer."""

    def assign_product_location(
        self,
        db: Session,
        shelf_map_id: int,
        product_id: int,
        x_relative: float,
        y_relative: float,
        facing_count: int,
        slot_number: int
    ) -> ProductLocationModel:
        """Saves a product's physical coordinate on a shelf, running compliance checks."""
        logger.info(f"LocationEngine: Mapping product={product_id} coordinates on shelf={shelf_map_id}")
        
        # 1. Fetch catalog validation parameters
        prod = db.query(ProductModel).filter(ProductModel.id == product_id).first()
        shelf = db.query(ShelfMapModel).filter(ShelfMapModel.id == shelf_map_id).first()
        if not prod or not shelf:
            raise ValueError("Catalog Product or Shelf Map ID not found.")

        # 2. Check if item was moved (Location History)
        existing_placement = db.query(ProductLocationModel).filter(
            ProductLocationModel.product_id == product_id,
            ProductLocationModel.shelf_map_id == shelf_map_id
        ).first()

        prev_shelf_id = None
        if not existing_placement:
            # Check if placed on another shelf
            other_placement = db.query(ProductLocationModel).filter(
                ProductLocationModel.product_id == product_id
            ).first()
            if other_placement:
                prev_shelf_id = other_placement.shelf_map_id
                # Remove from other shelf location
                db.delete(other_placement)

        # 3. PlanogramCompliance & Misplacement verification
        is_misplaced = False
        expected_plan = db.query(PlanogramModel).filter(
            PlanogramModel.shelf_map_id == shelf_map_id,
            PlanogramModel.product_id == product_id
        ).first()

        expected_shelf_map_id = None
        expected_pos_str = "Slot 1"
        detected_pos_str = f"Slot {slot_number}"

        if not expected_plan:
            # Product is not supposed to be on this shelf at all
            is_misplaced = True
            # Try to find where it belongs
            other_plan = db.query(PlanogramModel).filter(PlanogramModel.product_id == product_id).first()
            if other_plan:
                expected_shelf_map_id = other_plan.shelf_map_id
                expected_pos_str = f"Slot {other_plan.expected_position}"
        else:
            # Product is on correct shelf, verify slot position
            if expected_plan.expected_position != slot_number:
                is_misplaced = True
                expected_shelf_map_id = shelf_map_id
                expected_pos_str = f"Slot {expected_plan.expected_position}"

        # Write placement
        if existing_placement:
            existing_placement.x_relative = x_relative
            existing_placement.y_relative = y_relative
            existing_placement.facing_count = facing_count
            existing_placement.slot_number = slot_number
            existing_placement.is_misplaced = is_misplaced
            placement = existing_placement
        else:
            placement = ProductLocationModel(
                shelf_map_id=shelf_map_id,
                product_id=product_id,
                x_relative=x_relative,
                y_relative=y_relative,
                facing_count=facing_count,
                slot_number=slot_number,
                is_misplaced=is_misplaced
            )
            db.add(placement)

        # Save movement history
        if not existing_placement:
            history = LocationHistoryModel(
                product_id=product_id,
                previous_shelf_map_id=prev_shelf_id,
                new_shelf_map_id=shelf_map_id
            )
            db.add(history)

        # Handle Misplacement alerts
        if is_misplaced:
            # Delete old misplacement if exists to avoid logs bloating
            db.query(MisplacedProductModel).filter(
                MisplacedProductModel.product_id == product_id,
                MisplacedProductModel.detected_shelf_map_id == shelf_map_id
            ).delete()

            severity = "Low"
            if expected_shelf_map_id and expected_shelf_map_id != shelf_map_id:
                # Placed on wrong shelf entirely
                severity = "Medium"
                # Check category mismatch
                expected_shelf = db.query(ShelfMapModel).filter(ShelfMapModel.id == expected_shelf_map_id).first()
                if expected_shelf and expected_shelf.rack_location.aisle_map.aisle_name != shelf.rack_location.aisle_map.aisle_name:
                    severity = "High"

            misplaced = MisplacedProductModel(
                product_id=product_id,
                detected_shelf_map_id=shelf_map_id,
                expected_shelf_map_id=expected_shelf_map_id,
                detected_position=detected_pos_str,
                expected_position=expected_pos_str,
                severity=severity
            )
            db.add(misplaced)
            logger.warning(f"LocationEngine: Flagged Misplaced Product id={product_id} severity={severity}")
        else:
            # Resolved misplacement: remove record
            db.query(MisplacedProductModel).filter(
                MisplacedProductModel.product_id == product_id,
                MisplacedProductModel.detected_shelf_map_id == shelf_map_id
            ).delete()

        db.commit()
        db.refresh(placement)
        
        # Trigger recalculations of occupancy stats
        self.update_shelf_occupancy_stats(db, shelf_map_id)
        
        return placement

    def update_shelf_occupancy_stats(self, db: Session, shelf_map_id: int):
        """Recalculates occupancy percentages and vacant spots on a shelf."""
        shelf = db.query(ShelfMapModel).filter(ShelfMapModel.id == shelf_map_id).first()
        if not shelf:
            return

        placements = db.query(ProductLocationModel).filter(ProductLocationModel.shelf_map_id == shelf_map_id).all()
        
        # Deduct width: assume average product width is 0.08 meters (8cm)
        avg_prod_width = 0.08
        total_occupied_width = sum(p.facing_count * avg_prod_width for p in placements)
        
        occupancy_ratio = min((total_occupied_width / shelf.width_meters) * 100, 100.0)
        unassigned_ratio = max(100.0 - occupancy_ratio, 0.0)

        # Clear old stats
        db.query(OccupancyStatisticsModel).filter(OccupancyStatisticsModel.shelf_map_id == shelf_map_id).delete()
        
        stats = OccupancyStatisticsModel(
            shelf_map_id=shelf_map_id,
            occupancy_percentage=round(occupancy_ratio, 2),
            unassigned_space_percentage=round(unassigned_ratio, 2)
        )
        db.add(stats)

        # Gap detection for empty space tables
        db.query(EmptyShelfModel).filter(EmptyShelfModel.id == shelf_map_id).delete()

        # Sort placements by horizontal location x_relative
        sorted_p = sorted(placements, key=lambda p: p.x_relative)
        
        # Gaps check
        start_x = 0.0
        for p in sorted_p:
            gap = p.x_relative - start_x
            if gap >= 0.20: # Gaps larger than 20cm are empty shelf spaces
                empty_spot = EmptyShelfModel(
                    shelf_map_id=shelf_map_id,
                    empty_start_x=start_x,
                    empty_end_x=p.x_relative,
                    estimated_vacant_slots=int(gap // avg_prod_width)
                )
                db.add(empty_spot)
            # Update start_x past current product width
            start_x = p.x_relative + (p.facing_count * avg_prod_width)

        # Final trailing gap check
        trailing_gap = shelf.width_meters - start_x
        if trailing_gap >= 0.20:
            empty_spot = EmptyShelfModel(
                shelf_map_id=shelf_map_id,
                empty_start_x=start_x,
                empty_end_x=shelf.width_meters,
                estimated_vacant_slots=int(trailing_gap // avg_prod_width)
            )
            db.add(empty_spot)

        db.commit()

    def get_or_create_store_map(self, db: Session, store_id: int) -> StoreMapModel:
        """Seeds store map layout, aisles, racks, and planograms if not yet mapped."""
        store_map = db.query(StoreMapModel).filter(StoreMapModel.store_id == store_id).first()
        if store_map:
            return store_map

        # Seeding a spectacular interactive Store Map layout!
        store_map = StoreMapModel(
            store_id=store_id,
            map_name="Main Floor Layout",
            width_meters=40.0,
            height_meters=30.0
        )
        db.add(store_map)
        db.commit()
        db.refresh(store_map)

        # Seed Aisles (Beverages, Snacks, Fruits, Grains)
        aisles_data = [
            {"name": "Beverages Aisle", "sx": 5.0, "sy": 2.0, "ex": 5.0, "ey": 24.0},
            {"name": "Snacks & Sweets", "sx": 12.0, "sy": 2.0, "ex": 12.0, "ey": 24.0},
            {"name": "Bakery Dept", "sx": 19.0, "sy": 2.0, "ex": 19.0, "ey": 24.0},
            {"name": "Grains & Spices", "sx": 26.0, "sy": 2.0, "ex": 26.0, "ey": 24.0}
        ]

        for a in aisles_data:
            aisle = AisleMapModel(
                store_map_id=store_map.id,
                aisle_name=a["name"],
                start_x=a["sx"],
                start_y=a["sy"],
                end_x=a["ex"],
                end_y=a["ey"]
            )
            db.add(aisle)
            db.commit()
            db.refresh(aisle)

            # Seed 2 Racks per Aisle
            for r_idx in range(1, 3):
                rack = RackLocationModel(
                    aisle_map_id=aisle.id,
                    rack_number=f"{aisle.aisle_name[:3].upper()}-R{r_idx}",
                    x_coordinate=a["sx"],
                    y_coordinate=a["sy"] + (r_idx * 7.0)
                )
                db.add(rack)
                db.commit()
                db.refresh(rack)

                # Seed 3 Shelves levels per Rack
                for s_level in range(1, 4):
                    shelf = ShelfMapModel(
                        rack_location_id=rack.id,
                        shelf_level=f"Level {s_level}",
                        width_meters=1.6,
                        height_meters=0.4,
                        max_capacity=25
                    )
                    db.add(shelf)
                    db.commit()
                    db.refresh(shelf)

                    # Initial seed for planogram compliance mapping using standard catalog products
                    prods = db.query(ProductModel).limit(3).all()
                    for p_idx, prod in enumerate(prods):
                        plano = PlanogramModel(
                            shelf_map_id=shelf.id,
                            product_id=prod.id,
                            expected_position=p_idx + 1,
                            expected_facing_count=3
                        )
                        db.add(plano)
                    db.commit()

        db.refresh(store_map)
        return store_map
