#!/usr/bin/env python
"""
Test Image Generator for Kodomo Shokudo Survey

This script generates a sample test image that simulates a survey form with
colored stickers. The image can be used to test the image processing functionality
without having to create a physical survey form.

Usage:
    python generate_test_image.py [--output OUTPUT_PATH] [--stickers STICKERS]

Requirements:
    - OpenCV must be installed
    - NumPy must be installed
"""

import os
import sys
import argparse
import random
import cv2
import numpy as np

def generate_test_image(output_path, sticker_counts=None):
    """Generate a test image with colored stickers"""
    # Default sticker counts if not provided
    if sticker_counts is None:
        sticker_counts = {
            'UL': {'red': 3, 'green': 2, 'blue': 1, 'yellow': 0},
            'UR': {'red': 1, 'green': 4, 'blue': 2, 'yellow': 1},
            'LL': {'red': 0, 'green': 1, 'blue': 3, 'yellow': 2},
            'LR': {'red': 2, 'green': 0, 'blue': 1, 'yellow': 3}
        }
    
    # Create a white background (A4 paper in landscape orientation)
    # A4 dimensions: 297mm x 210mm (landscape: 297mm width, 210mm height)
    # We'll scale to pixels at 3 pixels per mm
    width, height = 891, 630  # 297mm * 3, 210mm * 3
    image = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # Draw quadrant lines
    mid_x, mid_y = width // 2, height // 2
    cv2.line(image, (0, mid_y), (width, mid_y), (0, 0, 0), 2)
    cv2.line(image, (mid_x, 0), (mid_x, height), (0, 0, 0), 2)
    
    # Add quadrant labels
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(image, "ごはん", (mid_x // 2 - 50, mid_y // 2), font, 1.5, (0, 0, 0), 2)
    cv2.putText(image, "あそび", (mid_x + mid_x // 2 - 50, mid_y // 2), font, 1.5, (0, 0, 0), 2)
    cv2.putText(image, "おしゃべり", (mid_x // 2 - 70, mid_y + mid_y // 2), font, 1.5, (0, 0, 0), 2)
    cv2.putText(image, "べんきょう", (mid_x + mid_x // 2 - 70, mid_y + mid_y // 2), font, 1.5, (0, 0, 0), 2)
    
    # Add title and question
    cv2.putText(image, "こども食堂アンケート", (width // 2 - 200, 50), font, 1.5, (0, 0, 0), 2)
    cv2.putText(image, "きょうはなにがたのしかった？", (width // 2 - 250, 100), font, 1.5, (0, 0, 0), 2)
    
    # Define sticker colors (BGR format)
    colors = {
        'red': (0, 0, 255),
        'green': (0, 255, 0),
        'blue': (255, 0, 0),
        'yellow': (0, 255, 255)
    }
    
    # Define quadrant regions
    quadrants = {
        'UL': (0, 0, mid_x, mid_y),
        'UR': (mid_x, 0, width, mid_y),
        'LL': (0, mid_y, mid_x, height),
        'LR': (mid_x, mid_y, width, height)
    }
    
    # Add stickers to each quadrant
    sticker_radius = 15
    min_distance = sticker_radius * 3  # Minimum distance between sticker centers
    
    for quadrant, region in quadrants.items():
        x_min, y_min, x_max, y_max = region
        
        # Add padding to avoid stickers on the edges
        padding = sticker_radius * 2
        x_min += padding
        y_min += padding
        x_max -= padding
        y_max -= padding
        
        # Keep track of sticker positions to avoid overlap
        sticker_positions = []
        
        # Add stickers for each color
        for color, count in sticker_counts[quadrant].items():
            for _ in range(count):
                # Try to find a position that doesn't overlap with existing stickers
                max_attempts = 100
                for attempt in range(max_attempts):
                    # Generate random position
                    x = random.randint(x_min, x_max)
                    y = random.randint(y_min, y_max)
                    
                    # Check if position is far enough from existing stickers
                    valid_position = True
                    for pos_x, pos_y in sticker_positions:
                        distance = np.sqrt((x - pos_x) ** 2 + (y - pos_y) ** 2)
                        if distance < min_distance:
                            valid_position = False
                            break
                    
                    if valid_position:
                        # Add sticker
                        cv2.circle(image, (x, y), sticker_radius, colors[color], -1)
                        sticker_positions.append((x, y))
                        break
    
    # Add legend
    legend_y = height - 50
    legend_x_start = 50
    legend_x_spacing = 200
    
    for i, (color_name, color) in enumerate(colors.items()):
        x = legend_x_start + i * legend_x_spacing
        # Draw color circle
        cv2.circle(image, (x, legend_y), sticker_radius, color, -1)
        # Add label
        if color_name == 'red':
            label = '未就学児'
        elif color_name == 'green':
            label = '小学生'
        elif color_name == 'blue':
            label = '中高生'
        else:  # yellow
            label = '大人'
        cv2.putText(image, label, (x + sticker_radius + 5, legend_y + 5), font, 0.7, (0, 0, 0), 2)
    
    # Save image
    cv2.imwrite(output_path, image)
    print(f"Generated test image saved to {output_path}")
    
    # Display image
    cv2.imshow("Test Image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    return image

def parse_sticker_counts(stickers_str):
    """Parse sticker counts from string"""
    try:
        # Format: UL:red=3,green=2,blue=1,yellow=0;UR:red=1,green=4,blue=2,yellow=1;...
        sticker_counts = {}
        
        quadrants = stickers_str.split(';')
        for quadrant in quadrants:
            if not quadrant:
                continue
                
            parts = quadrant.split(':')
            if len(parts) != 2:
                continue
                
            quadrant_name, counts = parts
            
            if quadrant_name not in ['UL', 'UR', 'LL', 'LR']:
                continue
                
            color_counts = {}
            for count in counts.split(','):
                if not count:
                    continue
                    
                color_parts = count.split('=')
                if len(color_parts) != 2:
                    continue
                    
                color, count = color_parts
                
                if color not in ['red', 'green', 'blue', 'yellow']:
                    continue
                    
                try:
                    color_counts[color] = int(count)
                except ValueError:
                    continue
            
            sticker_counts[quadrant_name] = color_counts
        
        # Make sure all quadrants and colors are present
        for quadrant in ['UL', 'UR', 'LL', 'LR']:
            if quadrant not in sticker_counts:
                sticker_counts[quadrant] = {}
            
            for color in ['red', 'green', 'blue', 'yellow']:
                if color not in sticker_counts[quadrant]:
                    sticker_counts[quadrant][color] = 0
        
        return sticker_counts
    except Exception as e:
        print(f"Error parsing sticker counts: {e}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Generate test image for Kodomo Shokudo Survey')
    parser.add_argument('--output', default='test_image.jpg', help='Output path for the test image')
    parser.add_argument('--stickers', help='Sticker counts in format: UL:red=3,green=2,blue=1,yellow=0;UR:red=1,green=4,blue=2,yellow=1;LL:red=0,green=1,blue=3,yellow=2;LR:red=2,green=0,blue=1,yellow=3')
    args = parser.parse_args()
    
    print("Generating test image for Kodomo Shokudo Survey...")
    
    # Parse sticker counts if provided
    sticker_counts = None
    if args.stickers:
        sticker_counts = parse_sticker_counts(args.stickers)
    
    # Generate test image
    generate_test_image(args.output, sticker_counts)
    
    print("Test image generation complete!")
    print(f"You can now use this image to test the image processing functionality:")
    print(f"python test_image_processing.py --image_path {args.output}")

if __name__ == '__main__':
    main()
