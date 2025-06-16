import os, shutil, random

all_images = [f for f in os.listdir("captured_frames/*") if f.endswith(".jpg")]
random.shuffle(all_images)

train_split = int(len(all_images) * 0.8)
train_files = all_images[:train_split]
val_files = all_images[train_split:]

for subset, files in [("train", train_files), ("val", val_files)]:
    for f in files:
        shutil.copy(f"images/{f}", f"dataset/images/{subset}/{f}")
        label = f.replace(".jpg", ".txt")
        shutil.copy(f"labels/{label}", f"dataset/labels/{subset}/{label}")
