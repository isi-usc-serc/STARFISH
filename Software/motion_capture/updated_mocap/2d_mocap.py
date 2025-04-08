import cv2
import numpy as np
import csv
import time
from datetime import datetime
import os

# Dictionary to store multiple trackers
trackers = {}
max_markers = 8  # Max number of circles to track
distance_threshold = 20  # Minimum distance to consider a new marker

# Ensure data_output directory exists
os.makedirs('data_output', exist_ok=True)

# Create CSV file with headers
csv_filename = os.path.join('data_output', f"marker_positions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
csv_file = open(csv_filename, 'w', newline='')
csv_writer = csv.writer(csv_file)
# Write headers - Time + columns for each marker's x,y coordinates
headers = ['Timestamp']
for i in range(max_markers):
    headers.extend([f'Marker_{i}_X_mm', f'Marker_{i}_Y_mm'])
csv_writer.writerow(headers)

# Load calibration data for camera distortion and pixel-mm conversion
calib_data = np.load("camera_calibration.npz")
camera_matrix = calib_data["camera_matrix"]
dist_coeffs = calib_data["dist_coeffs"]

# Real-world width of reference object (checkerboard square)
real_width_mm = 25.4 # 1 in. square

# Real-world offsets from edge of image to the bracket
v_start = 115+60  # vertical distance from top of image to corner of 80-20 in px
v_adj = 137+30  # vertical distance from bottom of image to corner of 80-20 in px
h_start = 173+30 # horizontal distance from top of image to corner of 80-20 in px
h_adj = 155+30 # horizontal distance from bottom of image to corner of 80-20 in px

# Function to detect SOLID circular markers
def detect_markers(frame, min_radius=5, max_radius=25):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply CLAHE for better contrast
    clahe = cv2.createCLAHE(clipLimit=1, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)

    # Apply Median Blur to reduce noise while keeping edges
    blurred = cv2.medianBlur(enhanced_gray, 5)

    # Canny Edge Detection
    edges = cv2.Canny(blurred, 200, 255) # Lower and upper thresholds

    # **Use Otsu's Thresholding Instead of Adaptive Thresholding**
    _, binary = cv2.threshold(edges, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # binary = cv2.bitwise_not(binary)

    #dilation to close gaps
    kernel = np.ones((3,3), np.uint8)
    kernel1 = np.ones((4,4), np.uint8)
    kernel2 = np.ones((2,2), np.uint8)
    binary = cv2.dilate(binary,kernel1,iterations=2) # DEFAULT: 2
    binary = cv2.erode(binary,kernel2,iterations=3) # DEFAULT: 3
    # binary = cv2.dilate(binary,kernel1,iterations=1) # Not in original
    # binary = cv2.erode(binary,kernel2,iterations=4) # Not in original
    # binary = cv2.dilate(binary,kernel1,iterations=1) # Not in original
    # binary = cv2.erode(binary,kernel2,iterations=1) # Not in original



    # **Find contours instead of using HoughCircles**
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detected_circles = []
    for cnt in contours:
        perimeter = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * perimeter, True)

        # Compute circularity (roundness measure)
        area = cv2.contourArea(cnt)
        if perimeter == 0:
            continue
        circularity = 4 * np.pi * (area / (perimeter ** 2))  # Close to 1 for perfect circles

        # Filter out non-circular and small/large objects
        if .7 < circularity < 1.2 and area > 40:  # Reverted to original values
            (x, y), radius = cv2.minEnclosingCircle(cnt)
            radius = int(radius)
            if min_radius <= radius <= max_radius:
                detected_circles.append((int(x), int(y), radius))

    return detected_circles, binary

# Function to check if a detected marker is already tracked
def is_duplicate_marker(new_x, new_y, existing_trackers, threshold=20):
    for marker_id, (tracker, last_seen, center) in trackers.items():
        tracked_x, tracked_y = center
        distance = np.sqrt((new_x - tracked_x) ** 2 + (new_y - tracked_y) ** 2)
        if distance < threshold:
            return marker_id  # Return existing marker ID if it's a duplicate
    return None  # If not found, it's a new marker

imgcount =0

# Initialize video capture
cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)  # Adjust width
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)  # Adjust height

