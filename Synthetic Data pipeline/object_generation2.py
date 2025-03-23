# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 19:35:20 2024

@author: engpeter
"""


import random
from PIL import Image, ImageFont, ImageDraw
from math import pi

# Constants
image_size = (300, 300)
font = ImageFont.truetype("arial.ttf", 60)
shapes = ["circle", "semicircle", "quarter circle", "triangle", "rectangle", "pentagon", "star", "cross"]
colors = ["black", "red", "blue", "green", "purple", "brown", "orange"]

classes = {shape: i for i, shape in enumerate(shapes)}
alphanum_classes = {char: i for i, char in enumerate("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", start = 8)}


# Function to calculate polygon centroid
def polygon_centroid(vertices):
    n = len(vertices)
    A, C_x, C_y = 0, 0, 0
    for i in range(n):
        x_i, y_i = vertices[i]
        x_next, y_next = vertices[(i + 1) % n]
        cross_product = x_i * y_next - x_next * y_i
        A += cross_product
        C_x += (x_i + x_next) * cross_product
        C_y += (y_i + y_next) * cross_product
    A *= 0.5
    C_x /= (6 * A)
    C_y /= (6 * A)
    return C_x, C_y
def circular_centroid(center, radius, segment_type):
    
    """
    Calculate the centroid of a quarter circle or semicircle.

    Parameters:
    center (tuple): The (x, y) coordinates of the center of the full circle.
    radius (float): The radius of the quarter circle.
    segment_type (string): The type of segment ('quarter' or 'semi'). 
    
    Returns:
    tuple: The (x, y) coordinates of the centroid of the quarter circle.
    """
    if segment_type == 'quarter':
        centroid_offset = (4 * radius) / (3 * pi)
        centroid_x = center[0] + centroid_offset
        centroid_y = center[1] + centroid_offset
    elif segment_type == 'semi':
        centroid_offset = (4 * radius) / (3 * pi)
        centroid_x = center[0]
        centroid_y = center[1] + centroid_offset
    else:
        raise ValueError("segment_type must be 'quarter' or 'semi'")
    
    return (centroid_x, centroid_y) 



# Function to draw shapes and alphanumerics
def draw_shape(draw, shape, shape_color):
    if shape == "circle":
        draw.ellipse((50, 50, 250, 250), fill=shape_color)
        bbox = [(50, 50), (250, 50), (250, 250), (50, 250)]  # Four corners of the bounding box
        return [(150, 150)], bbox
    elif shape == "semicircle":
        draw.pieslice((50, 50, 250, 250), start=0, end=180, fill=shape_color)
        bbox = [(50, 150), (250, 150), (250, 250), (50, 250)]  # Bounding box corners of the semicircle
        return [circular_centroid((150, 150), 100, "semi")], bbox
    elif shape == "quarter circle":
        draw.pieslice((50, 50, 250, 250), start=0, end=90, fill=shape_color)
        bbox = [(150, 150), (250, 150), (250, 250), (150, 250)]  # Bounding box corners of the quarter circle
        return [circular_centroid((150, 150), 100, "quarter")], bbox
    elif shape == "triangle":
        vertices = [(150, 50), (50, 250), (250, 250)]
        draw.polygon(vertices, fill=shape_color)
        bbox = [(50, 50), (250, 50), (250, 250), (50, 250)]  # Four corners of the bounding box
        return vertices, bbox
    elif shape == "rectangle":
        draw.rectangle((50, 50, 250, 250), fill=shape_color)
        bbox = [(50, 50), (250, 50), (250, 250), (50, 250)]  # Bounding box of the rectangle
        return [(150, 150)], bbox
    elif shape == "pentagon":
        vertices = [(150, 50), (50, 150), (100, 250), (200, 250), (250, 150)]
        draw.polygon(vertices, fill=shape_color)
        bbox = [(50, 50), (250, 50), (250, 250), (50, 250)]  # Four corners of the bounding box
        return vertices, bbox
    
    elif shape == "cross":
        draw.rectangle((100, 50, 200, 250), fill=shape_color)  # Vertical part
        draw.rectangle((50, 100, 250, 200), fill=shape_color)  # Horizontal part
        bbox = [(50, 50), (250, 50), (250, 250), (50, 250)]  # Bounding box of the cross
        return [(150, 150)], bbox
    elif shape == "star":
        vertices = [(150, 50), (175, 150), (250, 150), (200, 200), (225, 300),
                    (150, 225), (75, 300), (100, 200), (50, 150), (125, 150)]
        draw.polygon(vertices, fill=shape_color)
        bbox = [(50, 50), (250, 50), (250, 300), (50, 300)]  # Bounding box of the star
        return vertices, bbox
    

def draw_shape_alnum():
    img = Image.new("RGBA", image_size, (255, 255, 255, 0))
    canvas = ImageDraw.Draw(img)
    
    shape = random.choice(shapes)
    text = random.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    shape_color = random.choice(colors)
    text_colors = [color for color in colors if color != shape_color]
    text_color = random.choice(text_colors)
    
    # Draw shape and get bounding box
    vertices, bbox_shape = draw_shape(canvas, shape, shape_color)
    
    # Calculate text bounding box and centroid
    bbox_text = canvas.textbbox((0, 0), text, font=font)
    text_width = bbox_text[2] - bbox_text[0]
    text_height = bbox_text[3] - bbox_text[1]
    
    # Calculate shape centroid
    if len(vertices) == 1:
        centroid_x, centroid_y = vertices[0]
    else:
        centroid_x, centroid_y = polygon_centroid(vertices)
    
    # Calculate text position
    text_x = centroid_x - text_width / 2
    text_y = centroid_y - text_height / 2 - (text_height * 0.25)
    
    # Draw alphanumeric text on the shape
    canvas.text((text_x, text_y), text, fill=text_color, font=font)
    
    text_y_min = text_y + (text_height * 0.25) - 5  # Five-pixel padding
    text_x_min = text_x
    
    # Update text bounding box coordinates
    bbox_text = [(text_x_min, text_y_min),
                 (text_x_min + text_width, text_y_min + text_height + 10)]
    
    # Bounding box corners for the text
    bbox_text_corners = [(text_x_min, text_y_min),
                         (text_x_min + text_width, text_y_min),
                         (text_x_min + text_width, text_y_min + text_height + 10),
                         (text_x_min, text_y_min + text_height + 10)]
    
    return img, shape, bbox_shape, bbox_text_corners, text


