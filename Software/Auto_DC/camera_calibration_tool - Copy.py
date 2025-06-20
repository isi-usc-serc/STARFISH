# """
# This program will track a calibration target, and calculate the pixeles per milimeter 
# using the selected camera. 
# 
# The script will also calibrate the image recognition logic.
#
# All calibration data is stored as a text file, and imported by the host dataCollection
# program automatically.
#
# Created on Wed Jun 11 17:33:49 2025
#
# @author: BillyChrist
# """
 

import cv2
import numpy as np
import os

############# Calibration Parameters (edit these as needed) ###############
GRID_SIZE_MM         = 25.0     # Size of one grid square in mm
GRID_TO_SUBJECT_MM   = 56.5     # Height from grid to subject (ball) in mm
SUBJECT_SIZE_MM      = 10.0     # Diameter of the subject (ball) in mm
SUBJECT_TO_CAMERA_MM = 205.0    # Height from top of subject to camera in mm

# HSV Color Presets (moved from data collection program)
# TODO: Add support for multiple balls - currently only supports one ball type
HSV_PRESETS = {
    "red_ball": {
        "hue_range": (0, 10),      # Red wraps around 0-10 and 170-180
        "saturation_range": (100, 255),
        "value_range": (50, 255),
        "hue_margin": 5,           # Tunable margin for hue
        "saturation_margin": 20,   # Tunable margin for saturation  
        "value_margin": 30         # Tunable margin for value
    }
    # TODO: Add more ball colors here:
    # "blue_ball": { ... },
    # "green_ball": { ... },
    # etc.
}

# Default ball type to use
DEFAULT_BALL_TYPE = "red_ball"

CALIB_DIR = os.path.join(os.path.dirname(__file__), "calibration_data")
if not os.path.exists(CALIB_DIR):
    os.makedirs(CALIB_DIR)

########################### Camera detection ##############################
def detect_cameras(max_cams=5):
    available = []
    for i in range(max_cams):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available.append(i)
            cap.release()
    return available

