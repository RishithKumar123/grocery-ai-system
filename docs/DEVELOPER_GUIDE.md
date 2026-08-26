# Developer Guide for YOLOv11 Grocery Detection System

This guide provides technical documentation for developers working with the YOLOv11 grocery detection system.

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  FastAPI     │  │  Endpoints   │  │  Auth        │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  Service Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Training    │  │  Inference   │  │  Model Mgmt  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  ML Layer                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  YOLO Model  │  │  Inference   │  │  Class Reg  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  Data Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  PostgreSQL  │  │  SQLite      │  │  File System │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Key Modules

#### ML Module (`app/ml/`)
- `model_manager.py`: Model loading and version management
- `inference_engine.py`: Inference orchestration and caching
- `training_service.py`: Training job management
- `class_registry.py`: Class name mapping and resolution
- `export_service.py`: Model export to various formats
- `dataset_validator.py`: Dataset validation and checking

#### AI Module (`app/ai/`)
- `detector.py`: Legacy detection (deprecated, use inference_engine)
- `pipeline.py`: Video processing pipeline
- `ocr.py`: OCR for text extraction
- `barcode_scanner.py`: Barcode detection and decoding
- `matching_engine.py`: Product matching logic

#### API Module (`app/presentation/api/v1/`)
- `inventory.py`: Inventory scanning endpoints
- `training.py`: Training management endpoints
- `model_registry.py`: Model versioning endpoints
- `dataset.py`: Dataset management endpoints

## Code Structure

### Directory Layout

```
backend/
├── app/
│   ├── ai/                    # AI components
│   │   ├── detector.py
│   │   ├── pipeline.py
│   │   ├── ocr.py
│   │   └── barcode_scanner.py
│   ├── core/                  # Core functionality
│   │   ├── config.py
│   │   ├── database.py
│   │   └── logging.py
│   ├── data/                  # Data models
│   │   ├── models/
│   │   └── repositories/
│   ├── ml/                    # ML components
│   │   ├── model_manager.py
│   │   ├── inference_engine.py
│   │   ├── training_service.py
│   │   ├── class_registry.py
│   │   ├── export_service.py
│   │   ├── dataset_validator.py
│   │   └── paths.py
│   ├── presentation/          # API layer
│   │   └── api/
│   │       └── v1/
│   │           ├── inventory.py
│   │           ├── training.py
│   │           └── model_registry.py
│   └── services/              # Business logic
├── dataset/                   # Dataset files
│   ├── data.yaml
│   ├── images/
│   └── labels/
├── logs/                      # Log files
├── models/                    # Model files
└── runs/                      # Training outputs
```

## Core Components

### GroceryInferenceEngine

The main inference engine for grocery detection.

```python
from app.ml.inference_engine import GroceryInferenceEngine

# Initialize
engine = GroceryInferenceEngine(db=db)

# Single image prediction
result = engine.predict(
    source=image_bytes,
    conf=0.5,
    iou=0.45,
    persist_track=False,
    use_cache=True
)

# Batch prediction
results = engine.predict_batch(
    sources=[image1, image2, image3],
    batch_size=8
)

# Cache management
engine.clear_cache()
engine.set_cache_enabled(False)
```

#### Key Features
- **Singleton Pattern**: Ensures single model instance
- **Caching**: Reduces redundant inference
- **Batch Processing**: Efficient multi-image processing
- **Unknown Product Handling**: Stores low-confidence detections
- **Product Catalog Integration**: Maps detections to products

### YoloModelManager

Manages YOLO model loading and versioning.

```python
from app.ml.model_manager import YoloModelManager

# Get singleton instance
manager = YoloModelManager.get()

# Load model
model_info = manager.load()

# Set active model
manager.set_active_model(
    weights_path=Path("models/best.pt"),
    persist=True
)

# Find latest trained weights
latest = manager.find_latest_trained_weights()

# Resolve production path
prod_path = manager.resolve_production_path()
```

#### Key Features
- **Forbidden Weights**: Blocks generic pretrained models
- **Auto-discovery**: Finds latest trained model
- **Version Management**: Tracks model versions
- **Production Safety**: Ensures only custom models used

