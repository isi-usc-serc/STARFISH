import cv2
import numpy as np
import matplotlib.pyplot as plt

# Function to detect small circular bright spots in a frame
def detect_circular_bright_spots(frame, min_radius=5, max_radius=50):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (11, 11), 0)
    _, binary_image = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    circular_contours = []
    for contour in contours:
        # Fit a minimum enclosing circle
        (x, y), radius = cv2.minEnclosingCircle(contour)
        radius = int(radius)

        if min_radius <= radius <= max_radius:  # Filter by size
            perimeter = cv2.arcLength(contour, True)
            area = cv2.contourArea(contour)

            if perimeter == 0:
                continue  # Avoid division by zero

            # Calculate circularity (1.0 is a perfect circle)
            circularity = 4 * np.pi * (area / (perimeter * perimeter))

            # Ensure contour is circular
            if 0.75 <= circularity <= 1.2:
                circular_contours.append(contour)

    return circular_contours

# Initialize video capture (0 for built-in camera, 1 for USB webcam)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open the webcam.")
    exit()

plt.ion()  # Turn on interactive mode
fig, ax = plt.subplots()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame from the webcam.")
        break

    circular_contours = detect_circular_bright_spots(frame)
    output_frame = frame.copy()
    cv2.drawContours(output_frame, circular_contours, -1, (0, 255, 0), 2)

    ax.clear()
    ax.set_title('Detected Small Circular Bright Spots')
    ax.imshow(cv2.cvtColor(output_frame, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    plt.pause(0.01)  # Pause to update the plot

    # Display the result in a window (optional, for debugging)
    # cv2.imshow('Detected Small Circular Bright Spots', output_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
plt.ioff()
plt.show()
