import pytest
import numpy as np
from sqlalchemy.orm import Session

from app.data.models.product_model import ProductModel
from app.data.models.store_model import StoreModel
from app.data.models.inventory_model import InventoryModel
from app.ai.container_detector import ContainerDetector
from app.ai.embedding_engine import EmbeddingEngine
from app.services.decision_service import DecisionEngineService


def test_container_detector_mappings():
    detector = ContainerDetector()
    assert detector._map_to_container_type("bottle") == "bottle"
    assert detector._map_to_container_type("cup") == "bottle"
    assert detector._map_to_container_type("box") == "box"
    assert detector._map_to_container_type("bag") == "bag"
    assert detector._map_to_container_type("person") is None


def test_embedding_similarity_calculation():
    engine = EmbeddingEngine()
    
    # Dummy embedding vectors
    vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    vec2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    vec3 = np.array([0.0, 1.0, 0.0], dtype=np.float32)

    sim_identical = engine.calculate_similarity(vec1, vec2)
    sim_orthogonal = engine.calculate_similarity(vec1, vec3)

    assert round(sim_identical, 2) == 1.0
    assert round(sim_orthogonal, 2) == 0.0


def test_decision_engine_presence_resolution(db_session: Session):
    service = DecisionEngineService()

    # Seed catalog product
    prod = ProductModel(name="Patanjali Honey 500g", barcode="8901234567890", sku="PATANJALI-HONEY-500G", category="Groceries", price=220.0)
    db_session.add(prod)
    db_session.commit()

    # 1. Barcode match -> Expect YES (confidence ~ 0.98)
    res1 = service.resolve_decision(
        db=db_session,
        yolo_label="jar",
        ocr_text=None,
        barcode="8901234567890",
        embedding_similarity=0.5,
        target_product_id=prod.id
    )
    assert res1["present"] is True
    assert res1["confidence"] >= 0.9

    # 2. High OCR + Embedding Similarity -> Expect YES
    res2 = service.resolve_decision(
        db=db_session,
        yolo_label="jar",
        ocr_text="Patanjali Pure Honey",
        barcode=None,
        embedding_similarity=0.88,
        target_product_id=prod.id
    )
    assert res2["present"] is True

    # 3. Unrelated product text & low similarity -> Expect NO
    res3 = service.resolve_decision(
        db=db_session,
        yolo_label="box",
        ocr_text="Unrelated Brand Soap",
        barcode=None,
        embedding_similarity=0.2,
        target_product_id=prod.id
    )
    assert res3["present"] is False
