import cv2
import numpy as np
import glob

# Define checkerboard dimensions
CHECKERBOARD = (7, 7)  # Adjust based on your calibration board
square_size = 25.4  # Size of a square in mm (change accordingly)

# Prepare object points
objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2) * square_size

# Arrays to store object points and image points
objpoints = []  # 3D points
imgpoints = []  # 2D points

# Load all checkerboard images
images = glob.glob("calibration_images/*.*")  # Gets all image files
print("All image files:", images)



for fname in images:
    img = cv2.imread(fname)
    if img is None:
        print(f"Failed to load {fname}")
        continue

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)
    
    if ret:
        print(f"Checkerboard detected in {fname}")
        objpoints.append(objp)
        imgpoints.append(corners)
    else:
        print(f"Failed to detect checkerboard in {fname}")


cv2.destroyAllWindows()

if len(objpoints) == 0 or len(imgpoints) == 0:
    print("No valid checkerboard images found! Exiting.")
    exit()

ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
    objpoints, imgpoints, gray.shape[::-1], None, None
)


# Calibrate camera
ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

# Save calibration results
np.savez("camera_calibration.npz", camera_matrix=camera_matrix, dist_coeffs=dist_coeffs)

print("Camera Matrix:\n", camera_matrix)
print("Distortion Coefficients:\n", dist_coeffs)
