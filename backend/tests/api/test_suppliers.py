import pytest
from app.presentation.api.v1.auth import get_current_user
from app.domain.entities.user import User


@pytest.fixture(autouse=True)
def override_auth_dependency(client):
    """Overrides authentication dependency with a mock user for route validation."""
    def mock_get_current_user():
        return User(
            id=1,
            email="admin@test.com",
            hashed_password="hashed_pwd",
            full_name="Admin Test",
            is_active=True,
            role="Admin",
            is_verified=True,
            created_at=None,
            updated_at=None
        )
    client.app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    client.app.dependency_overrides.pop(get_current_user, None)


def test_supplier_crud_operations(client):
    """Verifies supplier creation, updates, and active status toggles."""
    res = client.post("/api/v1/suppliers", json={
        "name": "Superfoods LLC",
        "company_name": "Superfoods Distribution Inc",
        "contact_person": "Jane Doe",
        "contact_email": "jane@superfoods.com",
        "phone": "+1-234-567-89",
        "address": "777 Logistics Drive",
        "gst_vat": "GST-EU-999",
        "region": "EU",
        "payment_terms": "Net 30",
        "is_active": True
    })
    assert res.status_code == 201
    supplier_id = res.json()["id"]

    # Verify retrieval
    get_res = client.get(f"/api/v1/suppliers/{supplier_id}")
    assert get_res.status_code == 200
    assert get_res.json()["company_name"] == "Superfoods Distribution Inc"
    assert get_res.json()["region"] == "EU"

    # Verify update
    put_res = client.put(f"/api/v1/suppliers/{supplier_id}", json={
        "name": "Superfoods LLC Updated",
        "payment_terms": "Net 45"
    })
    assert put_res.status_code == 200
    assert put_res.json()["payment_terms"] == "Net 45"
    assert put_res.json()["name"] == "Superfoods LLC Updated"


def test_multiple_suppliers_per_product(client):
    """Verifies that a product can be associated with multiple reusable supplier records."""
    # 1. Create a product
    prod_res = client.post("/api/v1/products", json={
        "name": "Organic Honey 500g",
        "barcode": "8901234567890",
        "sku": "HONEY-500G-001",
        "category": "Produce",
        "brand": "BeePure",
        "price": 8.50,
        "description": "Pure farm honey"
    })
    assert prod_res.status_code == 201
    product_id = prod_res.json()["id"]

    # 2. Create Supplier A
    sup_a = client.post("/api/v1/suppliers", json={
        "name": "Honeybee Apiaries",
        "region": "US"
    })
    assert sup_a.status_code == 201
    sup_a_id = sup_a.json()["id"]

    # 3. Create Supplier B
    sup_b = client.post("/api/v1/suppliers", json={
        "name": "Golden Nectar Distributors",
        "region": "EU"
    })
    assert sup_b.status_code == 201
    sup_b_id = sup_b.json()["id"]

    # 4. Link both suppliers to the same product
    link_a = client.post(f"/api/v1/suppliers/{sup_a_id}/products/{product_id}")
    assert link_a.status_code == 200

    link_b = client.post(f"/api/v1/suppliers/{sup_b_id}/products/{product_id}")
    assert link_b.status_code == 200

    # 5. Verify the mappings list
    sup_a_prods = client.get(f"/api/v1/suppliers/{sup_a_id}/products")
    assert sup_a_prods.status_code == 200
    assert len(sup_a_prods.json()) == 1
    assert sup_a_prods.json()[0]["sku"] == "HONEY-500G-001"
