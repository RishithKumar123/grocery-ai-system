# Enterprise FMCG Grocery Dataset & Expansion Guide (300 to 1000+ SKUs)

This guide provides an architectural blueprint for building, annotating, validating, retraining, and scaling a production-grade FMCG grocery dataset using **YOLOv11**.

---

## 🏬 1. Supported Brands Registry (105 Pre-Registered Classes)

The dataset suite comes pre-configured with 105 FMCG product SKUs across 26 top brands:
* **Dairy & Staples**: Amul, Patanjali, Aashirvaad, Fortune, Saffola, Tata Sampann
* **Biscuits & Snacks**: Britannia, Parle, Sunfeast, Cadbury, Haldiram, Lays
* **Instant Foods**: Nestlé Maggi, Sunfeast Yippee, Quaker, Kellogg's
* **Personal Care & Hygiene**: Colgate, Dettol, Himalaya, Dabur
* **Health Drinks & Beverages**: Horlicks, Boost, Bournvita, Coca-Cola, Pepsi, Sprite, Thums Up, Maaza, Frooti, Real Juice
* **Condiments & House Care**: Kissan, Vim, Surf Excel, Ariel, Harpic, Lizol, MDH, Everest, Catch

---

## 🛠️ 2. Step-by-Step Dataset Curation & Validation Workflow

### Step A: Collect Images
* **Target per SKU**: 50–150 images per product class.
* **Variations**: Different lighting conditions, shelf angles, partial occlusions, stacked items, and multi-product arrangements.

### Step B: Run Automated Dataset Validation Suite
Run the build-in diagnostic utilities to ensure label syntax and image integrity:

```powershell
cd "D:\GroceryAI\backend"

# 1. Check Image and Label Counts
venv\Scripts\python training/dataset_statistics.py

# 2. Validate Label Syntax & Coordinates Bounds [0, 1]
venv\Scripts\python training/dataset_validator.py

# 3. Detect Duplicate Images via MD5 Hash Comparison
venv\Scripts\python training/duplicate_image_detector.py

# 4. Find Unannotated Images or Orphan Label Files
venv\Scripts\python training/missing_label_checker.py

# 5. Check Class Instance Frequency Distribution
venv\Scripts\python training/class_distribution.py
```

---

## 🔄 3. Synchronize Database & Train

### Step C: Synchronize Database Catalog
Synchronize your SQL database table `ProductModel.yolo_class_mapping` with `training/data.yaml` class IDs:

```powershell
venv\Scripts\python sync_catalog_mapping.py
```

### Step D: Train YOLOv11 on RTX 3050 GPU
Launch model training:

```powershell
venv\Scripts\python training/train.py
```

Training parameters:
- `model`: `yolo11m.pt`
- `epochs`: `100`
- `imgsz`: `640`
- `batch`: `8`
- `device`: `0` (RTX 3050)
- `workers`: `8`
- `cache`: `True`
- `amp`: `True` (Mixed Precision)

Upon training completion, `train.py` automatically copies `best.pt` to `backend/models/best.pt`.

---

## 🚀 4. Scaling from 300 to 1000+ SKUs

To expand the dataset to 1000+ products:

1. **Class ID Registration**: Append new class entries to `training/data.yaml`:
   ```yaml
   105: BrandX_ProductY
   106: BrandZ_ProductW
   ```
2. **Database Sync**: Re-run `python sync_catalog_mapping.py` to auto-register new products in SQL database.
3. **Incremental Pretrained Training**: Pass the previous `best.pt` checkpoint to `train.py` as fine-tuning base to accelerate convergence:
   ```python
   model = YOLO("models/best.pt")
   ```
4. **ONNX Export for Edge Deployment**:
   ```powershell
   venv\Scripts\python training/export.py onnx
   ```