### TrainingService

Orchestrates YOLO training jobs.

```python
from app.ml.training_service import YoloTrainingService

service = YoloTrainingService()

# Start training
job = service.start_training(config_overrides={
    "epochs": 200,
    "imgsz": 640,
    "batch": 8
})

# Resume training
job = service.resume_training(run_dir="runs/detect/train")

# Check job status
job = TrainingJobStore.get(job.job_id)
print(f"Status: {job.status}")
print(f"Metrics: {job.metrics}")
```

#### Key Features
- **Background Training**: Runs in separate threads
- **Job Management**: Tracks training progress
- **Auto-export**: Exports metrics and copies best model
- **Validation**: Validates dataset before training

## Database Schema

### Product Model

```python
class ProductModel(Base):
    __tablename__ = "products"
    
    id: int
    name: str
    barcode: str
    sku: str
    category: str
    brand: Optional[str]
    price: float
    cost_price: float
    tax: float
    
    # ML-specific fields
    yolo_class_mapping: Optional[int]  # Maps to YOLO class ID
    confidence_threshold: float        # Product-specific threshold
    clip_embeddings: Optional[str]      # CLIP embeddings
    ocr_reference_text: Optional[str]   # OCR reference text
```

### AI Scan Model

```python
class AIScanModel(Base):
    __tablename__ = "ai_scans"
    
    id: int
    scan_type: str
    image_path: str
    status: str
    created_at: datetime
    processed_at: Optional[datetime]
```

### AI Scan Detection Model

```python
class AIScanDetectionModel(Base):
    __tablename__ = "ai_scan_detections"
    
    id: int
    scan_id: int
    product_id: int
    confidence: float
    bounding_box: dict  # JSON with bbox details
    expiry_date_detected: Optional[datetime]
    raw_ocr_text: str
```

## API Endpoints

### Training Endpoints

```bash
# Start training
POST /api/v1/training/start
Query params: epochs, imgsz, batch, model

# Resume training
POST /api/v1/training/resume/{run_dir}

# Get job status
GET /api/v1/training/jobs/{job_id}

# List all jobs
GET /api/v1/training/jobs

# Validate dataset
GET /api/v1/training/validate

# Get data.yaml
GET /api/v1/training/data-yaml
```

### Inference Endpoints

```bash
# Scan inventory
POST /api/v1/inventory/scan
Body: image file

# Get scan results
GET /api/v1/inventory/scan/{scan_id}
```

### Model Registry Endpoints

```bash
# Register model
POST /api/v1/model-registry

# List models
GET /api/v1/model-registry

# Get model details
GET /api/v1/model-registry/{model_id}

# Deploy model
POST /api/v1/model-registry/{model_id}/deploy

# Rollback deployment
POST /api/v1/model-registry/deployments/{deployment_id}/rollback
```

## Configuration

### Settings

```python
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # YOLO Configuration
    YOLO_MODEL_PATH: str = "models/best.pt"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.5
    YOLO_IOU_THRESHOLD: float = 0.45
    
    # Paths
    DATASET_ROOT: str = "dataset"
    RUNS_ROOT: str = "runs"
    LOCAL_STORAGE_DIR: str = "storage"
    
    # Performance
    ENABLE_GPU: bool = True
    BATCH_SIZE: int = 8
    CACHE_ENABLED: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = True
```

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/grocery

# Model Configuration
YOLO_MODEL_PATH=/path/to/models/best.pt
YOLO_CONFIDENCE_THRESHOLD=0.5
YOLO_IOU_THRESHOLD=0.45

# Performance
ENABLE_GPU=true
BATCH_SIZE=8
CACHE_ENABLED=true

# Logging
LOG_LEVEL=INFO
```

## Development Workflow

### Setting Up Development Environment

```bash
# 1. Clone repository
git clone <repository-url>
cd <project-directory>

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup database
python scripts/init_db.py

# 5. Generate data.yaml
python generate_data_yaml.py

# 6. Validate dataset
python validate_dataset.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_inference.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_inference.py::test_predict
```

### Code Style

```bash
# Format code
black app/
isort app/

