# """ 
# (PC) Host Program: Automated Data Collection
# This script will listen for timestamp data from the raspberry pi
# and match it to the position data timestamps, and publish the data to 
# a CSV file.

# Note: Run this 'listener' program before starting the client program.

# Created on Wed Jun 11 17:33:49 2025
# @author: BillyChrist

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

############################ Characterization Parameters #######################
Volts   = 5.0      # volts
Current = 1.0      # amperes
Load    = 200      # grams


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
ALIGNMENT_WINDOW_MS  = 500  # ms, for matching position and temperature data

# Buffer sizes
THERMO_BUFFER_SIZE   = 100  # Pi packet buffer size
POSITION_BUFFER_SIZE = 100  # Host data buffer size

# Cleanup interval and retention
CLEANUP_INTERVAL     = 1.0  # seconds, how often to clean up old data
BUFFER_RETENTION_SEC = 2.0  # seconds, how long to keep unmatched data

# Position sample rate
POSITION_SAMPLE_RATE = 0.25 # seconds, how often to sample position data

# Thermocouple configuration for the Pi
TC_CHANNELS = [0, 1, 2, 3]
TC_TYPE = "J"               # Thermocouple type: J, K, etc.
PULSE_DURATION = 1.5        # seconds
SEND_INTERVAL  = 0.25       # seconds between temperature samples

# Set number of samples to collect, and interval between pulses
NUM_RUNS = 1
INTER_RUN_DELAY = 20        # Interval time between pulses in seconds
LEAD_TIME = 2.0             # seconds, lead-in before SMA pulse

DEBUG = True                # Set to False to suppress debug output

# Error handling configuration
MAX_CONSECUTIVE_ERRORS = 10  # Exit after this many consecutive errors
error_count = 0  # Counter for consecutive errors


#################################### SETUP ####################################
os.makedirs(FRAME_DIR, exist_ok=True)

# Initialize cameras using openCV
cams = []
print("[INFO] Initializing cameras...")
for cam_id in CAMERA_IDS:
    cam = cv2.VideoCapture(cam_id)
    if cam.isOpened():
        print(f"[INFO] Camera {cam_id} opened successfully")
    else:
        print(f"[ERROR] Camera {cam_id} failed to open")
    cams.append(cam)

# File naming convention
def get_csv_path(run_index):
    v_str = f"{str(Volts).replace('.', 'p')}V"
    a_str = f"{str(Current).replace('.', 'p')}A"
    g_str = f"{int(Load)}G"
    return os.path.join(LOG_DIR, f"{v_str}_{a_str}_{g_str}_run_{run_index + 1}.csv")

# Define socket for communication with Pi
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
    "run_time": INTER_RUN_DELAY,
    "lead_time": LEAD_TIME
}
conn.sendall(json.dumps(config_packet).encode())

