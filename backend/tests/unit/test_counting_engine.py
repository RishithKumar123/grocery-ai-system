import pytest
from sqlalchemy.orm import Session
from app.data.models.product_model import ProductModel
from app.services.counting_service import CountingEngineService


def test_spatial_iou_overlapping_boxes():
    service = CountingEngineService()

    # Box 1
    box1 = {"xmin": 0.1, "ymin": 0.1, "xmax": 0.3, "ymax": 0.3}
    # Box 2 (Identical Box)
    assert service.calculate_iou(box1, box1) == 1.0

    # Box 3 (Partial overlap)
    box3 = {"xmin": 0.2, "ymin": 0.2, "xmax": 0.4, "ymax": 0.4}
    # Intersection: (0.3 - 0.2) * (0.3 - 0.2) = 0.01
    # Area1: 0.04, Area2: 0.04. Union = 0.04 + 0.04 - 0.01 = 0.07
    # IoU: 0.01 / 0.07 = 0.1428
    assert abs(service.calculate_iou(box1, box3) - 0.1428) < 0.001

    # Box 4 (No intersection)
    box4 = {"xmin": 0.5, "ymin": 0.5, "xmax": 0.7, "ymax": 0.7}
    assert service.calculate_iou(box1, box4) == 0.0


def test_count_static_images_deduplication(db_session: Session):
    service = CountingEngineService()

    # 1. Seed sample product
    prod = ProductModel(
        name="Aetheria Premium Juice 1L",
        barcode="7890123456789",
        sku="BEV-JUICE-1L",
        category="Beverages",
        price=120.0
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)

    # 2. Duplicate detections (IoU = 1.0)
    dets = [
        {
            "yolo_label": "juice",
            "barcode": "7890123456789",
            "confidence": 0.92,
            "bounding_box": {"xmin": 0.1, "ymin": 0.1, "xmax": 0.3, "ymax": 0.3}
        },
        {
            "yolo_label": "juice",
            "barcode": "7890123456789",
            "confidence": 0.88,
            "bounding_box": {"xmin": 0.1, "ymin": 0.1, "xmax": 0.3, "ymax": 0.3}
        },
        # Low confidence detection (confidence < 0.50)
        {
            "yolo_label": "juice",
            "barcode": "7890123456789",
            "confidence": 0.35,
            "bounding_box": {"xmin": 0.4, "ymin": 0.4, "xmax": 0.6, "ymax": 0.6}
        }
    ]

    res = service.count_static_images(
        db=db_session,
        store_id=1,
        shelf_id=None,
        detections=dets
    )

    # Dets: 3 raw. 1 low-confidence rejected, 1 overlap duplicate removed, 1 verified!
    assert res["total_counted"] == 1
    assert res["raw_count"] == 3
    assert res["duplicate_count"] == 1
    assert res["rejected_count"] == 1


def test_video_tracking_simulation_job(db_session: Session):
    service = CountingEngineService()

    job = service.simulate_video_tracking_job(
        db=db_session,
        store_id=1,
        video_id=None,
        user_id=None,
        config={"min_confidence": 0.5, "tracking_timeout": 30}
    )

    assert job.status == "Completed"
    assert job.total_counted > 0
    assert len(job.results) > 0
    assert len(job.tracks) > 0
    assert job.statistics is not None
    assert job.statistics.total_products_counted == job.total_counted
