import pytest
from sqlalchemy.orm import Session
from app.data.models.product_model import ProductModel
from app.data.models.store_model import StoreModel
from app.data.models.inventory_model import InventoryModel
from app.services.availability_service import AvailabilityService


def test_availability_verification_yes_and_no_conditions(db_session: Session):
    service = AvailabilityService()

    # Seed Store
    store1 = StoreModel(name="Main Supermarket", location="Central Ave")
    store2 = StoreModel(name="Downtown Branch", location="Downtown")
    db_session.add_all([store1, store2])
    db_session.commit()

    # Seed Products
    prod1 = ProductModel(name="Aetheria Milk 1L", barcode="6666666666666", sku="MILK-1L", category="Dairy", price=75.0)
    prod2 = ProductModel(name="Aetheria Butter 200g", barcode="7777777777777", sku="BUTTER-200G", category="Dairy", price=140.0)
    db_session.add_all([prod1, prod2])
    db_session.commit()

    # Seed Inventory: prod1 in stock at store1 (qty=10), prod2 out of stock at store1 (qty=0) but in stock at store2 (qty=15)
    inv1 = InventoryModel(store_id=store1.id, product_id=prod1.id, name=prod1.name, sku=prod1.sku, quantity=10, available_stock=10)
    inv2 = InventoryModel(store_id=store1.id, product_id=prod2.id, name=prod2.name, sku=prod2.sku, quantity=0, available_stock=0)
    inv3 = InventoryModel(store_id=store2.id, product_id=prod2.id, name=prod2.name, sku=prod2.sku, quantity=15, available_stock=15)
    db_session.add_all([inv1, inv2, inv3])
    db_session.commit()

    # 1. Check Available Product -> Expect YES
    res1 = service.verify_availability(db=db_session, store_id=store1.id, search_query="MILK-1L", search_method="SKU")
    assert res1.status == "YES"
    assert res1.product_id == prod1.id
    assert res1.available_quantity == 10
    assert res1.reason is None

    # 2. Check Out of Stock Product -> Expect NO with Nearest Store fallback
    res2 = service.verify_availability(db=db_session, store_id=store1.id, search_query="BUTTER-200G", search_method="SKU")
    assert res2.status == "NO"
    assert res2.reason == "Out of stock"
    assert res2.nearest_available_store is not None
    assert res2.nearest_available_store.store_id == store2.id
    assert res2.nearest_available_store.available_quantity == 15

    # 3. Check Non-existent Product -> Expect NO
    res3 = service.verify_availability(db=db_session, store_id=store1.id, search_query="NONEXISTENT", search_method="Name")
    assert res3.status == "NO"
    assert res3.reason == "Product not found"
