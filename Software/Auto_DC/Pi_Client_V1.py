# """ 
# (Pi) Client program: Thermocouple Data Collection & SMA Control

# This script will import configuration settings from the control program (PC), 
# listen for startup commands, control the thermocouple data collection 
# and SMA power pulse, and send the data along with timestamp info for the Host 
# program.

# connect to virtual environment by: 
# > source venv/bin/activate

# """

#!/usr/bin/env python3

# === Import libraries ===
import socket
import json
import time
import datetime
import RPi.GPIO as GPIO
from daqhats import mcc134, HatIDs, HatError, TcTypes

# Specify dependency path for daqhats
import sys
sys.path.append('/home/starfish2/STARFISH/Thermal/daqhats_custom_stuff/examples/python/mcc134')

from daqhats_utils import select_hat_device

################################ CONFIGURATION ################################
PC_IP = '192.168.0.102'  # Update with current Host PC's IP address
PC_PORT = 5005

SMA_GPIO_PIN = 18

DEBUG = True             # Set to False to reduce debug output

################################## SETUP ######################################
# GPIO Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(SMA_GPIO_PIN, GPIO.OUT)
GPIO.output(SMA_GPIO_PIN, GPIO.LOW)

# Connect to Host
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((PC_IP, PC_PORT))
print(f"[INFO] Connected to PC at {PC_IP}:{PC_PORT}")

# Initialize MCC 134
try:
    address = select_hat_device(HatIDs.MCC_134)
    hat = mcc134(address)
except HatError as e:
    print(f"[ERROR] Could not initialize MCC 134: {e}")
    GPIO.cleanup()
    client.close()
    exit(1)

######################### Receive Configuration From Host ######################
config = json.loads(client.recv(1024).decode())
print(f"[INFO] Received config: {config}")

TC_CHANNELS = config.get("channels", [0])                # default: [0]
SMA_PULSE_DURATION = config.get("pulse_duration", 1.0)   # default: 1.0 sec
SEND_INTERVAL = config.get("send_interval", 0.25)        # default: 0.25 sec
TC_TYPE = getattr(TcTypes, f"TYPE_{config.get('tc_type', 'J')}")
NUM_RUNS = config.get("num_runs", 1)
RUN_TIME = config.get("run_time", 20.0)  # seconds
LEAD_TIME = config.get("lead_time", 2.0) # seconds

for ch in TC_CHANNELS:
    hat.tc_type_write(ch, TC_TYPE)

################################## LOOP #######################################
should_exit = False

