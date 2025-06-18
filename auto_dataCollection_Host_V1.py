import socket
from datetime import datetime

# After sending config and 'start dc', wait for 'ready' from Pi
logger.info("Waiting for 'ready' from Pi...")
client_socket.settimeout(5)  # Set a 5-second timeout
try:
    response = client_socket.recv(1024).decode().strip()
    if response != "ready":
        logger.error(f"Expected 'ready' from Pi, got: {response}")
        raise RuntimeError("Handshake failed: Pi did not send 'ready'")
except socket.timeout:
    logger.error("Timeout waiting for 'ready' from Pi")
    raise RuntimeError("Handshake failed: Pi did not respond in time")

# Send 'sync' to Pi
logger.info("Sending 'sync' to Pi...")
client_socket.sendall("sync".encode())

# Wait for Pi's timestamp response
logger.info("Waiting for Pi's timestamp...")
try:
    pi_timestamp_str = client_socket.recv(1024).decode().strip()
    pi_timestamp = datetime.fromisoformat(pi_timestamp_str)
    logger.info(f"Received Pi timestamp: {pi_timestamp}")
except socket.timeout:
    logger.error("Timeout waiting for Pi's timestamp")
    raise RuntimeError("Handshake failed: Pi did not send timestamp in time")

# Calculate clock offset
host_timestamp = datetime.now()
clock_offset = (host_timestamp - pi_timestamp).total_seconds()
logger.info(f"Calculated clock offset: {clock_offset:.6f} seconds")

# Send 'trigger' to Pi
logger.info("Sending 'trigger' to Pi...")
client_socket.sendall("trigger".encode())

# Now start reading data packets
logger.info("Starting data collection...") 