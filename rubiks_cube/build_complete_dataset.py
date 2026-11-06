"""Complete Rubik's Cube Sticker YOLO Dataset Builder & Visualizer."""
import cv2
import numpy as np
import yaml
import shutil
from pathlib import Path

# User Specs:
# 0 = white, 1 = yellow, 2 = red, 3 = orange, 4 = blue, 5 = green
CLASS_NAMES = ['white', 'yellow', 'red', 'orange', 'blue', 'green']
CLASS_COLORS = {
    0: (255, 255, 255), # White
    1: (0, 255, 255),   # Yellow
    2: (0, 0, 255),     # Red
    3: (0, 140, 255),   # Orange
    4: (255, 0, 0),     # Blue
    5: (0, 200, 0)      # Green
}

def classify_sticker_crop(crop):
    """Classify sticker crop into 0..5 using HSV & RGB metrics."""
    if crop is None or crop.size == 0:
        return 0
        
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    h_med = np.median(hsv[:, :, 0])
    s_med = np.median(hsv[:, :, 1])
    v_med = np.median(hsv[:, :, 2])
    
    b_med = np.median(crop[:, :, 0])
    g_med = np.median(crop[:, :, 1])
    r_med = np.median(crop[:, :, 2])
    
    # White check: Low saturation (< 50) and high brightness (v > 130)
    if s_med < 55 and v_med > 130:
        diff = max(abs(r_med - g_med), abs(g_med - b_med), abs(r_med - b_med))
        if diff < 35:
            return 0 # white
            
    # Blue check
    if 85 <= h_med <= 135 and s_med > 45:
        return 4 # blue
        
    # Green check
    if 35 <= h_med <= 85 and s_med > 40:
        return 5 # green
        
    # Yellow check
    if 14 <= h_med <= 34 and s_med > 65:
        return 1 # yellow

    # Orange vs Red check
    if h_med < 14 or h_med > 165:
        if g_med > 50 and (r_med - g_med) < 85 and h_med >= 6:
            return 3 # orange
        else:
            return 2 # red
            
    if r_med > g_med and r_med > b_med:
        return 1 if g_med > 150 else (3 if g_med > 65 else 2)
        
    return 0

def extract_cube_stickers(img_bgr):
    """Extract sticker bounding boxes filtered specifically to the Rubik's cube area."""
    h_img, w_img, _ = img_bgr.shape
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    candidates = []
    
    # Adaptive thresholding to find square boundaries
    for block_size in [11, 15, 21]:
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, block_size, 2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 150 < area < 9000:
                x, y, bw, bh = cv2.boundingRect(cnt)
                aspect = bw / float(bh)
                # Sticker aspect ratio constraint
                if 0.5 < aspect < 2.0:
                    # Ignore full frame or extreme border boxes
                    if bw > w_img * 0.4 or bh > h_img * 0.4:
                        continue
                    if x < 10 or y < 10 or (x + bw) > (w_img - 10) or (y + bh) > (h_img - 10):
                        continue
                    candidates.append((x, y, bw, bh, area))
                    
    # Non-maximum suppression by IoU
    candidates.sort(key=lambda item: item[4], reverse=True)
    dedup = []
    for c in candidates:
        x1, y1, w1, h1, a1 = c
        overlap = False
        for b in dedup:
            x2, y2, w2, h2, a2 = b
            xx1 = max(x1, x2)
            yy1 = max(y1, y2)
            xx2 = min(x1 + w1, x2 + w2)
            yy2 = min(y1 + h1, y2 + h2)
            inter = max(0, xx2 - xx1) * max(0, yy2 - yy1)
            iou = inter / float(a1 + a2 - inter)
            if iou > 0.30:
                overlap = True
                break
        if not overlap:
            dedup.append(c)

    # Classify each sticker box
    results = []
    for x, y, bw, bh, area in dedup:
        mx = max(2, int(bw * 0.2))
        my = max(2, int(bh * 0.2))
        crop = img_bgr[y+my:y+bh-my, x+mx:x+bw-mx]
        cls_id = classify_sticker_crop(crop)
        results.append((x, y, bw, bh, cls_id))
        
    return results

