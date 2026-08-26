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
        email="inventory_qa@grocery.com",
        hashed_password=get_password_hash("InventoryPassword123!"),
        full_name="Inventory QA Tester",
        role="Admin",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(subject=user.email)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def seed_data(db_session: Session):
    store = StoreModel(
        name="Main Store #1",
        location="NYC, NY",
        address="1 First St",
        contact="+12125550100",
        is_active=True
    )
    db_session.add(store)
    db_session.commit()

    prod = ProductModel(
        name="Surf Excel Easy Wash 1kg",
        brand="Unilever",
        sku="SURF-EXCEL-1KG",
        barcode="8901030000001",
        category="Detergents",
        price=140.0
    )
    db_session.add(prod)
    db_session.commit()

    inv = InventoryModel(
        store_id=store.id,
        product_id=prod.id,
        name=prod.name,
        sku=prod.sku,
        quantity=10,
        available_stock=10,
        reserved_stock=0,
        damaged_stock=0,
        min_stock=5,
        max_stock=50,
        reorder_level=10,
        location_bin="Shelf C1",
        status="In Stock"
    )
    db_session.add(inv)
    db_session.commit()

    return store, prod, inv


def test_apply_inventory_update_api(client, auth_headers, seed_data):
    store, prod, inv = seed_data

    payload = {
        "store_id": store.id,
        "product_id": prod.id,
        "new_quantity": 25,
        "confidence": 0.95
    }

    res = client.post("/api/v1/inventory-update/apply", json=payload, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["new_quantity"] == 25


def test_get_inventory_snapshots_api(client, auth_headers, seed_data):
    res = client.get("/api/v1/inventory-update/snapshots", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
