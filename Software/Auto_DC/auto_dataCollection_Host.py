# """ 
# (PC) Host Program: Automated Data Collection
# This script will listen for timestamp data from the raspberry pi
# and match it to the position data timestamps, and publish the data to 
# a CSV file.

# Note: Run this 'listener' program before starting the client program.

# To run the software, run the following commands to activate the virtual environment: 
#  > cd "C:\Users\Owner\Desktop\SERC\STARFISH Project\Software\STARFISH"
#  > & "venv\Scripts\Activate.ps1"    (in VScode terminal)
#
# Created on Wed Jun 11 17:33:49 2025
#
# @author: BillyChrist
# """

# === Import libraries ===
import cv2
import csv
import os
import socket
import json
import time
from datetime import datetime, timedelta, timezone
from dateutil import parser
from collections import deque
import threading
import sys
import select
import numpy as np

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
ALIGNMENT_WINDOW_MS  = 300  # ms, for matching position and temperature data

# Buffer sizes
THERMO_BUFFER_SIZE   = 100  # Pi packet buffer size
POSITION_BUFFER_SIZE = 100  # Host data buffer size
time_offset = 0.0           # Time offset between Pi and Host clocks

# Cleanup interval and retention
CLEANUP_INTERVAL     = 0.5  # seconds, how often to clean up old data
BUFFER_RETENTION_SEC = 1.0  # seconds, how long to keep unmatched data

# Position sample rate
POSITION_SAMPLE_RATE = 0.25 # seconds, how often to sample position data

# Thermocouple configuration for the Pi
TC_CHANNELS = [0, 1, 2, 3]
TC_TYPE = "J"               # Thermocouple type: J, K, etc.
PULSE_DURATION = 1.5        # seconds
SEND_INTERVAL  = 0.25       # seconds between temperature samples

# Set number of samples to collect, and interval between pulses
NUM_RUNS = 10
INTER_RUN_DELAY = 20        # Interval time between pulses in seconds
LEAD_TIME = 2.0             # seconds, lead-in before SMA pulse

# Debug mode. Set to False to suppress debug output
DEBUG = True                

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

################### Calibration and Template Loading ###########################
def load_calibration(calib_dir="Software/Auto_DC/calibration_data"):
    calib_path = os.path.join(calib_dir, "calibration_data.txt")
    pixels_per_mm = None
    template_files = []
    with open(calib_path, "r") as f:
        for line in f:
            if line.startswith("pixels_per_mm_ball"):
                pixels_per_mm = float(line.split("=")[1].strip())
            if line.startswith("template_files"):
                files = line.split("=")[1].strip()
                template_files = [os.path.join(calib_dir, fn.strip()) for fn in files.split(",") if fn.strip()]
    if pixels_per_mm is None:
        raise ValueError("pixels_per_mm_ball not found in calibration file.")
    return pixels_per_mm, template_files

def load_templates(template_files):
    templates = []
    for fn in template_files:
        temp = cv2.imread(fn)
        if temp is not None:
            templates.append(temp)
        else:
            print(f"[WARN] Could not load template: {fn}")
    return templates

