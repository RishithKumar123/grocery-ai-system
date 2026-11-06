"""Precision Annotation and Dataset Creator for Rubik's Cube Stickers."""
import os
import cv2
import numpy as np
import yaml
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

def analyze_crop_color(crop_bgr):
    """Determine class of sticker from BGR crop using HSV & RGB color metrics."""
    if crop_bgr is None or crop_bgr.size == 0:
        return None
    
    # Calculate median BGR and HSV
    hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
    h_med = np.median(hsv[:, :, 0])
    s_med = np.median(hsv[:, :, 1])
    v_med = np.median(hsv[:, :, 2])
    
    b_med = np.median(crop_bgr[:, :, 0])
    g_med = np.median(crop_bgr[:, :, 1])
    r_med = np.median(crop_bgr[:, :, 2])
    
    # White check: Low saturation, high value/brightness
    if s_med < 45 and v_med > 140:
        return 0 # white
    
    # Yellow check: Hue around 18-35, high saturation & value
    if 15 <= h_med <= 38 and s_med > 80:
        return 1 # yellow
        
    # Blue check: Hue around 90-130
    if 85 <= h_med <= 135 and s_med > 60:
        return 4 # blue
        
    # Green check: Hue around 36-84
    if 36 <= h_med <= 84 and s_med > 50:
        return 5 # green
        
    # Orange vs Red check
    if h_med < 15 or h_med > 165:
        # Orange has higher Green component than Red
        if g_med > 60 and (r_med - g_med) < 80 and h_med >= 7:
            return 3 # orange
        else:
            return 2 # red

    # Fallback heuristic
    if r_med > g_med and r_med > b_med:
        return 3 if g_med > 80 else 2
    
    return 0

print("Module loaded.")
