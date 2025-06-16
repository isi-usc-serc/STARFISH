import cv2
import time
import os

# Parameters
output_dir = "captured_frames/set3"
fps = 1  # capture rate in Hz
delay = 1.0 / fps

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Initialize camera
cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

if not cap.isOpened():
    print("Error: Cannot open camera.")
    exit()

frame_count = 0
last_capture_time = time.time()

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # Show the current frame
        cv2.imshow('Camera Viewer (press q to quit)', frame)

        # Check if it's time to capture a frame
        current_time = time.time()
        if current_time - last_capture_time >= delay:
            filename = os.path.join(output_dir, f"frame_{frame_count:04d}.jpg")
            cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, 100])
            print(f"Saved {filename}")
            frame_count += 1
            last_capture_time = current_time

        # Break loop when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Capture stopped by user.")
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
