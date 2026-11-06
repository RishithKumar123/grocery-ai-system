"""Automated Precision Annotation Tool for Rubik's Cube Colored Stickers."""
import cv2
import numpy as np
from pathlib import Path

# Color mapping in HSV range
COLOR_RANGES = {
    "yellow": [
        (np.array([18, 80, 100]), np.array([35, 255, 255]))
    ],
    "orange": [
        (np.array([8, 120, 120]), np.array([17, 255, 255])),
        (np.array([0, 140, 120]), np.array([7, 255, 255]))
    ],
    "red": [
        (np.array([170, 100, 100]), np.array([180, 255, 255])),
        (np.array([0, 160, 100]), np.array([6, 255, 255]))
    ],
    "green": [
        (np.array([36, 60, 50]), np.array([85, 255, 255]))
    ],
    "blue": [
        (np.array([90, 70, 50]), np.array([130, 255, 255]))
    ],
    "white": [
        (np.array([0, 0, 160]), np.array([180, 50, 255]))
    ]
}

CLASS_IDS = {
    "white": 0,
    "yellow": 1,
    "red": 2,
    "orange": 3,
    "blue": 4,
    "green": 5
}

CLASS_COLORS_BGR = {
    "white": (255, 255, 255),
    "yellow": (0, 255, 255),
    "red": (0, 0, 255),
    "orange": (0, 165, 255),
    "blue": (255, 0, 0),
    "green": (0, 255, 0)
}

def detect_stickers(img_path):
    img = cv2.imread(str(img_path))
    h, w, c = img.shape
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Also create a gray mask to isolate the cube area from background tile
    # The Rubik's cube has a white plastic body and distinct colored stickers.
    
    detections = []
    
    # Find all square-ish contours on the image
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    contours, _ = cv2.findContours(thresh, cv2.RETRATION_LIST if hasattr(cv2, 'RETRATION_LIST') else cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    valid_boxes = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        # Stickers are roughly 100 to 10000 pixels depending on distance/angle
        if 80 < area < 15000:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
            x, y, bw, bh = cv2.boundingRect(cnt)
            aspect_ratio = bw / float(bh)
            if 0.5 < aspect_ratio < 2.0:
                valid_boxes.append((x, y, bw, bh, area))

    return img, valid_boxes

if __name__ == "__main__":
    print("Testing auto annotation script...")
