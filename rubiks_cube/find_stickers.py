"""Find and annotate every visible Rubik's Cube sticker in the 4 unique images."""
import cv2
import numpy as np
from pathlib import Path

# User Specs:
# 0 = white, 1 = yellow, 2 = red, 3 = orange, 4 = blue, 5 = green
CLASS_NAMES = ['white', 'yellow', 'red', 'orange', 'blue', 'green']
CLASS_COLORS = {
    0: (240, 240, 240), # White
    1: (0, 255, 255),   # Yellow
    2: (0, 0, 255),     # Red
    3: (0, 140, 255),   # Orange
    4: (255, 0, 0),     # Blue
    5: (0, 200, 0)      # Green
}

def classify_sticker(crop_bgr):
    """Classify crop into 0:white, 1:yellow, 2:red, 3:orange, 4:blue, 5:green."""
    if crop_bgr is None or crop_bgr.size == 0:
        return 0
        
    hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
    h_med = np.median(hsv[:, :, 0])
    s_med = np.median(hsv[:, :, 1])
    v_med = np.median(hsv[:, :, 2])
    
    b_med = np.median(crop_bgr[:, :, 0])
    g_med = np.median(crop_bgr[:, :, 1])
    r_med = np.median(crop_bgr[:, :, 2])
    
    # White sticker check: Low saturation (< 55) and high value/brightness (> 130)
    if s_med < 55 and v_med > 130 and max(abs(r_med - g_med), abs(g_med - b_med), abs(r_med - b_med)) < 30:
        return 0 # white
        
    # Blue check: Hue around 90-135
    if 85 <= h_med <= 135 and s_med > 50:
        return 4 # blue
        
    # Green check: Hue around 35-85
    if 35 <= h_med <= 85 and s_med > 40:
        return 5 # green
        
    # Yellow check: Hue around 15-35, high saturation & brightness
    if 14 <= h_med <= 34 and s_med > 70:
        return 1 # yellow

    # Orange vs Red check
    if h_med < 14 or h_med > 165:
        if g_med > 55 and (r_med - g_med) < 85 and h_med >= 6:
            return 3 # orange
        else:
            return 2 # red
            
    # Fallback heuristic based on dominant color channel
    if b_med > r_med and b_med > g_med:
        return 4 # blue
    if g_med > r_med and g_med > b_med:
        return 5 # green
    if r_med > g_med:
        return 1 if g_med > 150 else (3 if g_med > 70 else 2)
        
    return 0

def detect_cube_stickers(img_bgr):
    """Detect sticker bounding boxes on Rubik's cube."""
    h, w, _ = img_bgr.shape
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # Use Canny edges + adaptive threshold to locate sticker squares
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    candidates = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        # Sticker size range: between 150 and 8000 pixels
        if 120 < area < 9000:
            x, y, bw, bh = cv2.boundingRect(cnt)
            aspect = bw / float(bh)
            if 0.5 < aspect < 2.0:
                # Margin inset to avoid black/white borders when sampling color
                margin = int(min(bw, bh) * 0.2)
                crop = img_bgr[y+margin:y+bh-margin, x+margin:x+bw-margin]
                if crop.size > 0:
                    cls_id = classify_sticker(crop)
                    candidates.append((x, y, bw, bh, area, cls_id))
                    
    # Non-maximum suppression / deduplication of overlapping boxes
    boxes = []
    candidates.sort(key=lambda item: item[4], reverse=True) # Sort by area descending
    
    for c in candidates:
        x1, y1, w1, h1, a1, cls1 = c
        overlap = False
        for b in boxes:
            x2, y2, w2, h2, a2, cls2 = b
            # Compute IoU
            xx1 = max(x1, x2)
            yy1 = max(y1, y2)
            xx2 = min(x1 + w1, x2 + w2)
            yy2 = min(y1 + h1, y2 + h2)
            inter = max(0, xx2 - xx1) * max(0, yy2 - yy1)
            iou = inter / float(a1 + a2 - inter)
            if iou > 0.35:
                overlap = True
                break
        if not overlap:
            boxes.append(c)
            
    return boxes

if __name__ == "__main__":
    print("Sticker detector ready.")
