# -*- coding: utf-8 -*-
"""
This script will scan the computer and find each active camera, and return the 
index and ID.

Created on Wed Jun 11 17:33:49 2025

@author: space_lab
"""

import cv2

MAX_CAMERAS = 10

print("Scanning for connected cameras...")
for i in range(MAX_CAMERAS):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"[FOUND] Camera found at index {i}")
        cap.release()
    else:
        print(f"[    ] No camera at index {i}")
