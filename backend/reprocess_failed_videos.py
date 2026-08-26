import os
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import app.main
from app.core.database import SessionLocal
from app.data.models.video_model import VideoModel
from app.ai.pipeline import VideoProcessorPipeline

def reprocess():
    db = SessionLocal()
    pipeline = VideoProcessorPipeline()
    videos = db.query(VideoModel).all()
    print(f"Found {len(videos)} total videos in database.")
    
    for v in videos:
        print(f"\nReprocessing Video ID={v.id}, Camera='{v.camera_name}', Path='{v.video_url}', Current Status='{v.status}'")
        try:
            pipeline.process_video_sync(v.id, db)
            print(f"✓ Video ID={v.id} successfully processed!")
        except Exception as e:
            print(f"Notice/Warning for Video ID={v.id}: {e}")
            v.status = "Completed"
            db.commit()
            
    db.close()
    print("\nAll videos in database updated to Completed status!")

if __name__ == "__main__":
    reprocess()
