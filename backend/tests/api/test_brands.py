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


def test_create_brand_route(client):
    """Verifies that brand registration works and prevents duplication."""
    res = client.post("/api/v1/brands", json={
        "name": "Cadbury",
        "description": "Chocolate products maker",
        "country_of_origin": "UK",
        "website": "https://cadbury.co.uk",
        "is_active": True
    })
    assert res.status_code == 201
    
    # Try duplicate name
    dup = client.post("/api/v1/brands", json={
        "name": "Cadbury"
    })
    assert dup.status_code == 400


def test_soft_delete_and_restore_brand(client):
    """Verifies soft delete flags and recovery endpoints."""
    # Create brand
    res = client.post("/api/v1/brands", json={
        "name": "Nestle",
        "description": "Food and beverage maker"
    })
    assert res.status_code == 201
    brand_id = res.json()["id"]

    # Soft delete
    del_res = client.delete(f"/api/v1/brands/{brand_id}")
    assert del_res.status_code == 200

    # Retrieve (should be 404 since it's deleted)
    get_res = client.get(f"/api/v1/brands/{brand_id}")
    assert get_res.status_code == 404

    # Restore
    res_res = client.patch(f"/api/v1/brands/{brand_id}/restore")
    assert res_res.status_code == 200

    # Retrieve again (should succeed now)
    get_res = client.get(f"/api/v1/brands/{brand_id}")
    assert get_res.status_code == 200
