"""
Create sample dataset for training demonstration.
In production, replace with your actual annotated grocery product images.
"""
import shutil
from pathlib import Path
import random

# Create sample images (in production, use your actual product images)
dataset_root = Path(r"D:\GroceryAI\dataset")
train_images = dataset_root / "images" / "train"
train_labels = dataset_root / "labels" / "train"
val_images = dataset_root / "images" / "val"
val_labels = dataset_root / "labels" / "val"

# For demonstration, we'll create placeholder files
# In production, you would:
# 1. Collect actual product images
# 2. Annotate them using tools like LabelImg, CVAT, or Roboflow
# 3. Export annotations in YOLO format (class_id x_center y_center width height)
# 4. Split into train/val/test (typically 80/10/10)

print("Dataset Preparation Instructions:")
print("=" * 60)
print("\n1. Collect product images for each of your 10 Patanjali products:")
print("   - patanjali_amla_murabba")
print("   - patanjali_honey")
print("   - patanjali_cow_ghee")
print("   - patanjali_dant_kanti")
print("   - patanjali_aloe_vera_gel")
print("   - patanjali_wheat_atta")
print("   - patanjali_rice")
print("   - patanjali_moong_dal")
print("   - patanjali_chana_dal")
print("   - patanjali_soap")

print("\n2. Annotate images using YOLO format:")
print("   - Use LabelImg (pip install labelimg)")
print("   - Or use CVAT (open-source annotation tool)")
print("   - Or use Roboflow (web-based)")
print("   - Export annotations as .txt files with format:")
print("     class_id x_center y_center width height")
print("     (all values normalized 0-1)")

print("\n3. Organize files:")
print(f"   - Training images: {train_images}")
print(f"   - Training labels: {train_labels}")
print(f"   - Validation images: {val_images}")
print(f"   - Validation labels: {val_labels}")

print("\n4. Recommended minimum dataset:")
print("   - At least 50-100 images per class for training")
print("   - At least 10-20 images per class for validation")
print("   - Total: 500-1000 training images, 100-200 validation images")

print("\n5. For quick testing, you can start with:")
print("   - 10-20 images per class (100-200 total)")
print("   - 2-5 images per class for validation (20-50 total)")

print("\nCurrent dataset status:")
print(f"  Train images: {len(list(train_images.glob('*')))}")
print(f"  Train labels: {len(list(train_labels.glob('*.txt')))}")
print(f"  Val images: {len(list(val_images.glob('*')))}")
print(f"  Val labels: {len(list(val_labels.glob('*.txt')))}")

print("\n" + "=" * 60)
print("Once you have prepared your dataset, run training with:")
print("  python train_model.py")
