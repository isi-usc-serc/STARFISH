import cv2
import numpy as np

# Initialize video capture
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open the webcam.")
    exit()

# Function to detect multiple markers
def detect_markers(frame, min_radius=7, max_radius=20):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Apply CLAHE for contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)
    
    # Apply Gaussian Blur
    blurred = cv2.GaussianBlur(enhanced_gray, (15, 15), 0)
    
    # Adaptive Thresholding
    binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    
    # Detect circles
    circles = cv2.HoughCircles(binary, cv2.HOUGH_GRADIENT, dp=1.2, minDist=30,
                               param1=60, param2=35, minRadius=min_radius, maxRadius=max_radius)
    
    return circles

# Dictionary to store multiple trackers
trackers = {}
max_markers = 16  # Max number of circles to track
distance_threshold = 20  # Minimum distance to consider a new marker

# Function to check if a detected marker is already tracked
def is_duplicate_marker(new_x, new_y, existing_trackers, threshold=20):
    for marker_id, (tracker, last_seen, center) in existing_trackers.items():
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

    # Update existing trackers
    to_remove = []  # List of lost trackers
    for marker_id, (tracker, last_seen, center) in trackers.items():
        success, box = tracker.update(frame)
        if success:
            x, y, w, h = [int(v) for v in box]
            new_center = (x + w // 2, y + h // 2)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Draw tracking box
            # Add coordinates text
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
    if len(trackers) < max_markers:
        circles = detect_markers(frame)

        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i, (x, y, r) in enumerate(circles[0, :]):
                if len(trackers) >= max_markers:
                    break  # Stop if max markers reached

                # Check if this marker is already being tracked
                existing_marker = is_duplicate_marker(x, y, trackers, distance_threshold)

                if existing_marker:
                    continue  # Skip adding duplicate markers

                # Expand bounding box slightly for stability
                bbox = (x - r - 5, y - r - 5, 2 * r + 10, 2 * r + 10)

                # Use CSRT tracker for more robust tracking
                tracker = cv2.TrackerCSRT_create()
                tracker.init(frame, bbox)

                # Store tracker with unique ID
                trackers[f"marker_{i}"] = (tracker, 0, (x, y))

                # Draw detected circle and coordinates
                cv2.circle(frame, (x, y), r, (255, 0, 0), 3)
                cv2.circle(frame, (x, y), 2, (0, 0, 255), 3)
                coord_text = f"({x}, {y})"
                cv2.putText(frame, coord_text, (x, y - r - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.5, (255, 0, 0), 1)

    # Display output
    cv2.imshow('Multi-Marker Tracking', frame)

    if cv2.waitKey(10) & 0xFF == ord('q'):  # Adjusted wait time for better tracking
        break

cap.release()
cv2.destroyAllWindows()