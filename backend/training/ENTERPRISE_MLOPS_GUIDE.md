# Enterprise FMCG YOLOv11 MLOps & Deployment Guide

This document defines the complete automated MLOps workflow for training, validating, testing, versioning, and deploying custom YOLOv11 models on an **NVIDIA RTX 3050 GPU**.

---

## 🛠️ Windows CLI Commands

All commands must be executed from the `backend` directory using the Python virtual environment:

```powershell
cd "D:\GroceryAI\backend"
```

### 1. Step 1: Validate Dataset Quality & Syntax
Check image/label pairing, bounding box normalization (0-1), corrupt files, MD5 duplicates, and class imbalance:
```powershell
venv\Scripts\python training/dataset_validator.py
```
> Outputs: `dataset_report.json` and terminal quality report.

---

### 2. Step 2: Train Model on NVIDIA RTX 3050 GPU
Train YOLOv11 on CUDA (`device=0`, `amp=True`) with dynamic VRAM batch sizing:
```powershell
venv\Scripts\python training/train.py
```
> Training outputs are saved under `runs/detect/grocery_candidate_run/weights/best.pt` and copied to `models/candidates/candidate_best.pt`.

---

### 3. Step 3: Validate Candidate Model Metrics
Calculate precision, recall, mAP50, mAP50-95, per-class performance, and confusion matrix:
```powershell
venv\Scripts\python training/validate.py
```

---

### 4. Step 4: Run Inference Test on Sample Image or Video
Test predictions on single images, multi-product shelf snapshots, or video streams:
```powershell
venv\Scripts\python training/predict.py training/sample_test.jpg
```
> Saves annotated bounding box visual overlay to `runs/predict_results/`.

---

### 5. Step 5: Deploy Model to Production
Promote validated candidate model to production with automatic timestamped backup:
```powershell
venv\Scripts\python training/deploy.py
```
> Copies candidate model to `models/production/production_best.pt` and `models/best.pt`.

---

## 📁 Model Versioning & Folder Architecture

```text
backend/models/
├── production/
│   └── production_best.pt     <-- Active Production Weights
├── candidates/
│   └── candidate_best.pt        <-- Candidate Model Under Validation
├── backups/
│   └── backup_production_*.pt   <-- Timestamped Historical Backups
└── best.pt                      <-- Application Runtime Target
```

---

## 🏷️ Annotation Standard (YOLO Format)

Label text files must reside in `backend/training/dataset/labels/{train,val,test}/<image_name>.txt`.
Each line must follow the normalized YOLO coordinate standard:

$$\text{class\_id} \quad x_{\text{center}} \quad y_{\text{center}} \quad \text{width} \quad \text{height}$$

Where coordinates are float values normalized between $0.0$ and $1.0$:
- $x_{\text{center}} = \frac{\text{box\_x\_center}}{\text{image\_width}}$
- $y_{\text{center}} = \frac{\text{box\_y\_center}}{\text{image\_height}}$
- $\text{width} = \frac{\text{box\_width}}{\text{image\_width}}$
- $\text{height} = \frac{\text{box\_height}}{\text{image\_height}}$