def run_data_collection(run_index):
    global client, should_exit
    # 1. Lead-in delay and buffer priming
    # Wait for pre-match sync from host
    print(f"[INFO] Waiting for 'sync' from host for pre-match...")
    try:
        client.settimeout(10)  # 10 second timeout for sync
        msg = client.recv(1024).decode().strip()
        if msg.lower() == "sync":
            # Pre-match sync: record Pi's receive time and send to host
            from datetime import timezone
            T_pi_recv = datetime.now(timezone.utc).isoformat()
            try:
                client.sendall(f"sync_ts:{T_pi_recv}".encode())
                print(f"[INFO] Sent sync timestamp to host: {T_pi_recv}")
            except Exception as e:
                print(f"[WARN] Failed to send sync timestamp: {e}")
        elif msg.lower() == "stop":
            print("[INFO] Received stop command from host during pre-match. Exiting.")
            should_exit = True
            return
        else:
            print(f"[WARN] Received unexpected message from host during pre-match sync: {msg}")
    except socket.timeout:
        print("[WARN] Timeout waiting for 'sync' from host. Check host connection or sync logic.")
    finally:
        client.settimeout(None)  # Reset timeout
    # 2. Lead-in delay and buffer priming
    print(f"[INFO] Lead-in: waiting {LEAD_TIME} seconds before starting run {run_index + 1}...")
    lead_start = time.time()
    while time.time() - lead_start < LEAD_TIME:
        # Optionally, you could prime a buffer here if needed
        time.sleep(0.05)
    print(f"[INFO] Lead-in complete. Sending 'ready' to host and waiting for 'trigger'...")
    client.sendall(b"ready")
    # 3. Wait for 'trigger' from host
    while True:
        msg = client.recv(1024).decode().strip()
        if msg.lower() == "trigger":
            print("[INFO] Received 'trigger' from host. Starting data collection.")
            break
        elif msg.lower() == "stop":
            print("[INFO] Received stop command from host during handshake. Exiting.")
            should_exit = True
            return
    # 4. Main data collection loop (unchanged)
    start_time = time.time()
    sma_active = False
    pulse_start_time = None
    last_sample_time = time.time()
    pulse_sent = False

    while True:
        if should_exit:
            GPIO.output(SMA_GPIO_PIN, GPIO.LOW)
            break
        now = time.time()
        elapsed = now - start_time

        # Lead-in period: wait before activating SMA
        if not pulse_sent and elapsed >= LEAD_TIME:
            GPIO.output(SMA_GPIO_PIN, GPIO.HIGH)
            sma_active = True
            pulse_start_time = now
            pulse_sent = True
            if DEBUG:
                print(f"[INFO] SMA pulse started at t={elapsed:.2f}s")

        # End SMA pulse after configured duration
        if sma_active and pulse_sent and (now - pulse_start_time >= SMA_PULSE_DURATION):
            GPIO.output(SMA_GPIO_PIN, GPIO.LOW)
            sma_active = False
            if DEBUG:
                print(f"[INFO] SMA pulse ended at t={elapsed:.2f}s")

        # Sample temperature and send to host at fixed interval
        if now >= last_sample_time:
            temps = {}
            for ch in TC_CHANNELS:
                try:
                    value = hat.t_in_read(ch)
                    temps[f"ch{ch}"] = round(value, 2)
                except Exception as e:
                    temps[f"ch{ch}"] = None
                    if DEBUG:
                        print(f"[ERROR] Temp read failed for ch{ch}: {e}")

            timestamp = datetime.datetime.utcnow().isoformat() + "Z"

            packet = {
                "run_index": run_index + 1,
                "timestamp": timestamp,
                "temperatures_C": temps,
                "sma_active": sma_active
            }

            try:
                if DEBUG:
                    print("[DEBUG] Sending packet...")
                client.sendall((json.dumps(packet) + '\n').encode())
                if DEBUG:
                    print(f"[INFO] Sent: {packet}")
            except Exception as e:
                print(f"[ERROR] Failed to send packet to host: {e}")
                # Try to reconnect
                reconnect_attempts = 0
                while reconnect_attempts < 5:
                    try:
                        time.sleep(2)
                        client.close()
                        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        client.connect((PC_IP, PC_PORT))
                        print(f"[INFO] Reconnected to PC at {PC_IP}:{PC_PORT}")
                        break
                    except Exception as e2:
                        print(f"[ERROR] Reconnect attempt {reconnect_attempts+1} failed: {e2}")
                        reconnect_attempts += 1
                if reconnect_attempts == 5:
                    print("[FATAL] Could not reconnect to host. Exiting.")
                    break

            last_sample_time += SEND_INTERVAL
            sleep_time = last_sample_time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

        # Stop after run_time seconds
        if elapsed > RUN_TIME:
            GPIO.output(SMA_GPIO_PIN, GPIO.LOW)
            break

try:
    print("[INFO] Waiting for 'start dc' or 'stop' commands from host...")
    run_index = 0
    while True:
        msg = client.recv(1024).decode().strip()
        if msg.lower() == "start dc":
            print(f"[INFO] Starting data collection run {run_index + 1}...")
            run_data_collection(run_index)
            run_index += 1
        elif msg.lower() == "stop":
            print("[INFO] Received stop command from host. Exiting.")
            should_exit = True
            break

except KeyboardInterrupt:
    print("\n[INFO] Stopping script.")

finally:
    GPIO.output(SMA_GPIO_PIN, GPIO.LOW)
    GPIO.cleanup()
    client.close()
