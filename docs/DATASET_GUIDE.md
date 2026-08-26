# Dataset Guide for YOLOv11 Grocery Detection

This guide covers dataset preparation, annotation, and management for training custom grocery product detection models.

## Dataset Structure

### Required Directory Layout

```
dataset/
├── data.yaml              # Dataset configuration
├── images/
│   ├── train/             # Training images
│   ├── val/               # Validation images
│   └── test/              # Test images
└── labels/
    ├── train/             # Training annotations
    ├── val/               # Validation annotations
    └── test/              # Test annotations
```

### File Naming Convention

- Images: `{product_name}_{sequence_number}.{ext}`
- Labels: `{product_name}_{sequence_number}.txt`

Example:
```
images/train/patanjali_honey_001.jpg
labels/train/patanjali_honey_001.txt
```

## Data Generation

### 1. Product Catalog Integration

The system automatically generates class mappings from your product catalog:

```bash
python generate_data_yaml.py
```

This creates:
- `data.yaml` with class names and IDs
- Updates `yolo_class_mapping` in database

### 2. Image Collection Guidelines

#### Image Quality Requirements
- **Resolution**: Minimum 640x640 pixels
- **Format**: JPG, PNG, WebP
- **Lighting**: Consistent, well-lit conditions
- **Background**: Clean, minimal clutter
- **Angle**: Multiple angles (front, side, top)

#### Recommended Images per Product
- **Minimum**: 50 images
- **Recommended**: 100-200 images
- **Variations**: Different lighting, angles, backgrounds

#### Image Collection Tips
1. **Multiple Angles**: Capture products from different perspectives
2. **Lighting Variation**: Include different lighting conditions
3. **Background Variety**: Use different backgrounds to improve generalization
4. **Scale Variation**: Include products at different distances/sizes
5. **Occlusion Handling**: Include partially occluded products

## Annotation Process

### Annotation Tools

#### LabelImg (Desktop Application)

```bash
pip install labelimg
labelimg dataset/images/train dataset/labels/train
```

**Features**:
- Desktop application
- Real-time annotation
- YOLO format export
- Keyboard shortcuts

**Workflow**:
1. Open LabelImg with dataset paths
2. Draw bounding boxes around products
3. Select correct class label
4. Save automatically generates .txt file

#### CVAT (Web-based)

**Setup**:
1. Visit https://cvat.org
2. Create new project
3. Upload images
4. Configure task settings
5. Start annotation

**Features**:
- Collaborative annotation
- Advanced tools
- Quality control
- Version control

**Export**:
1. Go to "Export task dataset"
2. Select "YOLO 1.1" format
3. Download and extract to dataset directory

#### Roboflow (Web-based with Augmentation)

**Setup**:
1. Visit https://roboflow.com
2. Create new workspace
3. Upload images
4. Use annotation tools
5. Apply augmentations

**Features**:
- Built-in augmentation
- Auto-labeling (optional)
- Cloud storage
- API access

**Export**:
1. Go to "Export Dataset"
2. Select "YOLO v8" format
3. Download and extract

### Annotation Guidelines

#### Bounding Box Rules
- **Tight Fit**: Boxes should tightly enclose the product
- **No Padding**: Avoid excessive whitespace
- **Complete Objects**: Ensure entire product is visible
- **Consistent**: Use consistent annotation style

#### Class Labeling
- **Accurate**: Select the correct product class
- **Consistent**: Use same class for same product
- **Specific**: Use most specific class available

#### Quality Control
- **Review**: Periodically review annotations
- **Consistency**: Ensure consistent annotation style
- **Accuracy**: Verify bounding box accuracy
- **Completeness**: Check for missed products

## Dataset Splits

### Recommended Split Ratios

- **Training**: 80% (primary training data)
- **Validation**: 10% (model tuning)
- **Test**: 10% (final evaluation)

### Split Strategies

#### Random Split
```python
import random
from pathlib import Path
import shutil

def random_split(images_dir, train_ratio=0.8, val_ratio=0.1):
    images = list(Path(images_dir).glob("*.jpg"))
    random.shuffle(images)
    
    n = len(images)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)
    
    train_images = images[:train_end]
    val_images = images[train_end:val_end]
    test_images = images[val_end:]
    
    return train_images, val_images, test_images
```

#### Stratified Split
Ensures balanced class distribution across splits.

#### Temporal Split
Use for time-series data (newer products in test set).

## Data Augmentation

