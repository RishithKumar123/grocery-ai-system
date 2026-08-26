"""
Train YOLOv11 on custom grocery product dataset.
"""
from app.ml.training_service import YoloTrainingService
from app.core.logging import logger

def main():
    print("Starting YOLOv11 training for grocery product detection...")
    print("=" * 60)
    
    service = YoloTrainingService()
    
    # Training configuration (can be customized)
    config = {
        "model": "yolo11m.pt",  # or "yolo11l.pt" for better accuracy
        "epochs": 200,
        "imgsz": 640,  # or 960 for higher resolution
        "batch": 8,  # will auto-detect based on GPU memory
        "optimizer": "AdamW",
        "amp": True,  # Mixed precision training
        "patience": 30,  # Early stopping
        "cos_lr": True,  # Cosine learning rate
    }
    
    print(f"Configuration: {config}")
    print("\nStarting training job...")
    
    try:
        job = service.start_training(config_overrides=config)
        print(f"Training job started: {job.job_id}")
        print(f"Status: {job.status}")
        print(f"\nMonitor training progress in: runs/detect/{job.config['name']}")
        print("\nTraining will run in the background.")
        print("Check logs for progress updates.")
        
        return job
    except Exception as e:
        logger.error(f"Failed to start training: {e}")
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. Prepared dataset with images and labels")
        print("2. Generated data.yaml with correct class mappings")
        print("3. Installed ultralytics: pip install ultralytics")
        return None

if __name__ == "__main__":
    main()
