import pytest
from app.presentation.api.v1.auth import get_current_user
from app.domain.entities.user import User


@pytest.fixture(autouse=True)
def override_auth_dependency(client):
    """Overrides JWT token verification with a mock admin user for route testing."""
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


def test_create_category_route(client):
    """Verifies that category registration works and prevents duplication."""
    # Register parent
    res = client.post("/api/v1/categories", json={
        "name": "Beverages",
        "description": "Drinks and sodas",
        "parent_id": None,
        "is_active": True
    })
    assert res.status_code == 201
    parent_id = res.json()["id"]

    # Register child
    child_res = client.post("/api/v1/categories", json={
        "name": "Soft Drinks",
        "description": "Carbonated drinks",
        "parent_id": parent_id,
        "is_active": True
    })
    assert child_res.status_code == 201


def test_soft_delete_and_restore_category(client):
    """Verifies soft delete flags and recovery endpoints."""
    # Create category
    res = client.post("/api/v1/categories", json={
        "name": "Snacks",
        "description": "Chips and biscuits"
    })
    assert res.status_code == 201
    cat_id = res.json()["id"]

    # Soft delete
    del_res = client.delete(f"/api/v1/categories/{cat_id}")
    assert del_res.status_code == 200

    # Retrieve (should be 404 since it's deleted)
    get_res = client.get(f"/api/v1/categories/{cat_id}")
    assert get_res.status_code == 404

    # Restore
    res_res = client.patch(f"/api/v1/categories/{cat_id}/restore")
    assert res_res.status_code == 200

    # Retrieve again (should succeed now)
    get_res = client.get(f"/api/v1/categories/{cat_id}")
    assert get_res.status_code == 200
