import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.data.models.product_model import ProductModel
from app.data.models.store_model import StoreModel
from app.data.models.inventory_model import InventoryModel
from app.data.models.user_model import UserModel
from app.core.security import get_password_hash, create_access_token

client = TestClient(app)


@pytest.fixture
def auth_headers(db_session: Session):
    user = UserModel(
        email="availability_qa@grocery.com",
        hashed_password=get_password_hash("AvailabilityPassword123!"),
        full_name="Availability QA Tester",
        role="Admin",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(subject=user.email)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def seed_store_and_inventory(db_session: Session):
    store = StoreModel(
        name="Central Grocery Store #101",
        location="Metropolis, NY",
        address="100 Main Street",
        contact="+12125550199",
        is_active=True
    )
    db_session.add(store)
    db_session.commit()

    prod = ProductModel(
        name="Maggi 2-Minute Masala Noodles",
        brand="Nestle",
        sku="MAGGI-NOD-70G",
        barcode="8901058852316",
        category="Instant Noodles",
        price=14.0
    )
    db_session.add(prod)
    db_session.commit()

    inv = InventoryModel(
        store_id=store.id,
        product_id=prod.id,
        name=prod.name,
        sku=prod.sku,
        quantity=50,
        available_stock=45,
        reserved_stock=5,
        damaged_stock=0,
        min_stock=10,
        max_stock=200,
        reorder_level=20,
        location_bin="Aisle 3 - Shelf B2",
        status="In Stock"
    )
    db_session.add(inv)
    db_session.commit()

    return store, prod, inv


def test_availability_by_product_id_api(client, auth_headers, seed_store_and_inventory):
    store, prod, inv = seed_store_and_inventory
    res = client.get(
        f"/api/v1/availability/product/{prod.id}?store_id={store.id}",
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "YES"
    assert data["available_quantity"] == 45
    assert data["product_id"] == prod.id


def test_availability_by_barcode_api(client, auth_headers, seed_store_and_inventory):
    store, prod, inv = seed_store_and_inventory
    res = client.get(
        f"/api/v1/availability/barcode/{prod.barcode}?store_id={store.id}",
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "YES"
    assert data["barcode"] == prod.barcode


def test_availability_stats_api(client, auth_headers):
    res = client.get("/api/v1/availability/stats", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_searches" in data
    assert "search_success_rate" in data
