#!/usr/bin/env python
"""
Image Processing Test Script for Kodomo Shokudo Survey

This script allows you to test the image processing functionality without
having to go through the LINE LIFF app. It takes an image file as input,
processes it using the ImageService, and displays the results.

Usage:
    python test_image_processing.py --image_path IMAGE_PATH

Requirements:
    - OpenCV must be installed
    - The ImageService class must be implemented
"""

import os
import sys
import argparse
import cv2
import numpy as np
from services.image_service import ImageService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def display_image(title, image):
    """Display an image in a window"""
    cv2.imshow(title, image)
    cv2.waitKey(0)

def save_image(filename, image):
    """Save an image to a file"""
    cv2.imwrite(filename, image)
    print(f"Saved image to {filename}")

def process_image(image_path):
    """Process an image using the ImageService"""
    # Check if image file exists
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        sys.exit(1)
    
    try:
        # Create ImageService
        image_service = ImageService()
        
        # Read image file
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Process image
        processed_image_bytes, counts = image_service.process_image(image_data)
        
        # Convert processed image bytes back to OpenCV format
        nparr = np.frombuffer(processed_image_bytes, np.uint8)
        processed_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Display results
        print("Processing complete!")
        print("\nCounts by quadrant and color:")
        for quadrant, colors in counts.items():
            print(f"Quadrant {quadrant}:")
            for color, count in colors.items():
                print(f"  {color}: {count}")
        
        # Calculate total counts
        total_counts = {
            'red': 0,
            'green': 0,
            'blue': 0,
            'yellow': 0,
            'total': 0
        }
        
        for quadrant, colors in counts.items():
            for color, count in colors.items():
                total_counts[color] += count
                total_counts['total'] += count
        
        print("\nTotal counts by color:")
        for color, count in total_counts.items():
            if color != 'total':
                print(f"  {color}: {count}")
        print(f"Total stickers: {total_counts['total']}")
        
        # Display original image
        original_image = cv2.imread(image_path)
        if original_image is not None:
            # Resize if too large
            height, width = original_image.shape[:2]
            max_dimension = 800
            if height > max_dimension or width > max_dimension:
                scale = max_dimension / max(height, width)
                original_image = cv2.resize(original_image, None, fx=scale, fy=scale)
            
            display_image("Original Image", original_image)
        
        # Display processed image
        if processed_image is not None:
            # Resize if too large
            height, width = processed_image.shape[:2]
            max_dimension = 800
            if height > max_dimension or width > max_dimension:
                scale = max_dimension / max(height, width)
                processed_image = cv2.resize(processed_image, None, fx=scale, fy=scale)
            
            display_image("Processed Image", processed_image)
        
        # Save processed image
        output_path = os.path.join(
            os.path.dirname(image_path),
            f"processed_{os.path.basename(image_path)}"
        )
        save_image(output_path, processed_image)
        
        return processed_image, counts
    
    except Exception as e:
        print(f"Error processing image: {e}")
        sys.exit(1)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test image processing for Kodomo Shokudo Survey')
    parser.add_argument('--image_path', required=True, help='Path to the image file to process')
    args = parser.parse_args()
    
    print("Testing image processing for Kodomo Shokudo Survey...")
    
    # Process image
    process_image(args.image_path)
    
    # Close all windows
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
