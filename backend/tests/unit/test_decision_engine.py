import pytest
from sqlalchemy.orm import Session
from app.core.database import Base
from app.data.models.product_model import ProductModel
from app.data.models.decision_model import (
    DecisionResultModel,
    DecisionCandidateModel,
    DecisionRuleModel,
    DecisionWeightModel,
    DecisionFeedbackModel
)
from app.services.decision_service import DecisionEngineService
from app.presentation.api.v1.auth import get_current_user
from fastapi.testclient import TestClient
from app.main import app


# Test suite verifying Multi-Model Decision Engine logic

def test_decision_similarity_metric():
    service = DecisionEngineService()
    # Identical words intersection
    assert service.calculate_similarity("Coca-Cola 500ml", "Coca-Cola 500ml") == 1.0
    # Overlapping strings
    assert abs(service.calculate_similarity("Coca-Cola 500ml", "Pepsi 500ml") - 0.3333) < 0.001
    # Empty inputs
    assert service.calculate_similarity("", "Pepsi") == 0.0


def test_decision_resolution_logic(db_session: Session):
    service = DecisionEngineService()
    
    # 1. Seed Product Catalog item
    prod1 = ProductModel(
        name="Lipton Ice Tea Lemon 1L",
        barcode="8901030665324",
        sku="BEV-LIP-ICE-TEA",
        category="Drinks",
        brand="Lipton",
        price=75.00
    )
    db_session.add(prod1)
    db_session.commit()
    db_session.refresh(prod1)

    # 2. Run resolution with exact barcode matching
    decision = service.resolve_decision(
        db=db_session,
        yolo_label="bottle",
        ocr_text="Lipton Tea",
        barcode="8901030665324"
    )

    assert decision["product_id"] == prod1.id
    assert decision["present"] is True
    assert decision["confidence"] == 1.0


def test_decision_low_confidence_fallback(db_session: Session):
    service = DecisionEngineService()

    # Run resolution with no matched barcode or name likeness
    decision = service.resolve_decision(
        db=db_session,
        yolo_label="unknown_class",
        ocr_text="NonExistentProductOCRLabelXYZ",
        barcode="0000000000000"
    )

    assert decision["present"] is False
