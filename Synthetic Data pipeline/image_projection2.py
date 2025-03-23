# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 14:02:20 2024

@author: engpeter
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 12:45:37 2024

@author: engpeter
"""
import cv2
import numpy as np
import random

def aerial_projection2(shape_img, bbox_shape, bbox_text, field_img):
    """
    Project a shape with bounding boxes (for the shape and text) onto an aerial image
    using resizing, rotation, and minimal plan-view homography projection.
    
    Parameters:
    shape_img (numpy array): The shape image to be projected.
    bbox_shape (list of tuples): Bounding box coordinates for the shape.
    bbox_text (list of tuples): Bounding box coordinates for the alphanumeric text.
    field_img (numpy array): The aerial image.

    Returns:
    final_image (numpy array): The field image with the projected shape.
    rotated_bbox_shape (list of tuples): Rotated bounding box coordinates for the shape.
    rotated_bbox_text (list of tuples): Rotated bounding box coordinates for the alphanumeric text.
    """
    
    # Resize the shape image and bounding boxes to fit the field
    resized_shape, bbox_shape_resized, bbox_text_resized = resize_shape_and_bbox(field_img, shape_img, bbox_shape, bbox_text)

    # Rotate the shape and bounding boxes
    rotated_shape, rotated_bbox_shape, rotated_bbox_text = rotate_shape_and_bbox(resized_shape, bbox_shape_resized, bbox_text_resized)

    # Apply a mild homography projection to the rotated shape and bounding boxes
    final_image, projected_bbox_shape, projected_bbox_text = project_shape_and_bbox(rotated_shape, rotated_bbox_shape, rotated_bbox_text, field_img)
    
    return final_image, projected_bbox_shape, projected_bbox_text

def resize_shape_and_bbox(field_img, shape_img, bbox_shape, bbox_text):
    """
    Resize the shape image and corresponding bounding boxes to fit within the field image.
    
    Parameters:
    field_img (numpy array): The aerial image.
    shape_img (numpy array): The shape image.
    bbox_shape (list of tuples): Original bounding box for the shape.
    bbox_text (list of tuples): Original bounding box for the text.

    Returns:
    resized_shape (numpy array): Resized shape image.
    bbox_shape_resized (list of tuples): Resized shape bounding box.
    bbox_text_resized (list of tuples): Resized text bounding box.
    """
    
    field_height, field_width = field_img.shape[:2]
    
    # Resize the shape image to 20-30% of the field image size
    scale_factor = random.uniform(0.2, 0.3)
    new_shape_height = int(scale_factor * field_height)
    new_shape_width = int(scale_factor * field_width)
    
    resized_shape = cv2.resize(shape_img, (new_shape_width, new_shape_height))
    
    # Resize the bounding boxes proportionally
    bbox_shape_resized = [(x * new_shape_width / shape_img.shape[1], y * new_shape_height / shape_img.shape[0]) for (x, y) in bbox_shape]
    bbox_text_resized = [(x * new_shape_width / shape_img.shape[1], y * new_shape_height / shape_img.shape[0]) for (x, y) in bbox_text]
    
    return resized_shape, bbox_shape_resized, bbox_text_resized

def rotate_shape_and_bbox(shape_img, bbox_shape, bbox_text):
    """
    Rotate the shape and corresponding bounding boxes by a random angle.
    
    Parameters:
    shape_img (numpy array): The shape image.
    bbox_shape (list of tuples): Resized bounding box for the shape.
    bbox_text (list of tuples): Resized bounding box for the text.

    Returns:
    rotated_shape (numpy array): Rotated shape image.
    rotated_bbox_shape (list of tuples): Rotated shape bounding box.
    rotated_bbox_text (list of tuples): Rotated text bounding box.
    """
    
    angle = random.uniform(0, 90)  # Random rotation angle
    
    # Get rotation matrix and apply it to the shape image
    (h, w) = shape_img.shape[:2]
    center = (w // 2, h // 2)
    M_rotate = cv2.getRotationMatrix2D(center, angle, 1.0)
    
    # Perform the rotation
    rotated_shape = cv2.warpAffine(shape_img, M_rotate, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    
    # Apply the rotation to the bounding boxes
    bbox_shape_rotated = cv2.transform(np.float32([bbox_shape]).reshape(-1, 1, 2), M_rotate).reshape(-1, 2)
    bbox_text_rotated = cv2.transform(np.float32([bbox_text]).reshape(-1, 1, 2), M_rotate).reshape(-1, 2)
    
    return rotated_shape, bbox_shape_rotated, bbox_text_rotated

def project_shape_and_bbox(shape_img, bbox_shape, bbox_text, field_img):
    """
    Apply a mild plan-view homography projection to the shape and bounding boxes.
    
    Parameters:
    shape_img (numpy array): Rotated shape image.
    bbox_shape (list of tuples): Rotated bounding box for the shape.
    bbox_text (list of tuples): Rotated bounding box for the text.
    field_img (numpy array): The aerial image.

    Returns:
    final_image (numpy array): Field image with the projected shape.
    projected_bbox_shape (list of tuples): Projected shape bounding box.
    projected_bbox_text (list of tuples): Projected text bounding box.
    """
    
    # Get shape dimensions
    shape_rows, shape_cols = shape_img.shape[:2]
    field_height, field_width = field_img.shape[:2]
    
    # Random top-left position for the projection (within field boundaries)
    top_left_x = random.randint(0, field_width - shape_cols)
    top_left_y = random.randint(0, field_height - shape_rows)
    
    # Define points for the homography transformation of the shape
    shape_pts = np.float32([[0, 0], [shape_cols, 0], [shape_cols, shape_rows], [0, shape_rows]])
    
    # Simulate a plan view with minimal perspective distortion
    offset = 10  # Small offset to maintain minimal distortion
    field_pts = np.float32([
        [top_left_x + random.uniform(-offset, offset), top_left_y + random.uniform(-offset, offset)],
        [top_left_x + shape_cols + random.uniform(-offset, offset), top_left_y + random.uniform(-offset, offset)],
        [top_left_x + shape_cols + random.uniform(-offset, offset), top_left_y + shape_rows + random.uniform(-offset, offset)],
        [top_left_x + random.uniform(-offset, offset), top_left_y + shape_rows + random.uniform(-offset, offset)]
    ])
    
    # Compute homography matrix
    M_homography = cv2.getPerspectiveTransform(shape_pts, field_pts)
    
    # Apply perspective transformation to the shape image
    transformed_shape = cv2.warpPerspective(shape_img, M_homography, (field_img.shape[1], field_img.shape[0]))
    
    # Create mask for blending
    mask = transformed_shape[:, :, 3]  # Alpha channel
    mask_inv = cv2.bitwise_not(mask)
    transformed_shape_bgr = transformed_shape[:, :, :3]
    
    # Apply the mask to field and transformed shape
    field_bg = cv2.bitwise_and(field_img, field_img, mask=mask_inv)
    shape_fg = cv2.bitwise_and(transformed_shape_bgr, transformed_shape_bgr, mask=mask)
    
    # Combine the images
    final_image = cv2.add(field_bg, shape_fg)
    
    # Apply homography transformation to the bounding boxes
    projected_bbox_shape = cv2.perspectiveTransform(np.float32([bbox_shape]).reshape(-1, 1, 2), M_homography).reshape(-1, 2)
    projected_bbox_text = cv2.perspectiveTransform(np.float32([bbox_text]).reshape(-1, 1, 2), M_homography).reshape(-1, 2)
    
    return final_image, projected_bbox_shape, projected_bbox_text
