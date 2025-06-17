# """ 
# (PC) Host Program: Automated Data Collection
# This script will listen for timestamp data from the raspberry pi
# and match it to the position data timestamps, and publish the data to 
# a CSV file.

# Note: Run this 'listener' program before starting the client program.

# Created on Wed Jun 11 17:33:49 2025
# @author: space_lab

# To run the software, run the following commands to activate the virtual environment: 
#  > cd "C:\Users\Owner\Desktop\SERC\STARFISH Project\Software\STARFISH"
#  > & "venv\Scripts\Activate.ps1"    (in VScode terminal)

# Pi's current ip address: 

# """

# === Import libraries ===
import cv2
import csv
import os
import socket
import json
import time
from datetime import datetime, timedelta
from dateutil import parser
from collections import deque
import threading
import sys
import select


################################## CONFIGURATION ##############################
# Set data logging directory
LOG_DIR = r"C:\Users\Owner\Desktop\SERC\STARFISH_Project\Software\STARFISH\Thermo_Position_Data"
FRAME_DIR = os.path.join(LOG_DIR, "frames")

# Set port and IP info (currently listening for any connecting ip)
LISTEN_IP = "0.0.0.0"  # listens for anything trying to connect
LISTEN_PORT = 5005

# Define camera IDs in use
CAMERA_IDS = [1] #[0, 1, 2, 3, 4]  # 0: top for X/Y, 1-4: for Z

# Alignment tolerance in milliseconds
ALIGNMENT_WINDOW_MS = 500  

# Thermocouple configuration for the Pi
TC_CHANNELS = [0, 1, 2, 3]
TC_TYPE = "J"  # Thermocouple type: J, K, etc.
PULSE_DURATION = 1.0     # seconds
SEND_INTERVAL  = 1.0     # seconds between temperature samples

# Set number of samples to collect, and interval between pulses
NUM_RUNS = 5
INTER_RUN_DELAY = 20     # Interval time between pulses in seconds
LEAD_TIME = 2.0          # seconds, lead-in before SMA pulse


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
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((LISTEN_IP, LISTEN_PORT))
server.listen(1)
print(f"[INFO] Listening for Raspberry Pi on {LISTEN_IP}:{LISTEN_PORT}")
conn, addr = server.accept()
print(f"[INFO] Connected to Raspberry Pi at {addr}", flush=True)

# Send configuration to Pi
config_packet = {
    "pulse_duration": PULSE_DURATION,
    "send_interval": SEND_INTERVAL,
    "channels": TC_CHANNELS,
    "tc_type": TC_TYPE,
    "num_runs": NUM_RUNS,
    "run_time": INTER_RUN_DELAY,  # send run duration to Pi
    "lead_time": LEAD_TIME        # send lead-in time to Pi
}
conn.sendall(json.dumps(config_packet).encode())


