from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.barcode import schemas
import shutil
import tempfile
from pathlib import Path
from typing import List
from pydantic import BaseModel
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect
import asyncio

router = APIRouter(prefix="/barcode", tags=["barcode"])


def _save_upload_to_temp(file: UploadFile) -> str:
    suffix = Path(file.filename).suffix
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    with tf as f:
        shutil.copyfileobj(file.file, f)
    return tf.name


@router.post("/scan", response_model=schemas.ScanResultSchema)
def scan_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    temp_path = _save_upload_to_temp(file)
    from app.barcode.service import BarcodeService, BarcodeEngineError
    svc = BarcodeService(db)
    try:
        out = svc.analyze_image_file(temp_path)
    except BarcodeEngineError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return out


class StartStreamRequest(BaseModel):
    source: str
    skip_frames: Optional[int] = 5


@router.post("/live/start")
def start_live(req: StartStreamRequest, db: Session = Depends(get_db)):
    from app.barcode.stream import stream_manager
    sid = stream_manager.start_stream(req.source, db, skip_frames=req.skip_frames)
    return {"stream_id": sid}


@router.post("/live/stop")
def stop_live(stream_id: str):
    from app.barcode.stream import stream_manager
    ok = stream_manager.stop_stream(stream_id)
    if not ok:
        raise HTTPException(status_code=404, detail="stream not found")
    return {"stopped": True}


@router.get("/live/status")
def live_status(stream_id: str):
    from app.barcode.stream import stream_manager
    s = stream_manager.status(stream_id)
    if s is None:
        raise HTTPException(status_code=404, detail="stream not found")
    return s


@router.websocket("/live/ws")
async def websocket_stream_status(websocket: WebSocket):
    await websocket.accept()
    params = websocket.query_params
    stream_id = params.get("stream_id")
    if not stream_id:
        await websocket.close(code=1008)
        return
    from app.barcode.stream import stream_manager
    try:
        while True:
            status = stream_manager.status(stream_id)
            if status is None:
                await websocket.send_json({"error": "stream_not_found"})
                await asyncio.sleep(1.0)
                continue
            await websocket.send_json(status)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        return


@router.get("/history", response_model=List[schemas.DetectionSchema])
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    from app.barcode.service import BarcodeService
    repo = BarcodeService(db).repo
    results = repo.list_history(limit=limit)
    out = []
    for r in results:
        out.append({"value": r.value, "barcode_type": r.barcode_type.name if r.barcode_type else None, "confidence": r.confidence, "bbox": r.bbox, "rotation": r.rotation})
    return out


@router.get("/unknowns")
def list_unknowns(db: Session = Depends(get_db)):
    repo = BarcodeService(db).repo
    return repo.list_unknowns()


@router.post("/unknowns/{unknown_id}/approve")
def approve_unknown(unknown_id: int, approve: bool, db: Session = Depends(get_db)):
    repo = BarcodeService(db).repo
    u = repo.mark_unknown_reviewed(unknown_id, approve)
    if not u:
        raise HTTPException(status_code=404, detail="Unknown barcode not found")
    return {"id": u.id, "approved": u.approved}