def read_socket_line():
    """Read a line from the socket with proper error handling."""
    global error_count
    try:
        data = conn.recv(1024).decode().strip()
        if data:  # Reset error count on successful read
            error_count = 0
        return data
    except socket.timeout:
        return None
    except Exception as e:
        error_count += 1
        if error_count >= MAX_CONSECUTIVE_ERRORS:
            print(f"[FATAL] Too many consecutive errors ({error_count}). Exiting program.")
            cleanup_and_exit()
        print(f"[ERROR] Socket read error: {e}")
        return None

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
        raw = conn.recv(1024).decode().strip()
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
    # 1. Wait for 'ready' from Pi
    print(f"[INFO] Waiting for 'ready' from Pi before starting run {run_index + 1}...")
    ready_timeout = 10  # seconds
    while True:
        rlist, _, _ = select.select([conn], [], [], ready_timeout)
        if rlist:
            msg = read_socket_line()
            if msg is None:
                continue
            print(f"[DEBUG] Received message during handshake: '{msg}'")
            if msg.lower() == "ready":
                print(f"[INFO] Received 'ready' from Pi. Proceeding with pre-match sync.")
                break
            else:
                print(f"[WARN] Unexpected message during handshake: '{msg}'")
        else:
            print(f"[WARN] Timeout waiting for 'ready' from Pi. Retrying...")
    # 2. Pre-match sync step
    print(f"[INFO] Sending 'sync' to Pi and capturing pre-match position sample...")
    max_sync_attempts = 3
    sync_success = False
    rtt_offset = 0  # Default offset
    for attempt in range(max_sync_attempts):
        T_host_send = datetime.now()
        conn.sendall(b"sync\n")
        # Try to get a valid position sample
        for _ in range(5):  # Try up to 5 times to get a valid sample
            ts_pos_str, x, y, z = capture_position()
            if x is not None and y is not None and z is not None:
                ts_pos = datetime.fromisoformat(ts_pos_str).replace(tzinfo=None)
                print(f"[INFO] Pre-match position sample timestamp: {ts_pos}")
                sync_success = True
                break
            time.sleep(0.1)  # Short delay between attempts
        if sync_success:
            break
        print(f"[WARN] Sync attempt {attempt + 1} failed. Retrying...")
        time.sleep(0.5)  # Delay between sync attempts
    if not sync_success:
        print("[ERROR] Failed to get valid position sample during pre-match sync.")
        return
    # Wait for sync response from Pi with timeout
    sync_timeout = 10  # seconds
    rlist, _, _ = select.select([conn], [], [], sync_timeout)
    if rlist:
        pi_sync_msg = read_socket_line()
        print(f"[DEBUG] Raw sync message from Pi: '{pi_sync_msg}'")
        if pi_sync_msg.startswith("sync_ts:"):
            pi_ts_str = pi_sync_msg.split(":", 1)[1]
            print(f"[INFO] Pi pre-match temperature sample timestamp: {pi_ts_str}")
            try:
                T_pi_recv = parser.isoparse(pi_ts_str).replace(tzinfo=None)
                T_host_recv = datetime.now()
                rtt = (T_host_recv - T_host_send).total_seconds()
                print(f"[INFO] Measured RTT: {rtt*1000:.1f} ms")
                offset = (T_pi_recv - (T_host_send + (T_host_recv - T_host_send)/2)).total_seconds()
                print(f"[INFO] Calculated clock offset (Pi - Host): {offset*1000:.1f} ms")
                rtt_offset = offset
                if abs(offset*1000) > 100:
                    print("[WARN] Pre-match offset is greater than 100ms. Check network latency or system load.")
            except Exception as e:
                print(f"[ERROR] Failed to parse Pi sync timestamp: {e}")
                print("[ERROR] Aborting run due to failed sync.")
                return
        else:
            print("[WARN] Received unexpected message from Pi during pre-match sync.")
            print("[ERROR] Aborting run due to failed sync.")
            return
    else:
        print("[WARN] Timeout waiting for Pi's sync response. Check Pi connection or sync logic.")
        print("[ERROR] Aborting run due to failed sync.")
        return

    # 3. Lead-in delay to synchronize with Pi (prime position buffer)
    print(f"[INFO] Waiting for lead-in time ({LEAD_TIME} seconds) to synchronize with Pi...")
    position_buffer = deque(maxlen=POSITION_BUFFER_SIZE)
    lead_start = time.time()
    while time.time() - lead_start < LEAD_TIME:
        ts_pos_str, x, y, z = capture_position()
        ts_pos = datetime.fromisoformat(ts_pos_str).replace(tzinfo=None)
        if x is not None and y is not None and z is not None:
            position_buffer.append((ts_pos, x, y, z))
        time.sleep(POSITION_SAMPLE_RATE)
    print(f"[INFO] Lead-in complete. Sending 'trigger' to Pi and starting main data collection loop.")
    conn.sendall(b"trigger")

    # 4. Main data collection loop with Primer
    thermo_buffer = deque(maxlen=THERMO_BUFFER_SIZE)
    tolerance = timedelta(milliseconds=ALIGNMENT_WINDOW_MS)
    last_cleanup_time = time.time()
    csv_path = get_csv_path(run_index)
    try:
        with open(csv_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["run_index", "time", "x", "y", "z", "tc1", "tc2", "tc3", "tc4", "sma_active"])
    except PermissionError:
        print(f"[ERROR] Cannot write to {csv_path}. Please ensure the file is not open in another program.")
        return
    except Exception as e:
        print(f"[ERROR] Failed to create CSV file: {e}")
        return
    matches_count = 0
    start_time = time.time()
    last_position_time = 0
    try:
        while time.time() - start_time < INTER_RUN_DELAY:
            check_for_manual_exit()
            current_time = time.time()
            # a. Clean up old unmatched data
            if current_time - last_cleanup_time > CLEANUP_INTERVAL:
                cutoff_time = datetime.now() - timedelta(seconds=BUFFER_RETENTION_SEC)
                thermo_buffer = deque((ts, t) for ts, t in thermo_buffer if ts > cutoff_time)
                position_buffer = deque((ts, x, y, z) for ts, x, y, z in position_buffer if ts > cutoff_time)
                last_cleanup_time = current_time
                if len(thermo_buffer) > 0 or len(position_buffer) > 0:
                    print(f"[INFO] Buffer cleanup: thermo={len(thermo_buffer)}, position={len(position_buffer)}")
            # b. Receive thermocouple packet with timeout
            try:
                conn.settimeout(0.1)  # 100ms timeout
                raw = read_socket_line()
                if raw is None:
                    continue
                pkt = json.loads(raw)
                timestamp = pkt["timestamp"]
                temps = pkt.get("temperatures_C", {})
                temps["sma_active"] = pkt.get("sma_active", "")
                ts = parser.isoparse(timestamp).replace(tzinfo=None)
                # Adjust Pi timestamp using calculated offset
                ts = ts - timedelta(seconds=rtt_offset)
                thermo_buffer.append((ts, temps))
            except socket.timeout:
                pass
            except json.JSONDecodeError as e:
                error_count += 1
                if error_count >= MAX_CONSECUTIVE_ERRORS:
                    print(f"[FATAL] Too many consecutive errors ({error_count}). Exiting program.")
                    cleanup_and_exit()
                if DEBUG:
                    print(f"[DEBUG] Failed to decode JSON packet: {e}")
            except Exception as e:
                error_count += 1
                if error_count >= MAX_CONSECUTIVE_ERRORS:
                    print(f"[FATAL] Too many consecutive errors ({error_count}). Exiting program.")
                    cleanup_and_exit()
                if not isinstance(e, socket.timeout):
                    print(f"[ERROR] Failed to process packet: {e}")
                continue
            # c. Get camera-based position data (only every POSITION_SAMPLE_RATE seconds)
            if current_time - last_position_time >= POSITION_SAMPLE_RATE:
                ts_pos_str, x, y, z = capture_position()
                ts_pos = datetime.fromisoformat(ts_pos_str).replace(tzinfo=None)
                if x is not None and y is not None and z is not None:
                    position_buffer.append((ts_pos, x, y, z))
                last_position_time = current_time

            # d. Match closest TC data to position timestamp
            while thermo_buffer and position_buffer:
                ts_t, temps = thermo_buffer[0]
                # Find the position with the closest timestamp
                closest_idx, min_delta = None, None
                for i, (ts_p, x, y, z) in enumerate(position_buffer):
                    delta = abs(ts_t - ts_p)
                    if min_delta is None or delta < min_delta:
                        min_delta = delta
                        closest_idx = i
                # Only match if the closest position is valid
                if closest_idx is not None:
                    x, y, z = position_buffer[closest_idx][1:]
                    if x is not None and y is not None and z is not None:
                        if min_delta is not None and DEBUG:
                            print(f"[DEBUG] Thermo ts: {ts_t}, Closest position ts: {position_buffer[closest_idx][0]}, Delta: {min_delta.total_seconds()*1000:.1f} ms")
                        if min_delta is not None and min_delta <= tolerance:
                            # Found a match
                            ts_p, x, y, z = position_buffer[closest_idx]
                            ch = [temps.get(f"ch{i}", "") for i in range(4)]
                            sma_state = temps.get("sma_active", "")
                            try:
                                with open(csv_path, mode='a', newline='') as file:
                                    writer = csv.writer(file)
                                    writer.writerow([run_index + 1, ts_t.isoformat(), x, y, z] + ch + [sma_state])
                                matches_count += 1
                            except Exception as e:
                                print(f"[ERROR] Failed to write to CSV: {e}")
                                continue
                            # Remove matched entries
                            thermo_buffer.popleft()
                            position_buffer.remove((ts_p, x, y, z))
                            continue
                # No match within window, drop the oldest
                if position_buffer[0][0] < ts_t:
                    position_buffer.popleft()
                else:
                    thermo_buffer.popleft()
                break

        print(f"[INFO] Run {run_index + 1} completed. Total matches: {matches_count}")

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
        try:
            conn.sendall(b"start dc")
            run_data_collection(run_index)
        except (ConnectionResetError, BrokenPipeError) as e:
            print(f"[ERROR] Connection lost during run {run_index + 1}: {e}")
            break
        except Exception as e:
            print(f"[ERROR] Unexpected error during run {run_index + 1}: {e}")
            break

        if run_index < NUM_RUNS - 1:
            print(f"[INFO] Starting next run...")

except KeyboardInterrupt:
    print("\n[INFO] Data collection interrupted by user.")
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
finally:
    try:
        conn.sendall(b"stop")
        print("[INFO] Sent 'stop' command to Pi.")
    except Exception as e:
        print(f"[WARN] Could not send 'stop' command: {e}")
    print("[INFO] Cleaning up...")
    for cam in cams:
        cam.release()
    cv2.destroyAllWindows()
    try:
        conn.close()
    except:
        pass
    try:
        server.close()
    except:
        pass
    print("[INFO] Cleanup complete.")

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

def cleanup_and_exit():
    """Clean up resources and exit the program."""
    print("[INFO] Cleaning up resources before exit...")
    try:
        conn.sendall(b"stop")
        print("[INFO] Sent 'stop' command to Pi.")
    except Exception as e:
        print(f"[WARN] Could not send 'stop' command: {e}")
    
    for cam in cams:
        cam.release()
    cv2.destroyAllWindows()
    
    try:
        conn.close()
    except:
        pass
    try:
        server.close()
    except:
        pass
    print("[INFO] Cleanup complete. Exiting.")
    os._exit(1)
