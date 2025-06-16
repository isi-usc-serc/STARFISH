import os
import shutil
import random

# === CONFIGURATION ===
image_dir = "./training_images/complete_set/"
label_dir = "./training_images/labels/"  # Directory where corresponding .txt files live

output_image_dir = "dataset/images"
output_label_dir = "dataset/labels"

train_ratio = 0.8  # 80% training, 20% validation

# === GET IMAGE FILENAMES ===
all_images = [f for f in os.listdir(image_dir) if f.endswith(".jpg")]
random.shuffle(all_images)

# === SPLIT FILENAMES ===
train_split = int(len(all_images) * train_ratio)
train_files = all_images[:train_split]
val_files = all_images[train_split:]

# === CREATE OUTPUT DIRECTORIES IF THEY DON'T EXIST ===
for subset in ["train", "val"]:
    os.makedirs(os.path.join(output_image_dir, subset), exist_ok=True)
    os.makedirs(os.path.join(output_label_dir, subset), exist_ok=True)

# === COPY FILES ===
for subset, files in [("train", train_files), ("val", val_files)]:
    for img_file in files:
        # Copy image
        shutil.copy(
            os.path.join(image_dir, img_file),
            os.path.join(output_image_dir, subset, img_file)
        )

        # Copy corresponding label
        label_file = img_file.replace(".jpg", ".txt")
        label_src = os.path.join(label_dir, label_file)
        label_dst = os.path.join(output_label_dir, subset, label_file)

        if os.path.exists(label_src):
            shutil.copy(label_src, label_dst)
        else:
            print(f"⚠️ Warning: Label not found for {img_file} — expected {label_src}")
