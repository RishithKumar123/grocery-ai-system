import pytest
import io
import cv2
import numpy as np
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.data.models.product_model import ProductModel
from app.data.models.user_model import UserModel
from app.core.security import get_password_hash, create_access_token

client = TestClient(app)


@pytest.fixture
def auth_headers(db_session: Session):
    user = UserModel(
        email="test_verifier@grocery.com",
        hashed_password=get_password_hash("VerifierPassword123!"),
        full_name="Verification QA Tester",
        role="Admin",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(subject=user.email)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_product(db_session: Session):
    product = ProductModel(
        name="Tata Salt Pure Iodized 1kg",
        brand="Tata",
        sku="TATA-SALT-1KG",
        barcode="8901058000052",
        category="Groceries",
        price=28.0
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def create_dummy_image_bytes():
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    # Draw green rectangle simulating a bottle/box container
    cv2.rectangle(img, (50, 50), (250, 250), (0, 255, 0), -1)
    is_success, buffer = cv2.imencode(".jpg", img)
    return buffer.tobytes()


def test_search_products_for_verification(client, auth_headers, sample_product):
    res = client.get(
        f"/api/v1/verification/products/search?query=Tata",
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert len(data["results"]) >= 1
    assert data["results"][0]["sku"] == "TATA-SALT-1KG"


def test_verify_product_status_endpoint(client, auth_headers, sample_product):
    res = client.get(
        f"/api/v1/verification/products/{sample_product.id}/verification-status",
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["product_id"] == sample_product.id
    assert "ready_for_verification" in data


def test_verify_product_presence_api(client, auth_headers, sample_product):
    img_bytes = create_dummy_image_bytes()
    files = {"file": ("test_scan.jpg", io.BytesIO(img_bytes), "image/jpeg")}

    res = client.post(
        f"/api/v1/verification/verify-product?product_id={sample_product.id}&confidence_threshold=0.5",
        headers=auth_headers,
        files=files
    )
    assert res.status_code == 200
    data = res.json()
    assert "present" in data
    assert "confidence" in data
    assert "quantity" in data
    assert "detection_time_ms" in data