if not cap.isOpened():
    print("Error: Could not open the webcam.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame from webcam.")
        break
    

    # Undistort the camera frame
    frame_height, frame_width = frame.shape[:2]

    new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(camera_matrix, dist_coeffs, (frame_width, frame_height), 1, (frame_width, frame_height)) # Generates new camera matrix
    uframe = cv2.undistort(frame, camera_matrix, dist_coeffs, None, new_camera_matrix) # Undistorts the camera
    frame = uframe[v_start:1080-v_adj, h_start:1920-h_adj] # cropping frame to remove unecessary parts of image

    if imgcount == 0:
        imgcount += 1
        cv2.imwrite("test_frame.jpg",frame)

    # Conversion from pixels to real units
    pixel_width = 29; # Measured pixel width of the checkerboard square. Taken using undistorted camera image and processed using ImageJ
    pixel_to_mm = real_width_mm / pixel_width # keeping as int for simplicity
    # real_object_width = pixel_width * scale | multiply x,y coords by scale to get real world value in mm
    # For reference, top left corner is 0,0 px and 0,0 mm
    # Moving right is increase in +x-direction
    # Moving down is increase in +y-direction

    # Detect markers using contrast-based method
    circles, binary = detect_markers(frame)

    # Update existing trackers
    to_remove = []  # List of lost trackers
    
    # Prepare row data for CSV
    csv_row = [datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')]
    marker_positions = {i: None for i in range(max_markers)}  # Initialize all positions as None
    
    for marker_id, (tracker, last_seen, center) in trackers.items():
        success, box = tracker.update(frame)
        if success:
            x, y, w, h = [int(v) for v in box]
            new_center = (x + w // 2, y + h // 2)
            adj_center = (int(new_center[0] * pixel_to_mm), int(new_center[1] * pixel_to_mm))
            
            # Store position for CSV
            marker_num = int(marker_id.split('_')[1])  # Extract marker number from ID
            marker_positions[marker_num] = adj_center
            
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Draw tracking box
            coord_text = f"({adj_center[0]} mm, {adj_center[1]} mm)"
            cv2.putText(frame, coord_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.5, (0, 255, 0), 1)
            trackers[marker_id] = (tracker, 0, new_center)  # Reset lost count and update center
        else:
            trackers[marker_id] = (tracker, last_seen + 1, center)
            if last_seen > 10:  # Allow buffer before removal
                to_remove.append(marker_id)
    
    # Write positions to CSV
    for i in range(max_markers):
        if marker_positions[i] is not None:
            csv_row.extend([marker_positions[i][0], marker_positions[i][1]])
        else:
            csv_row.extend(['', ''])  # Empty values for missing markers
    csv_writer.writerow(csv_row)
    
    # Remove lost trackers
    for marker_id in to_remove:
        del trackers[marker_id]

    # Detect new markers if needed
    if len(trackers) < max_markers and circles:
        for i, (x, y, r) in enumerate(circles):
            if len(trackers) >= max_markers:
                break  # Stop if max markers reached

            # Check if this marker is already being tracked
            existing_marker = is_duplicate_marker(x, y, trackers, distance_threshold)

            if existing_marker:
                continue  # Skip adding duplicate markers

            # Expand bounding box slightly for stability
            
            x_min = max(0, x - r - 5)
            y_min = max(0, y - r - 5)
            width = min(frame_width - x_min, 2 * r + 10)
            height = min(frame_height - y_min, 2 * r + 10)

            bbox = (x_min, y_min, width, height)

            # Use CSRT tracker for more robust tracking
            tracker = cv2.TrackerCSRT.create()
            tracker.init(frame, bbox)

            # Store tracker with unique ID
            trackers[f"marker_{i}"] = (tracker, 0, (x, y))

            # Draw detected circle and coordinates
            cv2.circle(frame, (x, y), r, (255, 0, 0), 3)
            cv2.circle(frame, (x, y), 2, (0, 0, 255), 3)
            coord_text = f"({x}, {y})"
            cv2.putText(frame, coord_text, (x, y - r - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.5, (255, 0, 0), 1)

    # Debugging visualizations
    cv2.imshow('Binary Mask', binary)  # **Should now clearly separate markers from background**
    cv2.imshow('Multi-Marker Tracking', frame)

    if cv2.waitKey(10) & 0xFF == ord('q'):  # Adjusted wait time for better tracking
        break

cap.release()
cv2.destroyAllWindows()
csv_file.close()  # Close the CSV file
print(f"Marker positions have been saved to {csv_filename}")