############################# CAMERA PROCESSING ###############################
def detect_position(frame):
    """Basic red ball detection to extract (x, y) or z position."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
   
    # Configure color detection upper and lower bounds
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
        raw = conn.makefile().readline()
        pkt = json.loads(raw)
        timestamp = pkt["timestamp"]
        temps = pkt.get("temperatures_C", {})
        temps["sma_active"] = pkt.get("sma_active", "")
        ts = parser.isoparse(timestamp).replace(tzinfo=None)
        return ts, temps
    except Exception as e:
        print(f"[ERROR] Failed to decode packet: {e}")
        return None, None

################################ DATA COLLECTION ##############################
def run_data_collection(run_index):
    thermo_buffer = deque(maxlen=1000)  # Limit buffer size
    position_buffer = deque(maxlen=1000)  # Limit buffer size
    tolerance = timedelta(milliseconds=ALIGNMENT_WINDOW_MS)
    last_cleanup_time = time.time()
    CLEANUP_INTERVAL = 5.0      # Clean up old data every 5 seconds
    POSITION_SAMPLE_RATE = 0.5  # Sample position data every 0.5 seconds

    csv_path = get_csv_path(run_index)
    with open(csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["run_index", "time", "x", "y", "z", "tc1", "tc2", "tc3", "tc4", "sma_active"])

    print(f"[INFO] Beginning data collection for run {run_index + 1}")

    start_time = time.time()
    last_position_time = 0
    try:
        while time.time() - start_time < INTER_RUN_DELAY:  # Run for INTER_RUN_DELAY seconds
            check_for_manual_exit()
            
            current_time = time.time()
            
            # Clean up old unmatched data periodically
            if current_time - last_cleanup_time > CLEANUP_INTERVAL:
                # Remove data older than 2 seconds
                cutoff_time = datetime.now() - timedelta(seconds=2)
                thermo_buffer = deque((ts, t) for ts, t in thermo_buffer if ts > cutoff_time)
                position_buffer = deque((ts, x, y, z) for ts, x, y, z in position_buffer if ts > cutoff_time)
                last_cleanup_time = current_time
                print(f"[INFO] Buffer cleanup: thermo={len(thermo_buffer)}, position={len(position_buffer)}")

            # 1. Receive thermocouple packet with timeout
            try:
                conn.settimeout(0.1)  # 100ms timeout
                raw = conn.makefile().readline()
                pkt = json.loads(raw)
                timestamp = pkt["timestamp"]
                temps = pkt.get("temperatures_C", {})
                temps["sma_active"] = pkt.get("sma_active", "")
                ts = parser.isoparse(timestamp).replace(tzinfo=None)
                thermo_buffer.append((ts, temps))
            except socket.timeout:
                pass
            except Exception as e:
                print(f"[ERROR] Failed to decode packet: {e}")
                continue

            # 2. Get camera-based position data (only every POSITION_SAMPLE_RATE seconds)
            if current_time - last_position_time >= POSITION_SAMPLE_RATE:
                ts_pos_str, x, y, z = capture_position()
                ts_pos = datetime.fromisoformat(ts_pos_str).replace(tzinfo=None)
                position_buffer.append((ts_pos, x, y, z))
                last_position_time = current_time

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
                        writer.writerow([run_index + 1, ts_p.isoformat(), x_p, y_p, z_p] + ch + [sma_state])

                    position_buffer.popleft()
                    thermo_buffer = deque((ts, t) for ts, t in thermo_buffer
                                          if ts != match_time)
                else:
                    break

            # --- Buffer clearing for stale unmatched data ---
            # If the head of position_buffer is too old to ever match, drop it
            if position_buffer and thermo_buffer:
                ts_p, *_ = position_buffer[0]
                ts_t, _ = thermo_buffer[0]
                if ts_p < ts_t - tolerance:
                    print(f"[WARN] Dropping stale position data: {ts_p.isoformat()} (older than first thermo: {ts_t.isoformat()})")
                    position_buffer.popleft()
                elif ts_t < ts_p - tolerance:
                    print(f"[WARN] Dropping stale thermo data: {ts_t.isoformat()} (older than first position: {ts_p.isoformat()})")
                    thermo_buffer.popleft()

        print(f"[INFO] Run {run_index + 1} completed.")

    except KeyboardInterrupt:
        print("\n[INFO] Data collection interrupted.")
    finally:
        conn.settimeout(None)  # Reset timeout


################################# MAIN LOOP ###################################
# Kill Switch, enter this command in console: open("stop.txt", "w").close()
def check_for_manual_exit():
    try:
        if os.path.exists("stop.txt"):
            print("[STOP] Detected stop file. Exiting.")
            os._exit(0)
    except:
        pass


# Wait for input before starting data collection
input("[READY] Press Enter to begin data collection...")

try:
    for run_index in range(NUM_RUNS):
        check_for_manual_exit()
        print(f"[INFO] Sending 'start dc' command for run {run_index + 1}")
        conn.sendall(b"start dc")
        run_data_collection(run_index)

        if run_index < NUM_RUNS - 1:
            print(
                f"[INFO] Waiting {INTER_RUN_DELAY} "
                f"seconds before next run...\n"
            )
            time.sleep(INTER_RUN_DELAY)
            check_for_manual_exit()


finally:
    for cam in cams:
        cam.release()
    cv2.destroyAllWindows()
    conn.close()
    server.close()

def calibrate_camera():
    """
    TODO: Implement camera calibration to convert pixel coordinates to real-world units (pixels/mm).
    Steps may include:
      1. Capture an image with a ruler or known reference object.
      2. Measure the number of pixels corresponding to a known distance.
      3. Calculate and store the scale (pixels per mm or mm per pixel).
      4. Optionally, use OpenCV camera calibration for lens distortion correction.
    """
    pass
