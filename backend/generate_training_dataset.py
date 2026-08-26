import os
import cv2
import numpy as np
import random
from pathlib import Path

# Target directory setup
dataset_root = Path(r"D:\GroceryAI\dataset")
train_img_dir = dataset_root / "images" / "train"
train_lbl_dir = dataset_root / "labels" / "train"
val_img_dir = dataset_root / "images" / "val"
val_lbl_dir = dataset_root / "labels" / "val"
test_img_dir = dataset_root / "images" / "test"
test_lbl_dir = dataset_root / "labels" / "test"

for d in [train_img_dir, train_lbl_dir, val_img_dir, val_lbl_dir, test_img_dir, test_lbl_dir]:
    d.mkdir(parents=True, exist_ok=True)

class_names = [
    "patanjali_amla_murabba",
    "patanjali_honey",
    "patanjali_cow_ghee",
    "patanjali_dant_kanti",
    "patanjali_aloe_vera_gel",
    "patanjali_wheat_atta",
    "patanjali_rice",
    "patanjali_moong_dal",
    "patanjali_chana_dal",
    "patanjali_soap"
]

color_palette = [
    (50, 180, 50),   # Green
    (0, 165, 255),   # Orange (Honey)
    (255, 220, 100), # Gold (Ghee)
    (200, 50, 50),   # Red/Blue (Dant Kanti)
    (100, 220, 100), # Light Green
    (220, 200, 180), # Wheat
    (240, 240, 240), # Rice
    (0, 215, 255),   # Moong (Yellow)
    (50, 140, 220),  # Chana (Brown/Orange)
    (220, 150, 220)  # Soap
]

def generate_sample_image(img_idx: int, target_dir_img: Path, target_dir_lbl: Path):
    width, height = 640, 640
    # Background texture (shelf simulation)
    bg_color = (random.randint(20, 50), random.randint(20, 50), random.randint(20, 50))
    img = np.full((height, width, 3), bg_color, dtype=np.uint8)
    
    # Add horizontal shelf lines
    cv2.line(img, (0, 200), (640, 200), (80, 80, 80), 3)
    cv2.line(img, (0, 440), (640, 440), (80, 80, 80), 3)
    
    num_objects = random.randint(1, 3)
    labels = []
    
    for _ in range(num_objects):
        class_id = random.randint(0, 9)
        color = color_palette[class_id]
        
        # Bounding box dimensions
        w_box = random.randint(80, 160)
        h_box = random.randint(100, 200)
        x_min = random.randint(20, width - w_box - 20)
        y_min = random.randint(20, height - h_box - 20)
        x_max = x_min + w_box
        y_max = y_min + h_box
        
        # Draw container box on synthetic image
        cv2.rectangle(img, (x_min, y_min), (x_max, y_max), color, -1)
        cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (255, 255, 255), 2)
        
        # Overlay product title text
        cv2.putText(img, class_names[class_id][:10], (x_min + 5, y_min + 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        
        # Convert to YOLO normalized format: class_id x_center y_center w h
        x_center = (x_min + x_max) / (2.0 * width)
        y_center = (y_min + y_max) / (2.0 * height)
        norm_w = w_box / width
        norm_h = h_box / height
        
        labels.append(f"{class_id} {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}")
        
    img_name = f"sample_{img_idx:04d}.jpg"
    lbl_name = f"sample_{img_idx:04d}.txt"
    
    cv2.imwrite(str(target_dir_img / img_name), img)
    with open(target_dir_lbl / lbl_name, "w", encoding="utf-8") as f:
        f.write("\n".join(labels))

# Generate 40 Train images, 10 Val images, 5 Test images
for i in range(1, 41):
    generate_sample_image(i, train_img_dir, train_lbl_dir)

for i in range(41, 51):
    generate_sample_image(i, val_img_dir, val_lbl_dir)

for i in range(51, 56):
    generate_sample_image(i, test_img_dir, test_lbl_dir)

print(f"Generated 40 training, 10 validation, and 5 testing images with YOLO labels!")
