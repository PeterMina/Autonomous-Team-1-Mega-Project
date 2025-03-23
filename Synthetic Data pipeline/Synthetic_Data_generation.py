# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 18:34:03 2024

@author: engpeter
"""

"""
pipeline:
    
shape_alphanumerical generation --> aerial projection ---> text_train_validation split
    .                                                               .
    .                                                               .
    ---> pre projection annotation --> annotation projection and normalization yolov9 format
        
"""


import os
import cv2
import random
import numpy as np
from sklearn.model_selection import train_test_split
from images_projection import aerial_projection  # Your projection module
from image_projection2 import aerial_projection2
from object_generation2 import draw_shape_alnum
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Directories
aerial_images_dir = "D:/ODLC Data/aerial images"
output_images_dir = r"./yolo_data2/images"
output_labels_dir = r"./yolo_data2/labels"

# Classes (shapes and alphanumerics)
shapes = ["circle", "semicircle", "quarter circle", "triangle", "rectangle", "pentagon", "star", "cross"]
alphanumerics = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
classes = {shape: i for i, shape in enumerate(shapes)}
alphanum_classes = {char: i for i, char in enumerate(alphanumerics, start=8)}

# Create directories if they don't exist
os.makedirs(output_images_dir, exist_ok=True)
os.makedirs(output_labels_dir, exist_ok=True)

# Load aerial images
aerial_images = [os.path.join(aerial_images_dir, f) for f in os.listdir(aerial_images_dir) if f.endswith(".jpg")]

def plot_image_with_bbox(final_image, bbox_shape, bbox_text):
    """
    Plots the final image with the shape and text bounding boxes.

    Args:
    - final_image: The image to plot (as a numpy array).
    - bbox_shape: The bounding box for the shape, format [(x_min, y_min), (x_max, y_max)].
    - bbox_text: The bounding box for the text, format [(x_min, y_min), (x_max, y_max)].
    """
    # Convert the image from BGR to RGB for displaying using Matplotlib
    final_image_np = np.array(final_image)
    img_rgb = cv2.cvtColor(final_image_np, cv2.COLOR_BGR2RGB)
    
    # Plot the image
    plt.figure(figsize=(8, 8))
    plt.imshow(img_rgb)
    
    # Plot shape bounding box in red
    x_min_shape, y_min_shape = bbox_shape[0]
    x_max_shape, y_max_shape = bbox_shape[1]
    plt.plot([x_min_shape, x_max_shape, x_max_shape, x_min_shape, x_min_shape],
             [y_min_shape, y_min_shape, y_max_shape, y_max_shape, y_min_shape], color='red', linewidth=2, label='Shape BBox')

    # Plot text bounding box in blue
    x_min_text, y_min_text = bbox_text[0]
    x_max_text, y_max_text = bbox_text[1]
    plt.plot([x_min_text, x_max_text, x_max_text, x_min_text, x_min_text],
             [y_min_text, y_min_text, y_max_text, y_max_text, y_min_text], color='blue', linewidth=2, label='Text BBox')

    # Add legend to distinguish between bounding boxes
    plt.legend()

    # Show the final image with bounding boxes
    plt.axis('off')  # Hide axis
    plt.show()
    
def plot_projected_bbox(image, bbox_shape, bbox_text):
    """
    Plot the projected bounding box for the shape and text onto the image for debugging purposes.
    
    Parameters:
    image (numpy array): The image onto which the bounding boxes will be plotted.
    bbox_shape (list of tuples): The projected bounding box coordinates for the shape.
    bbox_text (list of tuples): The projected bounding box coordinates for the alphanumeric text.
    """
    # Convert BGR to RGB for displaying with matplotlib
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Create a figure and axis to plot on
    fig, ax = plt.subplots(1)
    
    # Display the aerial image
    ax.imshow(image_rgb)
    
    # Plot the shape bounding box
    polygon_shape = patches.Polygon(bbox_shape, closed=True, fill=False, edgecolor='r', linewidth=2, label='Shape BBox')
    ax.add_patch(polygon_shape)

    # Plot the text bounding box
    polygon_text = patches.Polygon(bbox_text, closed=True, fill=False, edgecolor='b', linewidth=2, label='Text BBox')
    ax.add_patch(polygon_text)
    
    # Add labels and legend
    ax.set_title("Projected Bounding Boxes")
    ax.legend(handles=[polygon_shape, polygon_text])
    
    # Show the plot
    plt.show()

def get_axis_aligned_bbox(rotated_bbox):
    """
    Get the axis-aligned bounding box from a rotated bounding box.
    
    Parameters:
    rotated_bbox (numpy array): The rotated bounding box with coordinates.
    
    Returns:
    axis_aligned_bbox (list): Axis-aligned bounding box as [x_min, y_min, x_max, y_max].
    """
    x_coords = rotated_bbox[:, 0]
    y_coords = rotated_bbox[:, 1]
    
    x_min = np.min(x_coords)
    y_min = np.min(y_coords)
    x_max = np.max(x_coords)
    y_max = np.max(y_coords)
    
    return [(x_min, y_min), (x_max, y_max)]
    
def create_yolo_annotation(bbox, img_width, img_height, class_id):
    """
    Convert bounding box to YOLO format (class_id, x_center, y_center, width, height)
    and ensure valid, normalized values.
    """
    print(f"####################### calss id: {class_id}")
    print("bbox:", bbox)
    print("img_width:", img_width)
    print("img_height ",img_height)
    x_min, y_min = bbox[0]
    x_max, y_max = bbox[1]
    print(f"{x_min} < {x_max}")
    print(f"{y_min} < {y_max}")
    #Ensure the bounding box stays within the image boundaries
    x_min = max(0, min(x_min, img_width))
    y_min = max(0, min(y_min, img_height))
    x_max = max(0, min(x_max, img_width))
    y_max = max(0, min(y_max, img_height))
    
    print(f"After clamping: x_min: {x_min}, x_max: {x_max}, y_min: {y_min}, y_max: {y_max}")
    
    # Ensure x_min < x_max and y_min < y_max (valid bounding box)
    if x_max <= x_min or y_max <= y_min:
        raise ValueError("Invalid bounding box dimensions")
       
    
    # Calculate YOLO normalized values
    x_center = (x_min + x_max) / 2.0 / img_width
    y_center = (y_min + y_max) / 2.0 / img_height
    width = (x_max - x_min) / img_width
    height = (y_max - y_min) / img_height
    
    # Ensure the normalized coordinates are between 0 and 1
    if not (0 <= x_center <= 1 and 0 <= y_center <= 1 and 0 <= width <= 1 and 0 <= height <= 1):
        raise ValueError(f"Normalized coordinates out of bounds: {x_center}, {y_center}, {width}, {height}")
        
    return f"{class_id} {x_center} {y_center} {width} {height}\n"


# Function to save YOLO format annotations
def save_yolo_annotation(file_path, shape_class_id, bbox_shape, alnum_class_id, bbox_text, img_width, img_height):
    with open(file_path, 'w') as f:
        # Shape annotation
        print("shape")
        shape_annotation = create_yolo_annotation(bbox_shape, img_width, img_height, shape_class_id)
        f.write(shape_annotation)
        
        # Alphanumeric annotation
        print("text")
        alnum_annotation = create_yolo_annotation(bbox_text, img_width, img_height, alnum_class_id)

        f.write(alnum_annotation)

# Generate images and annotations
image_paths = []
label_paths = []

for i in range(100):
    # Randomly pick an aerial image
    field_image_path = random.choice(aerial_images)
    field_img = cv2.imread(field_image_path)

    # Generate a random shape and text using draw_shape_alnum function
    img_pil, shape, bbox_shape, bbox_text, text = draw_shape_alnum()
    img_pil = img_pil.convert("RGBA")
    print(bbox_shape, bbox_text)
    
    
    #plot projected boundryfor shape
    
    # Convert PIL image to OpenCV format for projection
    shape_img = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGBA2BGRA)
    
    # Project the shape onto the aerial image
    final_image, updated_bbox_shape, updated_bbox_text = aerial_projection2(shape_img, bbox_shape, bbox_text, field_img)
    bbox_shape = get_axis_aligned_bbox(updated_bbox_shape)
    bbox_text = get_axis_aligned_bbox(updated_bbox_text)
    # Save the final image
    image_file_name = f"image_{i}.jpg"
    image_file_path = os.path.join(output_images_dir, image_file_name)
    cv2.imwrite(image_file_path, final_image)
    image_paths.append(image_file_path)

    # Save the YOLO annotation
    label_file_name = f"image_{i}.txt"
    label_file_path = os.path.join(output_labels_dir, label_file_name)
    label_paths.append(label_file_path)

    shape_class_id = classes[shape]
    alnum_class_id = alphanum_classes[text]
    
    save_yolo_annotation(label_file_path, shape_class_id, bbox_shape, alnum_class_id, bbox_text, final_image.shape[1], final_image.shape[0])
    if i%100 == 0:
        print(f"image{i+1}")
    plot_image_with_bbox(final_image, bbox_shape, bbox_text)
    #plot_projected_bbox(final_image, updated_bbox_shape, updated_bbox_text)
    #plot the projected boundry for text

    
# Split into train and validation sets
train_images, val_images, train_labels, val_labels = train_test_split(image_paths, label_paths, test_size=0.2, random_state=42)
    

# Save train/val splits
with open("./yolo_data/train.txt", "w") as f:
    for path in train_images:
        f.write(f"{path}\n")

with open("./yolo_data/val.txt", "w") as f:
    for path in val_images:
        f.write(f"{path}\n")

print("Dataset creation and YOLO annotation generation completed!")
