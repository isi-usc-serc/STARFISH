""" 
(PC) Host Program: Automated Data Collection
This script will listen for timestamp data from the raspberry pi
and match it to the position data timestamps, and publish the data to 
a CSV file.

Note: Run this 'listener' program before starting the client program.

Created on Wed Jun 11 17:33:49 2025
@author: space_lab

"""

# === Import libraries ===
import cv2
import csv
import os
import socket
import json
import time
from datetime import datetime, timedelta
from collections import deque


################################## CONFIGURATION ##############################
# Set data logging directory
LOG_DIR = r"C:\Users\space_lab\Desktop\STARFISH Test Data\Thermo_Position_Data"
FRAME_DIR = os.path.join(LOG_DIR, "frames")

# Set port and IP info (currently listening for any connecting ip)
LISTEN_IP = "0.0.0.0"  # listens on all its network interfaces
LISTEN_PORT = 5005

# Define camera IDs in use
CAMERA_IDS = [0, 1, 2, 3, 4]  # 0: top for X/Y, 1-4: for Z

# Alignment tolerance in milliseconds
ALIGNMENT_WINDOW_MS = 50

# Thermocouple configuration for the Pi
TC_CHANNELS = [0, 1, 2, 3]
TC_TYPE = "J"  # Thermocouple type: J, K, etc.
PULSE_DURATION = 1.0     # seconds
SEND_INTERVAL = 0.25     # seconds between temperature samples

# Set number of samples to collect, and interval between pulses
NUM_RUNS = 5
INTER_RUN_DELAY = 20  # Interval time between pulses in seconds




#################################### SETUP ####################################
os.makedirs(FRAME_DIR, exist_ok=True)

cams = []
print("[INFO] Initializing cameras...")
for cam_id in CAMERA_IDS:
    cam = cv2.VideoCapture(cam_id)
    if cam.isOpened():
        print(f"[INFO] Camera {cam_id} opened successfully")
    else:
        print(f"[ERROR] Camera {cam_id} failed to open")
    cams.append(cam)

def get_csv_path(run_index):
    return os.path.join(LOG_DIR, f"data_log_run_{run_index + 1}.csv")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((LISTEN_IP, LISTEN_PORT))
server.listen(1)
print(f"[INFO] Listening for Raspberry Pi on {LISTEN_IP}:{LISTEN_PORT}")
conn, addr = server.accept()
print(f"[INFO] Connected to Raspberry Pi at {addr}")

# Send configuration to Pi
config_packet = {
    "pulse_duration": PULSE_DURATION,
    "send_interval": SEND_INTERVAL,
    "channels": TC_CHANNELS,
    "tc_type": TC_TYPE
}
conn.sendall(json.dumps(config_packet).encode())




############################# CAMERA PROCESSING ###############################
def detect_position(frame):
    """Basic red ball detection to extract (x, y) or z position."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_red = (0, 100, 100)
    upper_red = (10, 255, 255)
    mask = cv2.inRange(hsv, lower_red, upper_red)
    moments = cv2.moments(mask)
    if moments["m00"] != 0:
        cx = int(moments["m10"] / moments["m00"])
        cy = int(moments["m01"] / moments["m00"])
        return cx, cy
    return None, None

def capture_position():
    """Capture position data from all cameras."""
    top_x, top_y = None, None
    z_positions = []
    for idx, cam in enumerate(cams):
        ret, frame = cam.read()
        if not ret:
            z_positions.append(None)
            continue
        x, y = detect_position(frame)
        if idx == 0:
            top_x, top_y = x, y
        else:
            z_positions.append(y if y is not None else None)
    z_avg = round(sum(z for z in z_positions if z is not None) / max(len([z 
            for z in z_positions if z is not None]), 1), 2)
    from datetime import timezone
    return datetime.now(timezone.utc).isoformat(), top_x, top_y, z_avg


############################# DATA IMPORT FROM Pi #############################
def recv_temp_packet():
    """Receive and decode thermocouple data."""
    try:
        data = conn.recv(1024).decode()
        pkt = json.loads(data)
        timestamp = pkt["timestamp"]
        temps = pkt.get("temperatures_C", {})
        temps["sma_active"] = pkt.get("sma_active", "")
        return datetime.fromisoformat(timestamp), temps
    except Exception as e:
        print(f"[ERROR] Failed to decode packet: {e}")
        return None, None


################################ DATA COLLECTION ##############################
def run_data_collection(run_index):
    thermo_buffer = deque()
    position_buffer = deque()
    tolerance = timedelta(milliseconds=ALIGNMENT_WINDOW_MS)

    csv_path = get_csv_path(run_index)
    with open(csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["time", "x", "y", "z", "tc1", "tc2", "tc3", "tc4",
                         "sma_active"])

    print(f"[INFO] Beginning data collection for run {run_index + 1}")

    start_time = time.time()
    try:
        while True:
            # 1. Receive thermocouple packet
            ts_thermo, temps = recv_temp_packet()
            if ts_thermo and temps:
                thermo_buffer.append((ts_thermo, temps))

            # 2. Get camera-based position data
            ts_pos_str, x, y, z = capture_position()
            ts_pos = datetime.fromisoformat(ts_pos_str)
            position_buffer.append((ts_pos, x, y, z))

            # 3. Match closest TC data to position timestamp
            while thermo_buffer and position_buffer:
                ts_p, x_p, y_p, z_p = position_buffer[0]
                closest_pair = min(
                    [(abs(ts_p - ts_t), ts_t, temps_t) for ts_t, temps_t in 
                     thermo_buffer],
                    key=lambda t: t[0],
                    default=(None, None, None)
                )

                delta, match_time, match_temps = closest_pair
                if delta <= tolerance:
                    # Match found; write to CSV
                    ch = [match_temps.get(f"ch{i}", "") for i in range(4)]
                    sma_state = match_temps.get("sma_active", "")
                    with open(csv_path, mode='a', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow([ts_p.isoformat(), x_p, y_p, z_p] 
                                        + ch + [sma_state])

                    position_buffer.popleft()
                    thermo_buffer = deque((ts, t) for ts, t in thermo_buffer
                                          if ts != match_time)
                else:
                    break

            # Stop after INTER_RUN_DELAY seconds to move to next pulse
            if time.time() - start_time > INTER_RUN_DELAY:
                print(f"[INFO] Run {run_index + 1} completed.")
                break

    except KeyboardInterrupt:
        print("\n[INFO] Data collection interrupted.")


################################# MAIN LOOP ###################################
# Wait for input before starting data collection
input("[READY] Press Enter to begin data collection...")

try:
    for run_index in range(NUM_RUNS):
        print(f"[INFO] Sending 'start dc' command for run {run_index + 1}")
        conn.sendall(b"start dc")
        run_data_collection(run_index)

        if run_index < NUM_RUNS - 1:
            print(
                f"[INFO] Waiting {INTER_RUN_DELAY} "
                f"seconds before next run...\n"
            )
            time.sleep(INTER_RUN_DELAY)


finally:
    for cam in cams:
        cam.release()
    cv2.destroyAllWindows()
    conn.close()
    server.close()