def create_yolo_dataset():
    user_uploaded_dir = Path(r'C:\Users\RISHITH KUMAR M\.gemini\antigravity\brain\6d398e4c-4322-4b48-8763-d28929d96af4\.user_uploaded')
    all_images = sorted(list(user_uploaded_dir.glob('media_1788333328*.jpg')))
    
    # 4 unique images (media_1788333328754 and 755 are identical)
    unique_images = [all_images[0], all_images[2], all_images[3], all_images[4]]
    
    dataset_dir = Path(r'D:\GroceryAI\rubiks_cube\dataset')
    if dataset_dir.exists():
        shutil.rmtree(dataset_dir)
        
    train_img_dir = dataset_dir / 'images' / 'train'
    val_img_dir = dataset_dir / 'images' / 'val'
    train_lbl_dir = dataset_dir / 'labels' / 'train'
    val_lbl_dir = dataset_dir / 'labels' / 'val'
    previews_dir = Path(r'D:\GroceryAI\rubiks_cube\previews')
    
    train_img_dir.mkdir(parents=True, exist_ok=True)
    val_img_dir.mkdir(parents=True, exist_ok=True)
    train_lbl_dir.mkdir(parents=True, exist_ok=True)
    val_lbl_dir.mkdir(parents=True, exist_ok=True)
    previews_dir.mkdir(parents=True, exist_ok=True)
    
    # 80% train / 20% val split:
    # First 3 images for train, 4th image for val
    train_set = unique_images[:3]
    val_set = unique_images[3:]
    
    stats = {"train_boxes": 0, "val_boxes": 0, "class_counts": {i: 0 for i in range(6)}}
    
    for set_type, img_list in [('train', train_set), ('val', val_set)]:
        target_img_dir = train_img_dir if set_type == 'train' else val_img_dir
        target_lbl_dir = train_lbl_dir if set_type == 'train' else val_lbl_dir
        
        for idx, img_path in enumerate(img_list):
            img_name = f"rubik_{set_type}_{idx+1}.jpg"
            lbl_name = f"rubik_{set_type}_{idx+1}.txt"
            
            img = cv2.imread(str(img_path))
            h_img, w_img, _ = img.shape
            
            # Copy image to dataset folder
            cv2.imwrite(str(target_img_dir / img_name), img)
            
            boxes = extract_cube_stickers(img)
            
            # Draw preview image
            preview_img = img.copy()
            yolo_lines = []
            
            for b in boxes:
                x, y, bw, bh, cls_id = b
                
                # YOLO normalized coordinates: class_id x_center y_center width height
                xc = (x + bw / 2.0) / w_img
                yc = (y + bh / 2.0) / h_img
                w_norm = bw / float(w_img)
                h_norm = bh / float(h_img)
                
                yolo_lines.append(f"{cls_id} {xc:.6f} {yc:.6f} {w_norm:.6f} {h_norm:.6f}")
                
                stats["class_counts"][cls_id] += 1
                if set_type == 'train':
                    stats["train_boxes"] += 1
                else:
                    stats["val_boxes"] += 1
                    
                # Draw bounding box and label on preview image
                color = CLASS_COLORS[cls_id]
                cv2.rectangle(preview_img, (x, y), (x + bw, y + bh), color, 2)
                label = f"{cls_id}:{CLASS_NAMES[cls_id]}"
                cv2.putText(preview_img, label, (x, max(15, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
            # Write label file
            (target_lbl_dir / lbl_name).write_text("\n".join(yolo_lines), encoding="utf-8")
            
            # Write preview image
            cv2.imwrite(str(previews_dir / f"preview_{set_type}_{idx+1}.jpg"), preview_img)
            print(f"[{set_type.upper()}] Processed {img_name}: {len(boxes)} sticker annotations.")

    # Create data.yaml
    data_yaml_content = {
        'path': str(dataset_dir),
        'train': 'images/train',
        'val': 'images/val',
        'nc': len(CLASS_NAMES),
        'names': CLASS_NAMES
    }
    
    with open(dataset_dir / 'data.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(data_yaml_content, f, default_flow_style=False)
        
    print("\n=========================================================")
    print("RUBIK'S CUBE DATASET CREATION SUMMARY")
    print("=========================================================")
    print(f"Dataset Root Dir : {dataset_dir}")
    print(f"Train Bounding Boxes : {stats['train_boxes']}")
    print(f"Val Bounding Boxes   : {stats['val_boxes']}")
    print(f"Total Bounding Boxes : {stats['train_boxes'] + stats['val_boxes']}")
    print("Per-Class Distribution:")
    for cid, cname in enumerate(CLASS_NAMES):
        print(f"  • Class {cid} ({cname}): {stats['class_counts'][cid]} stickers")
    print("=========================================================")

if __name__ == "__main__":
    create_yolo_dataset()
