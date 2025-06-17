import cv2
import numpy as np

# === CONFIG ===
onnx_path = "runs/train/your_model/weights/best.onnx"
input_size = 640
conf_threshold = 0.4
nms_threshold = 0.5
class_names = ["white_ball"]

# === Load Model ===
net = cv2.dnn.readNetFromONNX(onnx_path)

# === Open Webcam ===
cap = cv2.VideoCapture(1)  # Use 0 for default camera

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Resize and prepare blob
    blob = cv2.dnn.blobFromImage(frame, 1/255.0, (input_size, input_size), swapRB=True, crop=False)
    net.setInput(blob)
    outputs = net.forward()[0]  # Shape: [num_boxes, 85]

    # Post-process predictions
    boxes, confidences, class_ids = [], [], []

    rows = outputs.shape[0]
    frame_h, frame_w = frame.shape[:2]

    for i in range(rows):
        row = outputs[i]
        conf = row[4]
        if conf >= conf_threshold:
            class_scores = row[5:]
            class_id = np.argmax(class_scores)
            score = class_scores[class_id]

            if score > conf_threshold:
                cx, cy, w, h = row[0:4]
                x = int((cx - w/2) * frame_w / input_size)
                y = int((cy - h/2) * frame_h / input_size)
                width = int(w * frame_w / input_size)
                height = int(h * frame_h / input_size)

                boxes.append([x, y, width, height])
                confidences.append(float(score))
                class_ids.append(class_id)

    # Apply Non-Maximum Suppression
    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

    for i in indices:
        i = i[0] if isinstance(i, (tuple, list, np.ndarray)) else i
        box = boxes[i]
        x, y, w, h = box
        label = f"{class_names[class_ids[i]]} {confidences[i]:.2f}"

        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Show result
    cv2.imshow("YOLOv5 Real-Time Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
