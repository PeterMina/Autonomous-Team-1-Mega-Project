import os
import shutil
import random

# Define the paths
image_dir = r"D:\ODLC project\Synthetic Data\yolo_data\images"
label_dir = r"D:\ODLC project\Synthetic Data\yolo_data\labels"
output_dir = r"D:\ODLC project\Synthetic Data\yolo_data"

# Create the subdirectories for train, val, and test
for split in ['train', 'val', 'test']:
    os.makedirs(os.path.join(output_dir, split, 'images'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, split, 'labels'), exist_ok=True)

# Define the split ratios
train_ratio = 0.7
val_ratio = 0.15
test_ratio = 0.15

# Get list of image files and corresponding label files
images = sorted([f for f in os.listdir(image_dir) if f.endswith(".jpg")])
labels = sorted([f for f in os.listdir(label_dir) if f.endswith(".txt")])

# Ensure that the number of images matches the number of labels
assert len(images) == len(labels), "Number of images and labels do not match"

# Combine images and labels into pairs
data_pairs = list(zip(images, labels))

# Shuffle the data
random.shuffle(data_pairs)

# Calculate the split indices
num_total = len(data_pairs)
train_end = int(train_ratio * num_total)
val_end = train_end + int(val_ratio * num_total)

# Split the data
train_data = data_pairs[:train_end]
val_data = data_pairs[train_end:val_end]
test_data = data_pairs[val_end:]

# Helper function to move files
def move_files(data_pairs, split):
    for image_file, label_file in data_pairs:
        # Source file paths
        src_img = os.path.join(image_dir, image_file)
        src_label = os.path.join(label_dir, label_file)

        # Destination file paths
        dst_img = os.path.join(output_dir, split, 'images', image_file)
        dst_label = os.path.join(output_dir, split, 'labels', label_file)

        # Move the files
        shutil.copy2(src_img, dst_img)
        shutil.copy2(src_label, dst_label)

# Move the files to their respective directories
move_files(train_data, 'train')
move_files(val_data, 'val')
move_files(test_data, 'test')

print("Data split completed!")