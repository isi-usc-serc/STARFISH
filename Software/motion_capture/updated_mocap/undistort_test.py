import cv2
import numpy as np

# Load calibration data
calib_data = np.load("camera_calibration.npz")
camera_matrix = calib_data["camera_matrix"]
dist_coeffs = calib_data["dist_coeffs"]

# Known real-world width of reference object (e.g., checkerboard square, coin, card)
real_width_mm = 50  # Adjust based on your reference object

# Open camera
cap = cv2.VideoCapture(1)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]

    # Undistort the frame first
    new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(camera_matrix, dist_coeffs, (w, h), 1, (w, h))
    undistorted_frame = cv2.undistort(frame, camera_matrix, dist_coeffs, None, new_camera_matrix)

    # Convert to grayscale for object detection
    gray = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)  # Get bounding box

        # Ignore small noise
        if w > 30 and h > 30:
            pixel_width = w  # Width in pixels

            # Compute real-world scale (mm per pixel)
            scale = real_width_mm / pixel_width
            real_object_width = pixel_width * scale  # Convert detected width to mm

            # Display scale and size on the frame
            cv2.rectangle(undistorted_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(undistorted_frame, f"Scale: {scale:.2f} mm/pixel", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            cv2.putText(undistorted_frame, f"Width: {real_object_width:.2f} mm", (x, y + h + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    # Show the undistorted frame with measurements
    cv2.imshow("Undistorted & Scaled Tracking", undistorted_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
