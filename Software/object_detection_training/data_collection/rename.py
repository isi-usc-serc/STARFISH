import os

# Set the path to the directory containing your files
directory = './training_images/set2/'

# Loop through all files in the directory
for filename in os.listdir(directory):
    # Split the name and extension
    name, ext = os.path.splitext(filename)

    # Construct the new filename
    new_name = f"{name}_set2{ext}"

    # Build full paths
    src = os.path.join(directory, filename)
    dst = os.path.join(directory, new_name)

    # Rename the file
    os.rename(src, dst)
    print(f"Renamed: {filename} -> {new_name}")
