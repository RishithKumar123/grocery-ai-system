import time
import json
import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.data.models.product_model import ProductModel
from app.data.models.store_model import StoreModel
from app.data.models.inventory_model import InventoryModel
from app.data.models.inventory_update_model import InventoryUpdateModel
from app.data.models.shelf_mapping_model import ProductLocationModel, ShelfMapModel, RackLocationModel, AisleMapModel
from app.data.models.availability_model import (
    AvailabilityRequestModel,
    AvailabilityResultModel,
    AvailabilityHistoryModel,
    AvailabilityCacheModel,
    AvailabilityStatisticsModel
)
from app.presentation.schemas.availability_schemas import AvailabilityCheckOut, NearestStoreInfo

logger = logging.getLogger("grocery_system")


class AvailabilityService:
    """Enterprise Product Availability Verification Engine pipeline layer."""

    def verify_availability(
        self,
        db: Session,
        store_id: int,
        search_query: str,
        search_method: str,
        user_id: Optional[int] = None
    ) -> AvailabilityCheckOut:
        start_time = time.time()
        logger.info(f"AvailabilityEngine: Verifying query='{search_query}' method='{search_method}' store={store_id}")

        # 1. Check Cache
        cache_key = f"avail:{store_id}:{search_method}:{search_query.strip().lower()}"
        cached = db.query(AvailabilityCacheModel).filter(
            AvailabilityCacheModel.cache_key == cache_key,
            AvailabilityCacheModel.expires_at > datetime.utcnow()
        ).first()

        if cached:
            try:
                data = json.loads(cached.cached_response)
                data["search_time_ms"] = round((time.time() - start_time) * 1000, 2)
                return AvailabilityCheckOut(**data)
            except Exception as e:
                logger.warning(f"Cache deserialization failed: {e}")

        # Record Request in DB
        req = AvailabilityRequestModel(
            store_id=store_id,
            search_query=search_query,
            search_method=search_method,
            user_id=user_id
        )
        db.add(req)
        db.commit()
        db.refresh(req)

        # 2. Check Store active status
        store = db.query(StoreModel).filter(StoreModel.id == store_id).first()
        if not store or (hasattr(store, 'is_active') and not store.is_active):
            return self._build_no_response(db, req, store_id, search_query, search_method, user_id, "Store closed or inactive", start_time)

        # 3. Product Catalog Lookup by search_method
        prod_query = db.query(ProductModel)
        if search_method == "Barcode":
            product = prod_query.filter(ProductModel.barcode == search_query).first()
        elif search_method == "SKU":
            product = prod_query.filter(ProductModel.sku == search_query).first()
        elif search_method == "Product ID":
            try:
                product = prod_query.filter(ProductModel.id == int(search_query)).first()
            except ValueError:
                product = None
        elif search_method == "Name":
            product = prod_query.filter(ProductModel.name.ilike(f"%{search_query}%")).first()
        else:
            product = prod_query.filter(
                (ProductModel.name.ilike(f"%{search_query}%")) |
                (ProductModel.sku == search_query) |
                (ProductModel.barcode == search_query)
            ).first()

        if not product:
            return self._build_no_response(db, req, store_id, search_query, search_method, user_id, "Product not found", start_time)

        # Check Product active status
        if hasattr(product, 'is_active') and not product.is_active:
            return self._build_no_response(db, req, store_id, search_query, search_method, user_id, "Product inactive", start_time, product)

        # 4. Inventory Lookup
        inv = db.query(InventoryModel).filter(
            InventoryModel.store_id == store_id,
            InventoryModel.product_id == product.id
        ).first()

        if not inv:
            return self._build_no_response(db, req, store_id, search_query, search_method, user_id, "Out of stock", start_time, product)

        if inv.quantity <= 0 or inv.available_stock <= 0:
            return self._build_no_response(db, req, store_id, search_query, search_method, user_id, "Out of stock", start_time, product)

        # 5. Check Expiry
        if inv.expiry_date and inv.expiry_date < date.today():
            return self._build_no_response(db, req, store_id, search_query, search_method, user_id, "Inventory expired", start_time, product)

        # 6. Latest AI Scan Verification Check
        latest_upd = db.query(InventoryUpdateModel).filter(
            InventoryUpdateModel.store_id == store_id,
            InventoryUpdateModel.product_id == product.id
        ).order_by(InventoryUpdateModel.created_at.desc()).first()

        confidence_score = inv.confidence if inv.confidence is not None else 0.95
        last_scan_time = inv.updated_at
        last_inv_update = inv.updated_at

        if latest_upd:
            confidence_score = latest_upd.confidence
            last_inv_update = latest_upd.created_at

        # 7. Shelf Location Lookup
        aisle_str, rack_str, shelf_str, bin_str = "Aisle 1", "R1", "Level 1", "Bin A1"
        loc = db.query(ProductLocationModel).filter(ProductLocationModel.product_id == product.id).first()
        if loc and loc.shelf_map:
            s_map = loc.shelf_map
            shelf_str = s_map.shelf_level
            if s_map.rack_location:
                rack_str = s_map.rack_location.rack_number
                if s_map.rack_location.aisle_map:
                    aisle_str = s_map.rack_location.aisle_map.aisle_name

        if inv.location_bin:
            bin_str = inv.location_bin

        # 8. All conditions satisfied -> YES!
        search_time = round((time.time() - start_time) * 1000, 2)
        
        result = AvailabilityCheckOut(
            status="YES",
            reason=None,
            product_id=product.id,
            product_name=product.name,
            sku=product.sku,
            barcode=product.barcode or "N/A",
            brand=product.brand or "Standard Brand",
            category=product.category or "General",
            available_quantity=inv.available_stock,
            unit="pcs",
            store_id=store.id,
            store_name=store.name,
            branch=getattr(store, "branch_code", f"Branch #{store.id}"),
            aisle=aisle_str,
            rack=rack_str,
            shelf=shelf_str,
            bin=bin_str,
            last_scan_time=last_scan_time,
            last_inventory_update=last_inv_update,
            confidence_score=confidence_score,
            product_image=product.image_url or inv.image_url,
            nearest_available_store=None,
            search_time_ms=search_time
        )

        # Log Result and History
        res_record = AvailabilityResultModel(
            availability_request_id=req.id,
            status="YES",
            product_id=product.id,
            confidence_score=confidence_score
        )
        db.add(res_record)

        hist = AvailabilityHistoryModel(
            product_id=product.id,
            store_id=store_id,
            search_query=search_query,
            search_method=search_method,
            status="YES",
            user_id=user_id
        )
        db.add(hist)
        db.commit()

        # Cache response for 5 minutes
        self._write_cache(db, cache_key, result)
        self._update_stats(db, store_id, True, search_time)

        return result

    def _build_no_response(
        self,
        db: Session,
        req: AvailabilityRequestModel,
        store_id: int,
        search_query: str,
        search_method: str,
        user_id: Optional[int],
        reason: str,
        start_time: float,
        product: Optional[ProductModel] = None
    ) -> AvailabilityCheckOut:
        # Multi-store fallback: check if another store has stock for this product
        nearest_info = None
        if product:
            alt_inv = db.query(InventoryModel).filter(
                InventoryModel.product_id == product.id,
                InventoryModel.store_id != store_id,
                InventoryModel.available_stock > 0
            ).first()

            if alt_inv and alt_inv.store:
                nearest_info = NearestStoreInfo(
                    store_id=alt_inv.store.id,
                    store_name=alt_inv.store.name,
                    branch=getattr(alt_inv.store, "branch_code", f"Branch #{alt_inv.store.id}"),
                    available_quantity=alt_inv.available_stock,
                    distance_km=2.5
                )

        search_time = round((time.time() - start_time) * 1000, 2)
        
        result = AvailabilityCheckOut(
            status="NO",
            reason=reason,
            product_id=product.id if product else None,
            product_name=product.name if product else search_query,
            sku=product.sku if product else None,
            barcode=product.barcode if product else None,
            brand=product.brand if product else None,
            category=product.category if product else None,
            available_quantity=0,
            store_id=store_id,
            nearest_available_store=nearest_info,
            search_time_ms=search_time
        )

        res_record = AvailabilityResultModel(
            availability_request_id=req.id,
            status="NO",
            product_id=product.id if product else None,
            reason=reason,
            nearest_store_id=nearest_info.store_id if nearest_info else None
        )
        db.add(res_record)

        hist = AvailabilityHistoryModel(
            product_id=product.id if product else None,
            store_id=store_id,
            search_query=search_query,
            search_method=search_method,
            status="NO",
            reason=reason,
            user_id=user_id
        )
        db.add(hist)
        db.commit()

        self._update_stats(db, store_id, False, search_time)
        return result

    def _write_cache(self, db: Session, cache_key: str, result: AvailabilityCheckOut):
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        # Clear existing key if any
        db.query(AvailabilityCacheModel).filter(AvailabilityCacheModel.cache_key == cache_key).delete()
        
        # Serialize to json
        res_dict = result.model_dump()
        # Convert datetime objects to iso strings
        for k in ["last_scan_time", "last_inventory_update"]:
            if res_dict.get(k) and isinstance(res_dict[k], (datetime, date)):
                res_dict[k] = res_dict[k].isoformat()

        cache_obj = AvailabilityCacheModel(
            cache_key=cache_key,
            cached_response=json.dumps(res_dict, default=str),
            expires_at=expires_at
        )
        db.add(cache_obj)
        db.commit()

    def _update_stats(self, db: Session, store_id: int, is_available: bool, search_time_ms: float):
        stat = db.query(AvailabilityStatisticsModel).filter(AvailabilityStatisticsModel.store_id == store_id).first()
        if not stat:
            stat = AvailabilityStatisticsModel(
                store_id=store_id,
                total_searches=0,
                available_count=0,
                unavailable_count=0,
                average_search_time_ms=search_time_ms
            )
            db.add(stat)

        stat.total_searches += 1
        if is_available:
            stat.available_count += 1
        else:
            stat.unavailable_count += 1

        # Moving average search time
        stat.average_search_time_ms = round(((stat.average_search_time_ms * (stat.total_searches - 1)) + search_time_ms) / stat.total_searches, 2)
        db.commit()
