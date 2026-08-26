# Patanjali Product Detection System (YOLOv11)

This folder contains the complete dataset curation, audit, training, validation, and deployment pipeline for the **Patanjali Product Detection System**.

---

## 📁 Directory Layout

```text
backend/training/
├── data.yaml           <-- Patanjali 16 Class YAML Config
├── train.py            <-- RTX 3050 Training & Deployment Runner
├── predict.py          <-- Image Inference & Crop Overlay Script
├── validate.py         <-- mAP50 / mAP50-95 Metrics Evaluator
├── dataset_checker.py  <-- Dataset Health & Audit Manager
└── dataset/
    ├── images/
    │   ├── train/      <-- Place training images here
    │   ├── val/        <-- Place validation images here
    │   └── test/       <-- Place test images here
    └── labels/
        ├── train/      <-- Place YOLO format labels (.txt) here
        ├── val/        <-- Place validation labels (.txt) here
        └── test/       <-- Place test labels (.txt) here
```

---

## 🏷️ 16 Patanjali Catalog Classes (`data.yaml`)

```yaml
names:
  0: Patanjali_Honey
  1: Patanjali_Amla_Murabba
  2: Patanjali_Cow_Ghee
  3: Patanjali_Dant_Kanti
  4: Patanjali_Aloe_Vera_Gel
  5: Patanjali_Wheat_Atta
  6: Patanjali_Rice
  7: Patanjali_Moong_Dal
  8: Patanjali_Chana_Dal
  9: Patanjali_Ketchup
  10: Patanjali_Mango_Drink
  11: Patanjali_Mustard_Oil
  12: Patanjali_Corn_Flakes
  13: Patanjali_Besan
  14: Patanjali_Oats
  15: Patanjali_Biscuit
```

---

## 🛠️ Step-by-Step Workflow

### 1. Collect & Annotate Images
1. Capture photos of Patanjali product packages under varied lighting, angles, and shelf arrangements.
2. Annotate bounding boxes using **Roboflow** or **LabelImg** (Select YOLO output format).
3. Export files into:
   - `training/dataset/images/train/`
   - `training/dataset/labels/train/`
   - `training/dataset/images/val/`
   - `training/dataset/labels/val/`

### 2. Verify Dataset Health
Run the automated dataset audit manager to check for missing labels, corrupt images, duplicates, or class imbalances:

```powershell
cd "D:\GroceryAI\backend"
venv\Scripts\python training/dataset_checker.py
```

### 3. Start RTX 3050 Training
Launch model training pre-configured for your **NVIDIA GeForce RTX 3050 GPU**:

```powershell
venv\Scripts\python training/train.py
```

Training configuration:
* `model`: `yolo11m.pt`
* `epochs`: `100`
* `imgsz`: `640`
* `batch`: `8`
* `workers`: `8`
* `device`: `0` (RTX 3050)
* `amp`: `True` (Mixed Precision)

### 4. Automatic Deployment
Upon training completion, `train.py` automatically copies the best trained weights to:
`backend/models/best.pt`

The production system (`YoloV11InferenceEngine`) will immediately load `backend/models/best.pt` on server startup!

---

## 📈 Evaluate Metrics & Inspect Predictions

* **Validation Metrics**:
  ```powershell
  venv\Scripts\python training/validate.py
  ```
* **Run Image Prediction & Visual Bounding Box Overlay**:
  ```powershell
  venv\Scripts\python training/predict.py kirana.jpg
  ```

---

## ➕ Adding New Patanjali Products Later

To add a new product (e.g. `16: Patanjali_Chyawanprash`):
1. Open `training/data.yaml` and append `16: Patanjali_Chyawanprash`.
2. Add annotated images for class ID `16`.
3. Re-run `python training/train.py`.
4. The engine automatically deploys `best.pt` without breaking existing database schemas or frontend routes!