# Lint code
flake8 app/
pylint app/

# Type checking
mypy app/
```

## Extending the System

### Adding New Model Architectures

```python
# In model_manager.py
class YoloModelManager:
    def load_custom_model(self, architecture: str, weights_path: Path):
        """Load custom model architecture."""
        from ultralytics import YOLO
        
        if architecture == "custom":
            # Custom loading logic
            model = YOLO(str(weights_path))
            # Custom configuration
            return model
```

### Adding New Augmentation Techniques

```python
# In training_service.py
def _custom_augmentation_config():
    return {
        "custom_aug": True,
        "custom_params": {
            "rotation_range": 30,
            "brightness_range": 0.3,
            # Custom parameters
        }
    }
```

### Adding New Export Formats

```python
# In export_service.py
class YoloExportService:
    def export_tensorrt(self, weights_path: str):
        """Export to TensorRT format."""
        model = YOLO(weights_path)
        trt_path = model.export(format="engine", imgsz=640)
        return str(trt_path)
```

## Performance Optimization

### Inference Optimization

```python
# Enable caching
engine.set_cache_enabled(True)

# Use batch processing
results = engine.predict_batch(sources, batch_size=16)

# Reduce image size
result = engine.predict(source, conf=0.5, imgsz=512)

# Use smaller model
# In config: YOLO_MODEL_PATH = "models/yolo11s.pt"
```

### Training Optimization

```python
# Enable mixed precision
config = {"amp": True}

# Use larger batch size
config = {"batch": 16}

# Enable gradient accumulation
config = {"accumulate": 4}

# Use smaller image size for faster training
config = {"imgsz": 512}
```

## Debugging

### Common Debugging Techniques

```python
# Enable debug logging
import logging
logging.getLogger("ml").setLevel(logging.DEBUG)

# Check model loading
from app.ml.model_manager import YoloModelManager
manager = YoloModelManager.get()
print(f"Model loaded: {manager.model is not None}")

# Test inference
from app.ml.inference_engine import GroceryInferenceEngine
engine = GroceryInferenceEngine()
result = engine.predict(test_image)
print(f"Detections: {len(result['detections'])}")

# Validate dataset
from app.ml.dataset_validator import validate_dataset
report = validate_dataset()
print(f"Validation OK: {report.ok}")
```

### Logging

```python
from app.core.logging import (
    get_training_logger,
    get_inference_logger,
    get_prediction_logger,
    get_unknown_product_logger,
    get_error_logger
)

# Use specific loggers
training_logger = get_training_logger()
training_logger.info("Training started")

inference_logger = get_inference_logger()
inference_logger.info("Inference completed")

error_logger = get_error_logger()
error_logger.error("Error occurred", exc_info=True)
```

## Best Practices

### Code Organization
- Follow SOLID principles
- Use dependency injection
- Implement proper error handling
- Write comprehensive tests
- Document public APIs

### ML Best Practices
- Validate data before training
- Monitor training metrics
- Use proper evaluation metrics
- Implement model versioning
- Track experiments

### API Best Practices
- Use proper HTTP status codes
- Implement rate limiting
- Validate input data
- Use authentication/authorization
- Provide clear error messages

## Troubleshooting Development Issues

### Import Errors

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:/path/to/backend"

# Or use python -m
python -m app.main
```

### Database Issues

```bash
# Reset database
python scripts/reset_db.py

# Run migrations
python scripts/migrate.py

# Check connection
python scripts/test_db.py
```

### Model Loading Issues

```bash
# Check model file exists
ls -la models/best.pt

# Verify model format
python scripts/check_model.py

# Test model loading
python scripts/test_model_loading.py
```

## Contributing

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run tests and linting
6. Submit pull request

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Performance impact assessed

## Resources

### Internal Documentation
- [Training Guide](TRAINING_GUIDE.md)
- [Dataset Guide](DATASET_GUIDE.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)

### External Resources
- [Ultralytics Documentation](https://docs.ultralytics.com)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org)
- [PyTorch Documentation](https://pytorch.org/docs)

## Support

For development issues:
- Check existing documentation
- Review code examples
- Check logs for errors
- Contact development team
