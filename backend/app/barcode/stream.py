import threading
import time
import uuid
from typing import Optional, Dict, Any


class StreamProcessor:
    def __init__(self, source: str, db_session, skip_frames: int = 5, scanned_by_id: Optional[int] = None):
        self.source = source
        self.db = db_session
        self.skip_frames = max(1, skip_frames)
        self.scanned_by_id = scanned_by_id
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.id = str(uuid.uuid4())
        self._stats = {"frames": 0, "detections": 0, "start_time": None}

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self.id

    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def status(self) -> Dict[str, Any]:
        return {"id": self.id, "frames": self._stats.get("frames", 0), "detections": self._stats.get("detections", 0)}

    def _run(self):
        # import cv2 lazily inside thread
        import cv2
        from app.barcode.service import BarcodeService

        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            return

        svc = BarcodeService(self.db)
        self._stats["start_time"] = time.time()
        frame_idx = 0
        # create a scan record to associate frames
        scan = svc.repo.create_scan(source=self.source, scanned_by_id=self.scanned_by_id)

        try:
            while not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                frame_idx += 1
                self._stats["frames"] = frame_idx
                if frame_idx % self.skip_frames != 0:
                    continue
                detections = svc.process_frame(scan.id, frame, scanned_by_id=self.scanned_by_id)
                self._stats["detections"] += len(detections)
        finally:
            cap.release()


class StreamManager:
    def __init__(self):
        self._streams: Dict[str, StreamProcessor] = {}

    def start_stream(self, source: str, db_session, skip_frames: int = 5, scanned_by_id: Optional[int] = None) -> str:
        sp = StreamProcessor(source, db_session, skip_frames=skip_frames, scanned_by_id=scanned_by_id)
        sid = sp.start()
        self._streams[sid] = sp
        return sid

    def stop_stream(self, sid: str) -> bool:
        sp = self._streams.get(sid)
        if not sp:
            return False
        sp.stop()
        del self._streams[sid]
        return True

    def status(self, sid: str):
        sp = self._streams.get(sid)
        if not sp:
            return None
        return sp.status()


stream_manager = StreamManager()
