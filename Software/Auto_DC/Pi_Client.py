# """ 
# (Pi) Client program: Thermocouple Data Collection & SMA Control

# This script will import configuration settings from the control program (PC), 
# listen for startup commands, control the thermocouple data collection 
# and SMA power pulse, and send the data along with timestamp info for the Host 
# program.

# connect to virtual environment by: 
#  > source venv/bin/activate
#
# Created on Wed Jun 11 17:33:49 2025
#
# @author: BillyChrist
# """

#!/usr/bin/env python3

# === Import libraries ===
import socket
import json
import time
import datetime
import RPi.GPIO as GPIO
from daqhats import mcc134, HatIDs, HatError, TcTypes
import os

# Specify dependency path for daqhats
import sys
sys.path.append('/home/starfish2/STARFISH/Thermal/daqhats_custom_stuff/examples/python/mcc134')

from daqhats_utils import select_hat_device

################################ CONFIGURATION ################################
PC_IP = '192.168.0.102'        # Update with current Host PC's IP address
PC_PORT = 5005

SMA_GPIO_PIN = 16

DEBUG = True                   # Set to False to reduce debug output

MAX_CONSECUTIVE_ERRORS = 10    # Exit after this many consecutive errors

########################## Helper and Cleanup Functions #######################
def cleanup_and_exit():
    """Clean up resources and exit the program."""
    print("[INFO] Cleaning up resources before exit...")
    GPIO.output(SMA_GPIO_PIN, GPIO.LOW)
    GPIO.cleanup()
    try:
        client.close()
    except:
        pass
    print("[INFO] Cleanup complete. Exiting.")
    os._exit(1)

error_count = 0                # Counter for consecutive errors, (start at 0)
def read_socket_line():
    """Read a line from the socket with proper error handling."""
    global error_count, client
    try:
        data = client.recv(1024).decode().strip()
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

# If connection fails, retry connection and send data
def send_with_retry(data, max_retries=3):
    global error_count, client
    for attempt in range(max_retries):
        try:
            client.sendall(data)
            error_count = 0  # Reset error count on successful send
            return True
        except Exception as e:
            error_count += 1
            if error_count >= MAX_CONSECUTIVE_ERRORS:
                print(f"[FATAL] Too many consecutive errors ({error_count}). Exiting program.")
                cleanup_and_exit()
            print(f"[ERROR] Send attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait before retry
    return False

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

################################## MAIN LOOP ##################################
should_exit = False

def data_collection_loop(run_index):
    global client, should_exit
    # Lead-in is already done
    # Wait for 'trigger' from host
    while True:
        msg = read_socket_line()
        if msg is None:
            continue
        if msg.lower() == "trigger":
            print("[INFO] Received 'trigger' from host. Starting data collection.")
            break
        elif msg.lower() == "stop":
            print("[INFO] Received stop command from host during handshake. Exiting.")
            should_exit = True
            return

    # Main data collection loop
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
            # When the SMA pulse is triggered (right after setting sma_active = True):
            pulse_start_msg = f"pulse_start_ts:{time.time()}"
            send_with_retry((pulse_start_msg + "\n").encode())

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

            packet = {
                "run_index": run_index + 1,
                "timestamp": now,  # Send Unix timestamp
                "temperatures_C": temps,
                "sma_active": sma_active
            }
            # Debugging messages for packet handling
            try:
                if DEBUG:
                    print("[DEBUG] Sending packet...")
                if not send_with_retry((json.dumps(packet) + '\n').encode()):
                    print("[ERROR] Failed to send packet after retries")
                    should_exit = True
                    break
                if DEBUG:
                    print(f"[INFO] Sent: {packet}")
            except Exception as e:
                print(f"[ERROR] Failed to send packet to host: {e}")
                should_exit = True
                break

            last_sample_time += SEND_INTERVAL
            sleep_time = last_sample_time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

        # Stop after run_time seconds
        if elapsed > RUN_TIME:
            GPIO.output(SMA_GPIO_PIN, GPIO.LOW)
            break

# Handle sync request from host
def handle_sync():
    try:
        # Send current Unix timestamp
        sync_time = time.time()
        client.sendall(f"sync_ts:{sync_time}\n".encode())
        print(f"[INFO] Sent sync timestamp to host: {sync_time} at {time.time()}")
    except Exception as e:
        print(f"[ERROR] Failed to send sync timestamp: {e}")

try:
    print("[INFO] Waiting for 'start dc' or 'stop' commands from host...")
    run_index = 0
    while run_index < NUM_RUNS:
        msg = client.recv(1024).decode().strip()
        if msg.lower() == "start dc":
            print(f"[INFO] Starting data collection run {run_index + 1}...")
            # Send 'ready' to host immediately
            client.sendall(b"ready\n")
            print("[INFO] Sent 'ready' to host. Waiting for 'sync' for pre-match...")
            # Now wait for 'sync' from host for pre-match
            try:
                client.settimeout(10)  # 10 second timeout for sync
                sync_msg = client.recv(1024).decode().strip()
                if sync_msg.lower() == "sync":
                    print("[INFO] Received 'sync' from host. Syncing clocks and sending timestamp...")
                    handle_sync()
                elif sync_msg.lower() == "stop":
                    print("[INFO] Received stop command from host during pre-match. Exiting.")
                    should_exit = True
                    break
                else:
                    print(f"[WARN] Received unexpected message from host during pre-match sync: {sync_msg}")
            except socket.timeout:
                print("[WARN] Timeout waiting for 'sync' from host. Check host connection or sync logic.")
            finally:
                client.settimeout(None)  # Reset timeout

            # Continue with lead-in and data collection as before
            print(f"[INFO] Lead-in: waiting {LEAD_TIME} seconds before starting run {run_index + 1}...")
            lead_start = time.time()
            while time.time() - lead_start < LEAD_TIME:
                time.sleep(0.05)
            print(f"[INFO] Lead-in complete. Waiting for 'trigger' from host...")
            data_collection_loop(run_index)
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
