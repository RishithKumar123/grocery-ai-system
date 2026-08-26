# YOLOv11 Custom Grocery Model Training Guide

This guide provides comprehensive instructions for training a custom YOLOv11 model for grocery product detection.

## Prerequisites

- Python 3.8+
- CUDA-capable GPU (recommended) or CPU
- 8GB+ RAM (16GB+ recommended)
- 20GB+ disk space

## Installation

```bash
# Install dependencies
pip install ultralytics torch torchvision opencv-python
pip install albumentations  # For additional augmentation
```

## Dataset Preparation

### 1. Product Catalog Setup

First, ensure your product catalog is populated in the database:

```python
# Run this script to update your product catalog
python update_products.py
```

### 2. Generate data.yaml

The system automatically generates `data.yaml` from your product catalog:

```bash
python generate_data_yaml.py
```

This creates:
- Class names from product names (slugified)
- Class ID mappings
- Dataset structure configuration

### 3. Collect and Annotate Images

#### Recommended Dataset Size
- **Minimum**: 50-100 images per class (500-1000 total)
- **Recommended**: 100-200 images per class (1000-2000 total)
- **Validation**: 10-20 images per class (100-200 total)

#### Annotation Tools

**Option 1: LabelImg (Recommended for beginners)**
```bash
pip install labelimg
labelimg dataset/images/train dataset/labels/train
```

**Option 2: CVAT (Web-based, collaborative)**
- Visit https://cvat.org
- Create project, upload images, annotate online
- Export in YOLO format

**Option 3: Roboflow (Web-based, with augmentation)**
- Visit https://roboflow.com
- Upload images, annotate online
- Export in YOLO format

#### Annotation Format

Each image should have a corresponding `.txt` file with the same name:
```
class_id x_center y_center width height
```

All values are normalized 0-1.

Example:
```
0 0.5 0.5 0.3 0.4
1 0.7 0.3 0.2 0.25
```

### 4. Organize Dataset Structure

```
dataset/
├── data.yaml
├── images/
│   ├── train/
│   │   ├── product1_001.jpg
│   │   ├── product1_002.jpg
│   │   └── ...
│   ├── val/
│   │   └── ...
│   └── test/
│       └── ...
└── labels/
    ├── train/
    │   ├── product1_001.txt
    │   ├── product1_002.txt
    │   └── ...
    ├── val/
    │   └── ...
    └── test/
        └── ...
```

### 5. Validate Dataset

```bash
python validate_dataset.py
```

This checks:
- Image/label correspondence
- Valid YOLO format
- Class ID ranges
- Duplicate images
- Corrupted files

## Training Configuration

### Default Configuration

The system uses these default training parameters:

```python
{
    "model": "yolo11m.pt",      # Medium model (balanced speed/accuracy)
    "epochs": 200,              # Training iterations
    "imgsz": 640,               # Image size
    "batch": 8,                 # Batch size (auto-detected)
    "optimizer": "AdamW",       # Optimizer
    "amp": True,                # Mixed precision training
    "patience": 30,             # Early stopping
    "cos_lr": True,             # Cosine learning rate
}
```

### Data Augmentation

Built-in augmentation (automatically applied):
- HSV color space augmentation (h=0.015, s=0.7, v=0.4)
- Rotation (±10°)
- Translation (±10%)
- Scale (±50%)
- Shear (±2°)
- Perspective (0.0005)
- Horizontal flip (50%)
- Mosaic (100%)
- Mixup (10%)
- Random erasing (20%)

### Custom Configuration

```bash
python train_model.py
```

Or use the API:

```bash
curl -X POST "http://localhost:8000/api/v1/training/start?epochs=300&imgsz=960&model=yolo11l.pt"
```

## Starting Training

### Option 1: Command Line

```bash
python train_model.py
```

### Option 2: API Endpoint

```bash
# Start training
curl -X POST "http://localhost:8000/api/v1/training/start" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check job status
curl "http://localhost:8000/api/v1/training/jobs/{job_id}"

# List all jobs
curl "http://localhost:8000/api/v1/training/jobs"
```

### Option 3: Resume Training

```bash
# Resume from a specific run directory
curl -X POST "http://localhost:8000/api/v1/training/resume/{run_dir}"
```

## Monitoring Training

### Training Logs

Training logs are saved to:
- `logs/training.log` - Detailed training information
- Console output - Real-time progress

### Metrics Tracked

- **mAP50**: Mean Average Precision at IoU=0.5
- **mAP50-95**: Mean Average Precision at IoU=0.5:0.95
- **Precision**: Detection precision
- **Recall**: Detection recall
- **Loss**: Training loss components

### Visualization

Training generates:
- `results.png` - Training metrics over time
- `confusion_matrix.png` - Class-wise performance
- `PR_curve.png` - Precision-Recall curve
- `F1_curve.png` - F1 score curve

## Model Selection

### Best vs Last Weights

- **best.pt**: Model with highest validation mAP
- **last.pt**: Model from final epoch (useful for resuming)

### Model Sizes

| Model | Parameters | Speed | Accuracy | VRAM |
|-------|-----------|-------|----------|------|
| yolo11n | 2.6M | Fastest | Good | 2GB |
| yolo11s | 9.4M | Fast | Better | 4GB |
| yolo11m | 20.1M | Balanced | Good | 8GB |
| yolo11l | 25.3M | Slower | Better | 12GB |
| yolo11x | 56.9M | Slowest | Best | 24GB |

## Exporting Models

### Export to TorchScript

```python
from app.ml.export_service import YoloExportService

service = YoloExportService()
exported = service.export_all("runs/detect/train/weights/best.pt")
```

### Export to ONNX

```python
# ONNX export is included in export_all()
exported = service.export_all("runs/detect/train/weights/best.pt")
# Returns: {"best_pt": "...", "torchscript": "...", "onnx": "..."}
```

## Troubleshooting

### Common Issues

**Issue: CUDA out of memory**
- Reduce batch size: `batch=4`
- Use smaller model: `model=yolo11s.pt`
- Reduce image size: `imgsz=512`

**Issue: Poor accuracy**
- Increase dataset size
- Check annotation quality
- Train for more epochs
- Use larger model: `model=yolo11l.pt`

**Issue: Overfitting**
- Add more data augmentation
- Increase dataset size
- Reduce model complexity
- Use dropout (in custom config)

**Issue: Slow training**
- Enable GPU
- Use mixed precision: `amp=True` (default)
- Reduce image size: `imgsz=512`
- Use smaller model

### Validation Issues

```bash
# Check dataset validation
python validate_dataset.py

# Fix common issues:
# - Missing labels: Add corresponding .txt files
# - Invalid class IDs: Ensure IDs match data.yaml
# - Corrupted images: Remove or re-download
```

## Best Practices

1. **Start Small**: Begin with yolo11s.pt and 50 images per class
2. **Iterate**: Gradually increase dataset size and model complexity
3. **Validate Often**: Check validation metrics during training
4. **Save Checkpoints**: Keep best.pt and last.pt for comparison
5. **Test in Production**: Validate model on real-world images before deployment

## Next Steps

After training:
1. Export model to production format
2. Test inference with sample images
3. Deploy to production environment
4. Monitor performance and collect feedback
5. Iterate with new data

## Support

For issues:
- Check logs in `logs/` directory
- Review training metrics in `runs/detect/train/`
- Validate dataset with `validate_dataset.py`
- Consult Ultralytics documentation: https://docs.ultralytics.com
