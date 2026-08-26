from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.domain.entities.user import User
from app.presentation.api.v1.auth import get_current_user
from app.data.models.decision_model import (
    DecisionResultModel,
    DecisionRuleModel,
    DecisionWeightModel,
    DecisionFeedbackModel
)
from app.data.models.product_model import ProductModel
from app.services.decision_service import DecisionEngineService
from app.presentation.schemas.decision_schemas import (
    DecisionPayload,
    BatchDecisionPayload,
    DecisionOut,
    RuleOut,
    RuleUpdate,
    WeightsOut,
    WeightsUpdate,
    FeedbackSubmit
)

router = APIRouter(prefix="/decisions", tags=["multi-model-decision-engine"])
service = DecisionEngineService()


@router.post("/resolve", response_model=DecisionOut, status_code=status.HTTP_201_CREATED)
def resolve_prediction_decision(
    payload: DecisionPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fuses prediction indicators to resolve a single product identity decision."""
    decision = service.resolve_decision(
        db=db,
        yolo_label=payload.yolo_label,
        ocr_text=payload.ocr_text,
        barcode=payload.barcode,
        embedding_similarity=payload.embedding_similarity,
        video_id=payload.video_id,
        store_id=payload.store_id
    )
    return decision


@router.post("/batch", response_model=List[DecisionOut], status_code=status.HTTP_201_CREATED)
def resolve_batch_prediction_decisions(
    payload: BatchDecisionPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Processes batch recognition frames predictions."""
    results = []
    for item in payload.items:
        decision = service.resolve_decision(
            db=db,
            yolo_label=item.yolo_label,
            ocr_text=item.ocr_text,
            barcode=item.barcode,
            embedding_similarity=item.embedding_similarity,
            video_id=payload.video_id,
            store_id=payload.store_id
        )
        results.append(decision)
    return results


@router.get("/history", response_model=List[DecisionOut])
def get_decision_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve list of all historical AI fused decisions."""
    decisions = db.query(DecisionResultModel).order_by(DecisionResultModel.created_at.desc()).all()
    return decisions


@router.get("/rules", response_model=List[RuleOut])
def get_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve configurable business rules for resolution overrides."""
    return service.get_or_create_rules(db)


@router.put("/rules/{rule_key}", response_model=RuleOut)
def update_rule(
    rule_key: str,
    payload: RuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Modify parameter value or state of an access/fusion rule."""
    rule = db.query(DecisionRuleModel).filter(DecisionRuleModel.rule_key == rule_key).first()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_key}' not found.")
    
    rule.value = payload.value
    if payload.is_active is not None:
        rule.is_active = payload.is_active

    db.commit()
    db.refresh(rule)
    return rule


@router.get("/weights", response_model=WeightsOut)
def get_weights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve weights parameters assigned to YOLO, OCR, and Barcode models."""
    return service.get_or_create_weights(db)


@router.put("/weights", response_model=WeightsOut)
def update_weights(
    payload: WeightsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Modify model weighting coefficients dynamically without rebuilding codes."""
    total = payload.yolo_weight + payload.ocr_weight + payload.barcode_weight + payload.embedding_weight
    if not (0.95 <= total <= 1.05):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Coefficients must normalize approximately to 1.0. Current sum: {total:.2f}"
        )

    weights = service.get_or_create_weights(db)
    weights.yolo_weight = payload.yolo_weight
    weights.ocr_weight = payload.ocr_weight
    weights.barcode_weight = payload.barcode_weight
    weights.embedding_weight = payload.embedding_weight

    db.commit()
    db.refresh(weights)
    return weights


@router.get("/analytics/summary")
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aggregates telemetry stats on AI performance metrics."""
    decisions = db.query(DecisionResultModel).all()
    if not decisions:
        return {
            "total_decisions": 0,
            "conflict_rate": 0.0,
            "unknown_rate": 0.0,
            "average_confidence": 0.0,
            "accuracy": 100.0
        }

    total = len(decisions)
    unknowns = sum(1 for d in decisions if d.selected_product_id is None)
    conflicts = 0
    total_conf = 0.0

    for d in decisions:
        total_conf += d.final_confidence
        # Conflict metric: Barcode and OCR values are both present but represent different names
        if d.raw_barcode and d.raw_ocr_text:
            conflicts += 1

    approved = sum(1 for d in decisions if d.status in ["Approved", "Corrected"])

    return {
        "total_decisions": total,
        "conflict_rate": round((conflicts / total) * 100, 2),
        "unknown_rate": round((unknowns / total) * 100, 2),
        "average_confidence": round((total_conf / total) * 100, 2),
        "accuracy": round((approved / total) * 100, 2)
    }


@router.post("/{decision_id}/feedback", response_model=DecisionOut)
def submit_decision_feedback(
    decision_id: int,
    payload: FeedbackSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Correct classification tags and append feedback override layers."""
    decision = db.query(DecisionResultModel).filter(DecisionResultModel.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision record not found.")

    if payload.corrected_product_id:
        prod = db.query(ProductModel).filter(ProductModel.id == payload.corrected_product_id).first()
        if not prod:
            raise HTTPException(status_code=400, detail="Corrected product not in catalog.")
        
        decision.selected_product_id = payload.corrected_product_id
        decision.status = "Corrected"
        decision.final_confidence = 1.0

    feedback = DecisionFeedbackModel(
        decision_id=decision.id,
        user_id=current_user.id,
        corrected_product_id=payload.corrected_product_id,
        notes=payload.notes
    )
    db.add(feedback)
    db.commit()
    db.refresh(decision)
    return decision


@router.post("/{decision_id}/approve", response_model=DecisionOut)
def approve_decision(
    decision_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve prediction match candidate."""
    decision = db.query(DecisionResultModel).filter(DecisionResultModel.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision record not found.")
    
    decision.status = "Approved"
    db.commit()
    db.refresh(decision)
    return decision


@router.post("/{decision_id}/reject", response_model=DecisionOut)
def reject_decision(
    decision_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reject prediction match candidate."""
    decision = db.query(DecisionResultModel).filter(DecisionResultModel.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision record not found.")
    
    decision.status = "Rejected"
    db.commit()
    db.refresh(decision)
    return decision


@router.get("/{decision_id}", response_model=DecisionOut)
def get_decision_details(
    decision_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve detailed candidate comparisons and metrics for a single decision."""
    decision = db.query(DecisionResultModel).filter(DecisionResultModel.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision record not found.")
    return decision
