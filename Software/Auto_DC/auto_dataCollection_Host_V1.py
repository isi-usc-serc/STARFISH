""" 
PC: Data Collection Automation Script
This script will listen for timestamp data from the raspberry pi
and match it to the position data timestamps, and publish the data to 
a CSV file.

"""


# Import libraries
import cv2 # dir: C:\Users\space_lab\source\repos\openCV
import time
import datetime
import csv
import os
import socket
import json



################################## CONFIGURATION ##############################
CAMERA_IDS = [0, 1, 2, 3, 4]  # Update camera indexes as needed

# Data logging directory: C:\Users\space_lab\Desktop\STARFISH Test Data\Thermo_Position_Data
LOG_DIR = "data_logs"
FRAME_DIR = os.path.join(LOG_DIR, "frames")
CSV_PATH = os.path.join(LOG_DIR, "data_log.csv")

LISTEN_IP = "0.0.0.0"    # Raspberry Pi IP
LISTEN_PORT = 5005       # Define / Update port

##################################### SETUP ###################################
os.makedirs(FRAME_DIR, exist_ok=True)

# Initialize cameras
cams = []
for cam_id in CAMERA_IDS:
    cam = cv2.VideoCapture(cam_id)
    if not cam.isOpened():
        print(f"[ERROR] Camera {cam_id} failed to open.")
    cams.append(cam)

# Initialize CSV logging
with open(CSV_PATH, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Temperature_C", "SMA_Active"] +
                    [f"Cam{i}_Frame" for i in range(len(CAMERA_IDS))])

# Setup TCP socket server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((LISTEN_IP, LISTEN_PORT))
server.listen(1)
print(f"[INFO] Listening for Raspberry Pi on {LISTEN_IP}:{LISTEN_PORT}")
conn, addr = server.accept()
print(f"[INFO] Connected to Raspberry Pi at {addr}")

############################# Timestamp Matching ##############################
def capture_frames(timestamp_iso):
    """Capture and save frames from all cameras."""
    frame_paths = []
    for i, cam in enumerate(cams):
        ret, frame = cam.read()
        if ret:
            fname = f"{timestamp_iso.replace(':','-')}_cam{i}.jpg"
            fpath = os.path.join(FRAME_DIR, fname)
            cv2.imwrite(fpath, frame)
            frame_paths.append(fpath)
        else:
            frame_paths.append("ERROR")
    return frame_paths

def recv_temp_packet():
    """Receive a JSON temperature packet from Raspberry Pi."""
    data = conn.recv(1024).decode()
    try:
        pkt = json.loads(data)
        return pkt["timestamp"], pkt["temperature_C"], pkt["sma_active"]
    except Exception as e:
        print(f"[ERROR] Failed to decode packet: {e}")
        return None, None, None

################################### MAIN LOOP #################################
try:
    while True:
        timestamp, temperature, sma_active = recv_temp_packet()
        if not timestamp:
            continue  # skip on bad packet

        print(f"[INFO] Temp packet received: {timestamp}, {temperature} C")

        frame_paths = capture_frames(timestamp)

        with open(CSV_PATH, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, temperature, sma_active] + frame_paths)

finally:
    for cam in cams:
        cam.release()
    cv2.destroyAllWindows()
    conn.close()
    server.close()