# Template-based position detection
def detect_position_with_templates(frame, templates):
    best_val = -1
    best_loc = None
    best_temp = None
    for temp in templates:
        if frame.shape[0] < temp.shape[0] or frame.shape[1] < temp.shape[1]:
            continue
        res = cv2.matchTemplate(frame, temp, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > best_val:
            best_val = max_val
            best_loc = max_loc
            best_temp = temp
    if best_loc is not None and best_temp is not None:
        h, w = best_temp.shape[:2]
        center = (best_loc[0] + w//2, best_loc[1] + h//2)
        return center, best_val
    return None, None

# Load calibration and templates at startup
pixels_per_mm, template_files = load_calibration()
templates = load_templates(template_files)

# Update capture_position to use template matching
def capture_position():
    """Capture position data from all cameras using template matching."""
    top_x, top_y = None, None
    z_positions = []
    for idx, cam in enumerate(cams):
        ret, frame = cam.read()
        if not ret:
            z_positions.append(None)
            continue
        
        # Use template matching for position detection
        center, match_val = detect_position_with_templates(frame, templates)
        if center is not None:
            x, y = center
            # Convert to mm using calibration
            x_mm = x / pixels_per_mm
            y_mm = y / pixels_per_mm
        else:
            x_mm, y_mm = None, None
        if idx == 0:
            top_x, top_y = x_mm, y_mm
        else:
            z_positions.append(y_mm if y_mm is not None else None)
    z_avg = round(sum(z for z in z_positions if z is not None) / max(len([z for z in z_positions if z is not None]), 1), 2)
    from datetime import timezone
    return datetime.now(timezone.utc).isoformat(), top_x, top_y, z_avg


############################# DATA IMPORT FROM Pi #############################
def recv_temp_packet():
    """Receive and decode thermocouple data."""
    try:
        raw = read_socket_line()
        if raw is None:
            return None, None
        pkt = json.loads(raw)
        timestamp = pkt["timestamp"]
        temps = pkt.get("temperatures_C", {})
        temps["sma_active"] = pkt.get("sma_active", "")
        ts = parser.isoparse(timestamp)
       
        # Adjust Pi timestamp using calculated offset
        ts = ts - timedelta(seconds=time_offset)  # Use time_offset instead of rtt_offset
        return ts, temps
    except Exception as e:
        if not isinstance(e, socket.timeout):
            print(f"[ERROR] Failed to decode packet: {e}")
        return None, None

################################ DATA COLLECTION ##############################
thermo_buffer   = deque(maxlen=THERMO_BUFFER_SIZE)
position_buffer = deque(maxlen=POSITION_BUFFER_SIZE)

def run_data_collection(run_index):
    global thermo_buffer, position_buffer, time_offset
    
    print(f"\n[DEBUG] Starting run {run_index + 1}")
    
    # Initialize buffers for this run
    thermo_buffer.clear()
    position_buffer.clear()
    time_offset = 0.0
    
    print(f"[DEBUG] Initial buffer states: thermo={len(thermo_buffer)}, position={len(position_buffer)}")
    
    # Set socket timeout for the entire run
    conn.settimeout(0.1)  # 100ms timeout for the entire run
    
    try:
        # 1. Wait for 'ready' from Pi
        print(f"[INFO] Waiting for 'ready' from Pi before starting run {run_index + 1}...")
        while True:
            try:
                raw = read_socket_line()
                if raw is None:
                    continue
                msg = raw.strip()
                print(f"[DEBUG] Received message during handshake: '{msg}'")
                if msg == 'ready':
                    break
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[ERROR] Error during handshake: {e}")
                return

        print("[INFO] Received 'ready' from Pi. Proceeding with pre-match sync.")
        
        # 2. Pre-match sync
        print("[INFO] Sending 'sync' to Pi and capturing pre-match position sample...")
        conn.sendall(b"sync\n")
        
        # Capture position sample
        position_sample = capture_position()
        if position_sample is None:
            print("[ERROR] Failed to capture pre-match position sample")
            return
        print("[INFO] Pre-match position sample captured")
        
        # Get sync timestamp from Pi
        try:
            raw = read_socket_line()
            if raw is None:
                print("[ERROR] No sync response from Pi")
                return
            msg = raw.strip()
            print(f"[DEBUG] Raw sync message from Pi: '{msg}'")
            
            if not msg.startswith('sync_ts:'):
                print(f"[ERROR] Invalid sync message format: {msg}")
                return
                
            pi_ts = float(msg.split(':')[1])
            host_ts = time.time()
           
            # Convert position_sample[0] (ISO string) to float timestamp
            host_pos_ts = parser.isoparse(position_sample[0]).timestamp()
            rtt = (host_ts - host_pos_ts) * 1000  # Convert to ms
            time_offset = pi_ts - host_ts
            
            print(f"[INFO] Measured RTT: {rtt:.1f} ms")
            print(f"[INFO] Calculated time offset (Pi - Host): {time_offset*1000:.1f} ms")
            
            if abs(time_offset) > 0.1:  # 100ms threshold
                print("[WARN] Pre-match offset is greater than 100ms. Check network latency or system load.")
                
        except Exception as e:
            print(f"[ERROR] Failed to process sync response: {e}")
            return

        # 3. Lead-in time
        print("[INFO] Waiting for lead-in time (2.0 seconds) to synchronize with Pi...")
        time.sleep(2.0)
        print("[INFO] Lead-in complete. Sending 'trigger' to Pi and starting main data collection loop.")
        conn.sendall(b"trigger\n")
        
        # 4. Main data collection loop
        matches = 0
        sma_start_time = None
        run_start_time = time.time()
        # Helper to convert position_buffer timestamp to float
        def get_pos_ts(pos):
            return parser.isoparse(pos[0]).timestamp()

        while True:
            # Exit if run time exceeded
            if time.time() - run_start_time > (INTER_RUN_DELAY + PULSE_DURATION + 5):  # Add buffer for safety
                print("[INFO] Run time exceeded, ending run.")
                break
            # a. Capture position data
            position_sample = capture_position()
            if position_sample is not None:
                position_buffer.append(position_sample)
            
            # b. Receive thermocouple packet with timeout
            try:
                raw = read_socket_line()
                if raw is None:
                    continue
                    
                msg = raw.strip()
                
                # Check for SMA pulse start (accept both 'sma_start:' and 'pulse_start_ts:')
                if msg.startswith('sma_start:') or msg.startswith('pulse_start_ts:'):
                    try:
                        sma_start_time = float(msg.split(':')[1])
                        print(f"[INFO] SMA pulse start received from Pi, t=0 set at {sma_start_time}")
                    except Exception as e:
                        print(f"[ERROR] Failed to parse SMA pulse start time: {e}")
                    continue
                    
                # Parse temperature data as JSON packet
                try:
                    data = json.loads(msg)
                    if "timestamp" in data and "temperatures_C" in data:
                        thermo_ts = data['timestamp']
                        thermo_buffer.append((thermo_ts, data))
                        
                        # Find closest position sample
                        if position_buffer:
                            closest_pos = min(position_buffer, key=lambda x: abs(get_pos_ts(x) - thermo_ts))
                            delta = abs(get_pos_ts(closest_pos) - thermo_ts) * 1000  # Convert to ms
                            print(f"[DEBUG] Thermo ts: {thermo_ts:.3f}, Closest position ts: {get_pos_ts(closest_pos):.3f}, Delta: {delta:.1f} ms")
                            if delta <= ALIGNMENT_WINDOW_MS:
                                matches += 1
                                # Write to CSV
                                if sma_start_time is not None:
                                    time_ms = (thermo_ts - sma_start_time) * 1000
                                    if DEBUG:
                                        print(f"[DEBUG] Writing row to CSV: time_ms={time_ms}, x={closest_pos[1]}, y={closest_pos[2]}, temps={[data['temperatures_C'].get(f'ch{i}') for i in range(4)]}, sma_active={data['sma_active']}")
                                    writer.writerow({
                                        'time_ms': time_ms,
                                        'x_mm': closest_pos[1],
                                        'y_mm': closest_pos[2],
                                        'temp_ch0': data['temperatures_C'].get('ch0'),
                                        'temp_ch1': data['temperatures_C'].get('ch1'),
                                        'temp_ch2': data['temperatures_C'].get('ch2'),
                                        'temp_ch3': data['temperatures_C'].get('ch3'),
                                        'sma_active': data['sma_active']
                                    })
                                    csv_file.flush()
                                else:
                                    if DEBUG:
                                        print(f"[DEBUG] Skipping CSV write: sma_start_time is None (thermo_ts={thermo_ts})")
                    # else: not a temperature packet, ignore
                    
                except json.JSONDecodeError:
                    # Not a JSON packet, could be a control message, ignore
                    pass
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[ERROR] Error in main loop: {e}")
                break
                
            # c. Cleanup old data
            current_time = time.time()
            while thermo_buffer and current_time - thermo_buffer[0][0] > BUFFER_RETENTION_SEC:
                thermo_buffer.popleft()
            while position_buffer and current_time - get_pos_ts(position_buffer[0]) > BUFFER_RETENTION_SEC:
                position_buffer.popleft()
                
            if len(thermo_buffer) > 0 or len(position_buffer) > 0:
                print(f"[INFO] Buffer cleanup: thermo={len(thermo_buffer)}, position={len(position_buffer)}")
                
        print(f"[INFO] Run {run_index + 1} completed. Total matches: {matches}")
        print(f"[DEBUG] Final buffer states: thermo={len(thermo_buffer)}, position={len(position_buffer)}")
        # Print first few timestamps for manual inspection
        print("[DEBUG] First 5 thermo timestamps:", [t[0] for t in list(thermo_buffer)[:5]])
        print("[DEBUG] First 5 position timestamps:", [p[0] for p in list(position_buffer)[:5]])
        if matches == 0:
            print("[WARN] No matches found! Check timestamp alignment and template matching.")
        print(f"[DEBUG] Buffer contents - Thermo: {list(thermo_buffer)}... Position: {list(position_buffer)}...")
        
    except KeyboardInterrupt:
        print("\n[INFO] Data collection interrupted by user.")
    finally:
        conn.settimeout(None)  # Reset timeout to blocking mode
        # Clear any remaining buffers
        thermo_buffer.clear()
        position_buffer.clear()


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
        
        # Set up CSV file for this run
        csv_path = get_csv_path(run_index)
        csv_file = open(csv_path, 'w', newline='')
        fieldnames = ['time_ms', 'x_mm', 'y_mm', 'temp_ch0', 'temp_ch1', 'temp_ch2', 'temp_ch3', 'sma_active']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        
        print(f"[INFO] Starting run {run_index + 1} with CSV file: {csv_path}")
        
        try:
            # Send start command to Pi
            conn.sendall(b"start dc\n")
            print(f"[INFO] Sent 'start dc' command for run {run_index + 1}")
            
            # Run data collection for this run
            run_data_collection(run_index)
            
        except (ConnectionResetError, BrokenPipeError) as e:
            print(f"[ERROR] Connection lost during run {run_index + 1}: {e}")
            break
        except Exception as e:
            print(f"[ERROR] Unexpected error during run {run_index + 1}: {e}")
            break
        finally:
            # Close CSV file for this run
            csv_file.close()
            print(f"[INFO] Closed CSV file for run {run_index + 1}")

        # Only send reset if there are more runs to go
        if run_index < NUM_RUNS - 1:
            print(f"[INFO] Preparing for next run...")
            try:
                # Send reset command to Pi and wait for acknowledgment
                conn.sendall(b"reset\n")
                print("[INFO] Sent reset command to Pi")
                
                # Wait for acknowledgment with timeout
                rlist, _, _ = select.select([conn], [], [], 5.0)
                if rlist:
                    raw = read_socket_line()
                    if raw and raw.strip() == "reset_ack":
                        print("[INFO] Pi acknowledged reset")
                    else:
                        print(f"[WARN] Unexpected response from Pi after reset: {raw}")
                else:
                    print("[WARN] No response from Pi after reset command")
                    
            except Exception as e:
                print(f"[WARN] Failed to reset Pi: {e}")
            
            # Add delay between runs
            print("[INFO] Waiting 2 seconds before next run...")
            time.sleep(2)

except KeyboardInterrupt:
    print("\n[INFO] Data collection interrupted by user.")
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
finally:
    try:
        conn.sendall(b"stop\n")
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

# Clean up resources and exit the program.
def cleanup_and_exit():

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
