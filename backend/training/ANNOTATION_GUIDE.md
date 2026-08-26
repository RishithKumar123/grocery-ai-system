# Patanjali Product Dataset Annotation Guide

This guide provides instructions for capturing photos, annotating bounding boxes, and exporting YOLOv11 label files for Patanjali grocery items.

---

## 📷 1. Image Collection Strategy

1. **Target Volume**: 150 – 300 images per Patanjali product class under varied store conditions.
2. **Lighting Variations**: Capture under bright store LED overhead lights, ambient daylight, and low-light shelf corners.
3. **Arrangement & Occlusion**:
   - Single item standalone shots.
   - Dense multi-product shelf layouts.
   - Partial occlusions (packages sitting behind each other).
   - Varied camera angles (0° straight-on, 45° overhead, side profiles).

---

## 🏷️ 2. Class Index Reference (`data.yaml`)

```text
0: Patanjali_Honey
1: Patanjali_Cow_Ghee
2: Patanjali_Dant_Kanti
3: Patanjali_Aloe_Vera_Gel
4: Patanjali_Wheat_Atta
5: Patanjali_Rice
6: Patanjali_Moong_Dal
7: Patanjali_Amla_Murabba
8: Patanjali_Ketchup
9: Patanjali_Mango_Drink
```

---

## 🛠️ 3. Annotation Tools & Export Rules

### Tool Option A: Roboflow (Recommended)
1. Create a project named `Patanjali_Grocery_Detector`.
2. Upload images into `Train` (70%), `Val` (20%), and `Test` (10%) splits.
3. Draw tight bounding boxes around every visible Patanjali product package.
4. Click **Export Dataset** -> Select **YOLOv8 / YOLOv11 Format**.
5. Extract files directly into `backend/training/dataset/`.

### Tool Option B: LabelImg (Offline Desktop)
1. Install: `pip install labelimg`
2. Run: `labelimg`
3. Change save format to **YOLO**.
4. Draw boxes and set class indices according to `data.yaml`.
5. Save `.txt` files directly into `backend/training/dataset/labels/train/` or `val/`.

---

## 🔄 4. Health Audit & Training

Before starting training, run the dataset audit tool to check for unreadable images or corrupt labels:

```powershell
cd "D:\GroceryAI\backend"
venv\Scripts\python training/dataset_checker.py
```

Then launch training on your **NVIDIA GeForce RTX 3050 GPU**:

```powershell
venv\Scripts\python training/train.py
```