### Built-in Augmentation

The training pipeline includes automatic augmentation:
- HSV color space augmentation
- Geometric transformations
- Mosaic and mixup
- Random erasing

### Custom Augmentation

```python
import albumentations as A

transform = A.Compose([
    A.RandomRotate90(p=0.5),
    A.Flip(p=0.5),
    A.Transpose(p=0.5),
    A.OneOf([
        A.IAAAdditiveGaussianNoise(),
        A.GaussNoise(),
    ], p=0.2),
    A.OneOf([
        A.MotionBlur(p=0.2),
        A.MedianBlur(blur_limit=3, p=0.1),
        A.Blur(blur_limit=3, p=0.1),
    ], p=0.2),
    A.ShiftScaleRotate(shift_limit=0.0625, scale_limit=0.2, rotate_limit=45, p=0.2),
    A.OneOf([
        A.OpticalDistortion(p=0.3),
        A.GridDistortion(p=0.1),
        A.IAAPiecewiseAffine(p=0.3),
    ], p=0.2),
    A.OneOf([
        A.CLAHE(clip_limit=2),
        A.IAASharpen(),
        A.IAAEmboss(),
        A.RandomBrightnessContrast(),
    ], p=0.3),
    A.HueSaturationValue(p=0.3),
])
```

## Dataset Validation

### Validation Tool

```bash
python validate_dataset.py
```

### Validation Checks

- **Image Integrity**: Verify images can be loaded
- **Label Correspondence**: Ensure each image has a label
- **Format Validation**: Check YOLO format compliance
- **Class ID Range**: Verify class IDs are within range
- **Duplicate Detection**: Find duplicate images
- **Orphan Files**: Identify files without pairs

### Common Issues and Fixes

#### Missing Labels
**Issue**: Image exists but no corresponding label
**Fix**: Add label file or remove image

#### Invalid Class ID
**Issue**: Class ID outside valid range
**Fix**: Update label or regenerate data.yaml

#### Corrupted Images
**Issue**: Image cannot be loaded
**Fix**: Re-download or remove image

#### Duplicate Images
**Issue**: Same image appears multiple times
**Fix**: Remove duplicates to prevent overfitting

## Dataset Management

### Version Control

Track dataset versions using the API:

```bash
# Create dataset version
curl -X POST "http://localhost:8000/api/v1/dataset/{dataset_id}/version?version_tag=v1.0"

# List versions
curl "http://localhost:8000/api/v1/dataset/{dataset_id}/versions"
```

### Dataset Statistics

```bash
# Get dataset statistics
curl "http://localhost:8000/api/v1/dataset/{dataset_id}/statistics"
```

### Dataset Upload

```bash
# Upload image
curl -X POST "http://localhost:8000/api/v1/dataset/{dataset_id}/upload/image" \
  -F "file=@image.jpg" \
  -F "product_id=1"
```

## Best Practices

### Data Collection
1. **Diverse Conditions**: Collect images in various conditions
2. **Quality Over Quantity**: Better to have fewer high-quality images
3. **Consistent Annotation**: Maintain annotation standards
4. **Regular Updates**: Continuously add new products

### Annotation Quality
1. **Review Process**: Implement annotation review workflow
2. **Guidelines**: Create clear annotation guidelines
3. **Training**: Train annotators on standards
4. **Quality Metrics**: Track annotation quality metrics

### Dataset Maintenance
1. **Regular Validation**: Run validation checks periodically
2. **Version Control**: Track dataset versions
3. **Backup**: Maintain dataset backups
4. **Documentation**: Document dataset changes

## Troubleshooting

### Common Issues

**Issue: Low detection accuracy**
- Check annotation quality
- Increase dataset size
- Add more variation
- Verify class balance

**Issue: Class imbalance**
- Collect more samples for minority classes
- Use weighted loss
- Apply oversampling

**Issue: Poor generalization**
- Add more diverse images
- Increase augmentation
- Reduce overfitting

## Next Steps

After dataset preparation:
1. Validate dataset thoroughly
2. Start training with small dataset
3. Monitor training metrics
4. Iterate based on results
5. Expand dataset as needed

## Resources

- [LabelImg Documentation](https://github.com/heartexlabs/labelImg)
- [CVAT Documentation](https://opencv.github.io/cvat/)
- [Roboflow Documentation](https://docs.roboflow.com/)
- [YOLO Annotation Guide](https://github.com/ultralytics/ultralytics)
