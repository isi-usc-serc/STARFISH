""" 
(Pi) Client program: Thermocouple Data Collection & SMA Control

This script will import configuration settings from the control program (PC), 
listen for startup commands, control the thermocouple data collection 
and SMA power pulse, and send the data along with timestamp info for the Host 
program.

"""

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
sys.path.append('/home/Leapfrog/STARFISH/Thermal/daqhats_stuff/examples/python/mcc134')

from daqhats_utils import select_hat_device

################################ CONFIGURATION ################################
PC_IP = '192.168.0.106'  # Update with current Host PC's IP address
PC_PORT = 5005

SMA_GPIO_PIN = 18

################################## SETUP ######################################
# GPIO Setup
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

# Receive Configuration From Host
config = json.loads(client.recv(1024).decode())
print(f"[INFO] Received config: {config}")

TC_CHANNELS = config.get("channels", [0])                # default: [0]
SMA_PULSE_DURATION = config.get("pulse_duration", 1.0)   # default: 1.0 sec
SEND_INTERVAL = config.get("send_interval", 0.25)        # default: 0.25 sec
TC_TYPE = getattr(TcTypes, f"TYPE_{config.get('tc_type', 'J')}")

for ch in TC_CHANNELS:
    hat.tc_type_write(ch, TC_TYPE)

# Wait for "start dc" command
while True:
    msg = client.recv(1024).decode().strip()
    if msg.lower() == "start dc":
        print("[INFO] Starting data collection loop")
        break

################################## MAIN LOOP ##################################

try:
    sma_active = True
    pulse_start_time = time.time()
    last_sample_time = 0

    # Begin SMA pulse
    GPIO.output(SMA_GPIO_PIN, GPIO.HIGH)

    while True:
        now = time.time()

        # End SMA pulse after configured duration
        if sma_active and (now - pulse_start_time >= SMA_PULSE_DURATION):
            GPIO.output(SMA_GPIO_PIN, GPIO.LOW)
            sma_active = False

        # Sample temperature and send to host at fixed interval
        if now - last_sample_time >= SEND_INTERVAL:
            last_sample_time = now

            temps = {}
            for ch in TC_CHANNELS:
                value = hat.t_in_read(ch)
                temps[f"ch{ch}"] = round(value, 2)

            timestamp = datetime.datetime.utcnow().isoformat() + "Z"

            packet = {
                "timestamp": timestamp,
                "temperatures_C": temps,
                "sma_active": sma_active
            }

            client.sendall(json.dumps(packet).encode())
            print(f"[INFO] Sent: {packet}")

        time.sleep(0.01)  # Prevent maxing out CPU

except KeyboardInterrupt:
    print("\n[INFO] Stopping script.")

finally:
    GPIO.output(SMA_GPIO_PIN, GPIO.LOW)
    GPIO.cleanup()
    client.close()