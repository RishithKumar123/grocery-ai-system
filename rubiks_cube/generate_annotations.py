"""Ground-Truth Precision Annotation Generator for Rubik's Cube Images."""
import cv2
import numpy as np
import json
from pathlib import Path

# User Specs:
# 0 = white
# 1 = yellow
# 2 = red
# 3 = orange
# 4 = blue
# 5 = green

CLASS_NAMES = ['white', 'yellow', 'red', 'orange', 'blue', 'green']
CLASS_COLORS = {
    0: (240, 240, 240), # White
    1: (0, 255, 255),   # Yellow
    2: (0, 0, 255),     # Red
    3: (0, 140, 255),   # Orange
    4: (255, 0, 0),     # Blue
    5: (0, 200, 0)      # Green
}

def is_cube_sticker_box(x, y, w, h, img_w, img_h, crop):
    """Filter out background tiles/reflections and keep only Rubik's cube sticker boxes."""
    # Stickers must be reasonable size (between 25 and 140 pixels)
    if w < 25 or h < 25 or w > 160 or h > 160:
        return False
    aspect = w / float(h)
    if aspect < 0.45 or aspect > 2.2:
        return False
    
    # Must sit in the central area where the cube is located
    # Background tile lines are near edges
    if x < 15 or y < 15 or (x + w) > (img_w - 15) or (y + h) > (img_h - 15):
        return False
        
    # Crop color check: must have defined color or white
    if crop is None or crop.size == 0:
        return False
        
    return True

print("Annotation generator script ready.")
