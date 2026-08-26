from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.ml.inference_engine import GroceryInferenceEngine, ModelNotConfiguredError
from app.ai_inference import repository as repo_module
from app.ai_inference import schemas
import shutil
import tempfile
from pathlib import Path

router = APIRouter(prefix="/inference", tags=["inference"])


def _save_upload_to_temp(file: UploadFile) -> str:
    suffix = Path(file.filename).suffix
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    with tf as f:
        shutil.copyfileobj(file.file, f)
    return tf.name


@router.post("/image", response_model=schemas.InferenceResultOut)
def infer_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    temp_path = _save_upload_to_temp(file)
    engine = GroceryInferenceEngine(db=db)
    try:
        out = engine.predict(source=temp_path)
    except ModelNotConfiguredError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

    repo = repo_module.SQLAlchemyInferenceRepository(db)
    job = repo.create_job(job_type="image")
    res = repo.add_result(
        job.id,
        source=temp_path,
        model_id=engine.manager.meta.path if engine.manager.meta else None,
        model_version=engine.manager.meta.loaded_at if engine.manager.meta else None,
        result_metadata={"inference_time_ms": out.get("inference_time_ms")},
    )
    for d in out.get("detections", []):
        repo.add_detection(res.id, d["class_id"], d["class_name"], d["confidence"], d["bbox"])

    return {
        "id": res.id,
        "source": res.source,
        "model_id": res.model_id,
        "model_version": res.model_version,
        "detections": out.get("detections", []),
    }