#################### Mouse callback for point selection ###################
clicked_points = []
def click_event(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        clicked_points.append((x, y))
        print(f"Clicked: ({x}, {y})")

#################### Mouse callback for rectangle selection ###############
rect_start = None
rect_end = None
rect_done = False
def rect_event(event, x, y, flags, param):
    global rect_start, rect_end, rect_done
    if event == cv2.EVENT_LBUTTONDOWN:
        rect_start = (x, y)
        rect_end = (x, y)
        rect_done = False
    elif event == cv2.EVENT_MOUSEMOVE and rect_start is not None:
        rect_end = (x, y)
    elif event == cv2.EVENT_LBUTTONUP:
        rect_end = (x, y)
        rect_done = True

######################## Main calibration logic ###########################
def main():
    print("[INFO] Detecting available cameras...")
    cams = detect_cameras()
    if not cams:
        print("[ERROR] No cameras detected.")
        return
    print(f"[INFO] Available cameras: {cams}")
    cam_id = int(input(f"Select camera ID from {cams}: "))

    # Check if calibration file exists and load existing data
    calib_path = os.path.join(CALIB_DIR, "calibration_data.txt")
    existing_data = {}
    if os.path.exists(calib_path):
        print("[INFO] Existing calibration file found. Loading existing data...")
        with open(calib_path, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    existing_data[key.strip()] = value.strip()
        print(f"[INFO] Loaded existing data: {list(existing_data.keys())}")
    else:
        print("[INFO] No existing calibration file found. Starting fresh calibration.")

    # Initialize data variables with existing values or defaults
    pixels_per_mm_grid = float(existing_data.get("pixels_per_mm_grid", 0))
    pixels_per_mm_ball = float(existing_data.get("pixels_per_mm_ball", 0))
    grid_to_camera = float(existing_data.get("grid_to_camera_mm", SUBJECT_TO_CAMERA_MM + SUBJECT_SIZE_MM + GRID_TO_SUBJECT_MM))
    ball_to_camera = float(existing_data.get("ball_to_camera_mm", SUBJECT_TO_CAMERA_MM + (SUBJECT_SIZE_MM / 2)))
    
    # Load existing templates if available
    templates = []
    template_filenames = []
    if "template_files" in existing_data:
        existing_templates = existing_data["template_files"].split(",")
        for template_name in existing_templates:
            template_name = template_name.strip()
            template_path = os.path.join(CALIB_DIR, template_name)
            if os.path.exists(template_path):
                template = cv2.imread(template_path)
                if template is not None:
                    templates.append(template)
                    template_filenames.append(template_path)
                    print(f"[INFO] Loaded existing template: {template_name}")
    
    # Also check for template files that might exist but not be in the calibration data
    if not templates:
        print("[INFO] No templates found in calibration data, checking for existing template files...")
        for i in range(1, 10):  # Check for template_1.png through template_9.png
            template_name = f"template_{i}.png"
            template_path = os.path.join(CALIB_DIR, template_name)
            if os.path.exists(template_path):
                template = cv2.imread(template_path)
                if template is not None:
                    templates.append(template)
                    template_filenames.append(template_path)
                    print(f"[INFO] Found existing template file: {template_name}")
    
    print(f"[INFO] Found {len(templates)} existing templates.")

    # Check if we have existing pixels/mm data and offer to skip calibration
    if pixels_per_mm_grid > 0 and pixels_per_mm_ball > 0:
        print(f"[INFO] Found existing pixels/mm data: grid={pixels_per_mm_grid:.4f}, ball={pixels_per_mm_ball:.4f}")
        print("[INFO] Enter 'c' to calibrate pixels per mm, or 's' to skip (use existing data).")
        mode = input("Enter mode (c/s): ").strip().lower()
        if mode == 's':
            print("[INFO] Skipping pixels per mm calibration. Using existing data.")
            # Skip to template training
        else:
            print("[INFO] Proceeding with pixels per mm calibration.")
            # Continue with calibration
    else:
        print("[INFO] No existing pixels/mm data found. Proceeding with calibration.")
        mode = 'c'

    if mode == 'c':
        cap = cv2.VideoCapture(cam_id)
        if not cap.isOpened():
            print(f"[ERROR] Could not open camera {cam_id}")
            return

        print("[INFO] Press SPACE to capture a frame for calibration.")
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to grab frame.")
                break
            cv2.imshow("Live Feed - Press SPACE to capture", frame)
            key = cv2.waitKey(1)
            if key == 32:  # SPACE
                calib_img = frame.copy()
                break
            elif key == 27:  # ESC
                print("[INFO] Calibration cancelled.")
                cap.release()
                cv2.destroyAllWindows()
                return
        cap.release()
        cv2.destroyAllWindows()

        print("[INFO] Click two points on the calibration image (e.g., across known grid squares). Press ESC when done.")
        global clicked_points
        clicked_points = []
        cv2.imshow("Calibration Image - Click Two Points", calib_img)
        cv2.setMouseCallback("Calibration Image - Click Two Points", click_event)
        while len(clicked_points) < 2:
            cv2.waitKey(1)
        cv2.destroyAllWindows()

        pt1, pt2 = clicked_points[:2]
        pixel_dist = np.linalg.norm(np.array(pt1) - np.array(pt2))
        print(f"[INFO] Pixel distance between points: {pixel_dist:.2f}")

        num_squares = float(input("Enter number of grid squares between points: "))
        real_dist_mm = num_squares * GRID_SIZE_MM
        pixels_per_mm_grid = pixel_dist / real_dist_mm
        print(f"[INFO] Pixels per mm at grid height: {pixels_per_mm_grid:.4f}")

        # Use parameters for heights
        grid_to_camera = SUBJECT_TO_CAMERA_MM + SUBJECT_SIZE_MM + GRID_TO_SUBJECT_MM
        ball_to_camera = SUBJECT_TO_CAMERA_MM + (SUBJECT_SIZE_MM / 2)
        print(f"[INFO] grid_to_camera_mm = {grid_to_camera:.2f}")
        print(f"[INFO] ball_to_camera_mm = {ball_to_camera:.2f}")

        pixels_per_mm_ball = pixels_per_mm_grid * (grid_to_camera / ball_to_camera)
        print(f"[INFO] Pixels per mm at ball height: {pixels_per_mm_ball:.4f}")

        # Save to file
        with open(calib_path, "w") as f:
            f.write(f"pixels_per_mm_grid = {pixels_per_mm_grid:.6f}\n")
            f.write(f"pixels_per_mm_ball = {pixels_per_mm_ball:.6f}\n")
            f.write(f"grid_to_camera_mm = {grid_to_camera:.2f}\n")
            f.write(f"ball_to_camera_mm = {ball_to_camera:.2f}\n")
            f.write(f"calibration_points = {pt1}, {pt2}\n")
            f.write(f"real_dist_mm = {real_dist_mm:.2f}\n")
            f.write(f"num_squares = {num_squares}\n")
            f.write(f"camera_id = {cam_id}\n")
        print(f"[INFO] Calibration data saved to {calib_path}")

    ###################### Template Matching Training #####################
    print("[INFO] Enter 't' to train templates (draw box around ball), or 's' to skip.")
    mode = input("Enter mode (t/s): ").strip().lower()
    if mode == 't':
        # Clear existing templates
        templates = []
        template_filenames = []
        
        cap = cv2.VideoCapture(cam_id)
        for i in range(3):
            print(f"[INFO] Training template {i+1}/3. Press SPACE to freeze frame.")
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("[ERROR] Failed to grab frame.")
                    break
                disp = frame.copy()
                cv2.imshow("Draw box around ball - Press SPACE to freeze", disp)
                key = cv2.waitKey(1)
                if key == 32:  # SPACE
                    frozen = frame.copy()
                    break
                elif key == 27:
                    print("[INFO] Training cancelled.")
                    cap.release()
                    cv2.destroyAllWindows()
                    return
            # Draw rectangle
            global rect_start, rect_end, rect_done
            rect_start, rect_end, rect_done = None, None, False
            cv2.imshow("Draw box around ball - Drag mouse", frozen)
            cv2.setMouseCallback("Draw box around ball - Drag mouse", rect_event)
            while not rect_done:
                temp_disp = frozen.copy()
                if rect_start and rect_end:
                    cv2.rectangle(temp_disp, rect_start, rect_end, (0,255,0), 2)
                cv2.imshow("Draw box around ball - Drag mouse", temp_disp)
                if cv2.waitKey(1) == 13:  # ENTER to confirm
                    break
            cv2.destroyAllWindows()
            if rect_start and rect_end:
                x1, y1 = rect_start
                x2, y2 = rect_end
                x_min, x_max = min(x1, x2), max(x1, x2)
                y_min, y_max = min(y1, y2), max(y1, y2)
                template = frozen[y_min:y_max, x_min:x_max].copy()
                templates.append(template)
                # Save template image
                template_filename = os.path.join(CALIB_DIR, f"template_{i+1}.png")
                cv2.imwrite(template_filename, template)
                template_filenames.append(template_filename)
                print(f"[INFO] Template {i+1} captured and saved as {template_filename}.")
        cap.release()
        print(f"[INFO] {len(templates)} templates captured and saved.")
        # Update calibration_data.txt with template filenames
        with open(calib_path, "a") as f:
            f.write(f"template_files = {','.join([os.path.basename(fn) for fn in template_filenames])}\n")
    else:
        print("[INFO] Skipping template training.")

    ###### Combined Color Filtering and Template Matching Detection ######
    if templates:
        print("[INFO] Starting combined color filtering and template matching detection. Press ESC to exit.")
        cap = cv2.VideoCapture(cam_id)
        # HSV red color range (hardcoded - proven to work)
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([179, 255, 255])
        
        # Save HSV ranges to calibration file for host program
        with open(calib_path, "a") as f:
            f.write(f"ball_type = red_ball\n")
            f.write(f"hsv_lower1 = {lower_red1.tolist()}\n")
            f.write(f"hsv_upper1 = {upper_red1.tolist()}\n")
            f.write(f"hsv_lower2 = {lower_red2.tolist()}\n")
            f.write(f"hsv_upper2 = {upper_red2.tolist()}\n")
        print("[INFO] HSV color ranges saved to calibration file.")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask = cv2.bitwise_or(mask1, mask2)
            # Morphological operations to clean up the mask
            kernel = np.ones((5,5), np.uint8)
            mask = cv2.erode(mask, kernel, iterations=1)
            mask = cv2.dilate(mask, kernel, iterations=2)
            # Find contours (blobs = connected regions of pixels)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            best_val = -1
            best_loc = None
            best_temp = None
            best_rect = None
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if w < 10 or h < 10:
                    continue  # Ignore tiny blobs
                roi = frame[y:y+h, x:x+w]
                for temp in templates:
                    if roi.shape[0] < temp.shape[0] or roi.shape[1] < temp.shape[1]:
                        continue  # Skip if ROI is smaller than template
                    res = cv2.matchTemplate(roi, temp, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                    if max_val > best_val:
                        best_val = max_val
                        best_loc = (x + max_loc[0], y + max_loc[1])
                        best_temp = temp
                        best_rect = (best_loc, (best_loc[0] + temp.shape[1], best_loc[1] + temp.shape[0]))
            # Draw detection
            out = frame.copy()
            if best_rect is not None:
                cv2.rectangle(out, best_rect[0], best_rect[1], (0,255,0), 2)
                center = (best_rect[0][0] + (best_rect[1][0] - best_rect[0][0])//2,
                          best_rect[0][1] + (best_rect[1][1] - best_rect[0][1])//2)
                cv2.circle(out, center, 5, (0,0,255), -1)
                print(f"[INFO] Detected position: {center}, match score: {best_val:.2f}")
            cv2.imshow("Template+Color Tracking", out)
            cv2.imshow("Red Mask", mask)
            if cv2.waitKey(1) == 27:
                break
        cap.release()
        cv2.destroyAllWindows()
    else:
        print("[INFO] No templates available, skipping detection.")

if __name__ == "__main__":
    main()

