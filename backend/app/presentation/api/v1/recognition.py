from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.product_recognition import schemas
from app.product_recognition.service import ProductRecognitionService

router = APIRouter(prefix="/recognition", tags=["recognition"])


@router.post("/recognize", response_model=schemas.RecognizeResponse)
def recognize(req: schemas.RecognizeRequest, db: Session = Depends(get_db)):
    svc = ProductRecognitionService(db)
    payload = req.model_dump()
    out = svc.recognize(payload)
    return out


@router.get("/unknowns")
def list_unknowns(db: Session = Depends(get_db)):
    repo = ProductRecognitionService(db).repo
    return repo.db.query(repo.db.models.UnknownProductModel).order_by(repo.db.models.UnknownProductModel.created_at.desc()).limit(50).all()


@router.post("/{match_id}/feedback")
def feedback(match_id: int, correct_product_id: int | None = None, comment: str | None = None, db: Session = Depends(get_db)):
    repo = ProductRecognitionService(db).repo
    f = repo.add_feedback(match_id, None, correct_product_id, comment)
    return {"id": f.id}
