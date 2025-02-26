import cv2
import numpy as np

# Initialize video capture
cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)  # Adjust width
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)  # Adjust height

if not cap.isOpened():
    print("Error: Could not open the webcam.")
    exit()

# Function to detect SOLID circular markers
def detect_markers(frame, min_radius=4, max_radius=25):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply CLAHE for better contrast
    clahe = cv2.createCLAHE(clipLimit=2, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)

    # Apply Median Blur to reduce noise while keeping edges
    blurred = cv2.medianBlur(enhanced_gray, 5)

    # Canny Edge Detection
    edges = cv2.Canny(blurred, 50, 150) # Lower and upper thresholds

    # **Use Otsu's Thresholding Instead of Adaptive Thresholding**
    _, binary = cv2.threshold(edges, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # binary = cv2.bitwise_not(binary)

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
        if .7 < circularity < 1.2 and area > 40:
            (x, y), radius = cv2.minEnclosingCircle(cnt)
            radius = int(radius)
            if min_radius <= radius <= max_radius:
                detected_circles.append((int(x), int(y), radius))

    return detected_circles, binary

# Dictionary to store multiple trackers
trackers = {}
max_markers = 8  # Max number of circles to track
distance_threshold = 20  # Minimum distance to consider a new marker

# Function to check if a detected marker is already tracked
def is_duplicate_marker(new_x, new_y, existing_trackers, threshold=20):
    for marker_id, (tracker, last_seen, center) in trackers.items():
        tracked_x, tracked_y = center
        distance = np.sqrt((new_x - tracked_x) ** 2 + (new_y - tracked_y) ** 2)
        if distance < threshold:
            return marker_id  # Return existing marker ID if it's a duplicate
    return None  # If not found, it's a new marker

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame from webcam.")
        break

    # Detect markers using contrast-based method
    circles, binary = detect_markers(frame)

    # Update existing trackers
    to_remove = []  # List of lost trackers
    for marker_id, (tracker, last_seen, center) in trackers.items():
        success, box = tracker.update(frame)
        if success:
            x, y, w, h = [int(v) for v in box]
            new_center = (x + w // 2, y + h // 2)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Draw tracking box
            coord_text = f"({new_center[0]}, {new_center[1]})"
            cv2.putText(frame, coord_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.5, (0, 255, 0), 1)
            trackers[marker_id] = (tracker, 0, new_center)  # Reset lost count and update center
        else:
            trackers[marker_id] = (tracker, last_seen + 1, center)
            if last_seen > 10:  # Allow buffer before removal
                to_remove.append(marker_id)

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
            frame_height, frame_width = frame.shape[:2]
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
    cv2.imshow('Multi-Marker Tracking', frame)
    cv2.imshow('Binary Mask', binary)  # **Should now clearly separate markers from background**

    if cv2.waitKey(10) & 0xFF == ord('q'):  # Adjusted wait time for better tracking
        break

cap.release()
cv2.destroyAllWindows()