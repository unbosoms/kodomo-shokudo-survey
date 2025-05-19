import cv2
import numpy as np
import io
from PIL import Image

class ImageService:
    def __init__(self):
        """Initialize image processing service"""
        # Define color ranges in HSV space
        # These ranges can be adjusted based on actual sticker colors and lighting conditions
        self.color_ranges = {
            'red': [
                # Red wraps around in HSV, so we need two ranges
                (np.array([0, 100, 100]), np.array([10, 255, 255])),
                (np.array([160, 100, 100]), np.array([180, 255, 255]))
            ],
            'green': [(np.array([40, 100, 100]), np.array([80, 255, 255]))],
            'blue': [(np.array([100, 100, 100]), np.array([140, 255, 255]))],
            'yellow': [(np.array([20, 100, 100]), np.array([35, 255, 255]))]
        }
        
        # Minimum area for a sticker (in pixels)
        self.min_sticker_area = 100
        
        # Maximum area for a sticker (in pixels)
        self.max_sticker_area = 5000
    
    def process_image(self, image_data):
        """Process image and count stickers
        
        Args:
            image_data: Image data (file object, bytes, or numpy array)
            
        Returns:
            tuple: (processed_image, counts)
                processed_image: The processed image with annotations
                counts: Dictionary of counts by quadrant and color
        """
        # Convert image data to OpenCV format
        image = self._load_image(image_data)
        
        # Preprocess image (white balance, shadow removal)
        preprocessed = self._preprocess_image(image)
        
        # Detect paper and apply perspective transform
        paper = self._detect_and_transform_paper(preprocessed)
        
        # Divide into quadrants
        quadrants = self._divide_into_quadrants(paper)
        
        # Count stickers in each quadrant
        counts = {}
        for quadrant_name, quadrant_img in quadrants.items():
            counts[quadrant_name] = self._count_stickers_by_color(quadrant_img)
        
        # Create annotated image for visualization
        annotated = self._annotate_image(paper, quadrants, counts)
        
        # Convert back to bytes for storage
        _, processed_bytes = cv2.imencode('.jpg', annotated)
        
        return processed_bytes.tobytes(), counts
    
    def _load_image(self, image_data):
        """Load image from various input formats"""
        if isinstance(image_data, np.ndarray):
            # Already a numpy array
            return image_data
        
        if hasattr(image_data, 'read'):
            # File-like object
            image_bytes = image_data.read()
            # Reset file pointer if possible
            if hasattr(image_data, 'seek'):
                image_data.seek(0)
        elif isinstance(image_data, bytes):
            # Already bytes
            image_bytes = image_data
        else:
            raise ValueError("Unsupported image data format")
        
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Failed to decode image")
        
        return image
    
    def _preprocess_image(self, image):
        """Apply preprocessing to improve image quality
        
        - White balance adjustment
        - Shadow removal
        - Contrast enhancement
        """
        # Convert to LAB color space for white balance
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Split LAB channels
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        
        # Merge channels back
        limg = cv2.merge((cl, a, b))
        
        # Convert back to BGR
        balanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        
        # Shadow removal using bilateral filter
        bilateral = cv2.bilateralFilter(balanced, 9, 75, 75)
        
        return bilateral
    
    def _detect_and_transform_paper(self, image):
        """Detect paper in image and apply perspective transform"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY_INV, 11, 2)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            # If no contours found, return original image
            return image
        
        # Find the largest contour (assumed to be the paper)
        paper_contour = max(contours, key=cv2.contourArea)
        
        # Approximate the contour to a polygon
        peri = cv2.arcLength(paper_contour, True)
        approx = cv2.approxPolyDP(paper_contour, 0.02 * peri, True)
        
        # If we don't get a quadrilateral, return original image
        if len(approx) != 4:
            return image
        
        # Sort the points in order: top-left, top-right, bottom-right, bottom-left
        pts = approx.reshape(4, 2)
        rect = np.zeros((4, 2), dtype="float32")
        
        # Top-left point has the smallest sum
        # Bottom-right point has the largest sum
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # Top-right has the smallest difference
        # Bottom-left has the largest difference
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        # Define the destination points (A4 paper in landscape orientation)
        # A4 dimensions: 297mm x 210mm (landscape: 297mm width, 210mm height)
        # We'll scale to pixels at 3 pixels per mm
        width, height = 891, 630  # 297mm * 3, 210mm * 3
        dst = np.array([
            [0, 0],           # Top-left
            [width, 0],       # Top-right
            [width, height],  # Bottom-right
            [0, height]       # Bottom-left
        ], dtype="float32")
        
        # Calculate perspective transform matrix
        M = cv2.getPerspectiveTransform(rect, dst)
        
        # Apply perspective transform
        warped = cv2.warpPerspective(image, M, (width, height))
        
        return warped
    
    def _divide_into_quadrants(self, image):
        """Divide image into four quadrants"""
        height, width = image.shape[:2]
        mid_x, mid_y = width // 2, height // 2
        
        return {
            'UL': image[0:mid_y, 0:mid_x],       # Upper Left
            'UR': image[0:mid_y, mid_x:width],   # Upper Right
            'LL': image[mid_y:height, 0:mid_x],  # Lower Left
            'LR': image[mid_y:height, mid_x:width]  # Lower Right
        }
    
    def _count_stickers_by_color(self, image):
        """Count stickers in image by color"""
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        counts = {
            'red': 0,
            'green': 0,
            'blue': 0,
            'yellow': 0
        }
        
        # For each color, create a mask and count contours
        for color, ranges in self.color_ranges.items():
            # Create mask by combining all ranges for this color
            mask = None
            for lower, upper in ranges:
                color_mask = cv2.inRange(hsv, lower, upper)
                if mask is None:
                    mask = color_mask
                else:
                    mask = cv2.bitwise_or(mask, color_mask)
            
            # Apply morphological operations to clean up the mask
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            # Find contours in the mask
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Count contours that are likely to be stickers
            for contour in contours:
                area = cv2.contourArea(contour)
                if self.min_sticker_area < area < self.max_sticker_area:
                    counts[color] += 1
        
        return counts
    
    def _annotate_image(self, image, quadrants, counts):
        """Add annotations to the image for visualization"""
        # Create a copy of the image
        annotated = image.copy()
        
        # Draw quadrant lines
        height, width = annotated.shape[:2]
        mid_x, mid_y = width // 2, height // 2
        
        # Horizontal line
        cv2.line(annotated, (0, mid_y), (width, mid_y), (0, 0, 0), 2)
        
        # Vertical line
        cv2.line(annotated, (mid_x, 0), (mid_x, height), (0, 0, 0), 2)
        
        # Add count text to each quadrant
        quadrant_positions = {
            'UL': (10, 30),
            'UR': (mid_x + 10, 30),
            'LL': (10, mid_y + 30),
            'LR': (mid_x + 10, mid_y + 30)
        }
        
        for quadrant, position in quadrant_positions.items():
            x, y = position
            
            # Add quadrant label
            cv2.putText(annotated, quadrant, (x, y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            
            # Add color counts
            y_offset = 30
            for color, count in counts[quadrant].items():
                y += y_offset
                
                # Skip if count is 0
                if count == 0:
                    continue
                
                # Set text color based on sticker color
                if color == 'red':
                    text_color = (0, 0, 255)
                elif color == 'green':
                    text_color = (0, 255, 0)
                elif color == 'blue':
                    text_color = (255, 0, 0)
                elif color == 'yellow':
                    text_color = (0, 255, 255)
                else:
                    text_color = (255, 255, 255)
                
                cv2.putText(annotated, f"{color}: {count}", (x, y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
        
        return annotated
    
    def create_guide_overlay(self, width, height):
        """Create a transparent overlay with guide lines for camera preview
        
        Args:
            width: Width of the overlay
            height: Height of the overlay
            
        Returns:
            bytes: PNG image data with transparent background and guide lines
        """
        # Create a transparent image
        overlay = np.zeros((height, width, 4), dtype=np.uint8)
        
        # Calculate midpoints
        mid_x, mid_y = width // 2, height // 2
        
        # Draw horizontal line
        cv2.line(overlay, (0, mid_y), (width, mid_y), (255, 0, 0, 128), 2)
        
        # Draw vertical line
        cv2.line(overlay, (mid_x, 0), (mid_x, height), (255, 0, 0, 128), 2)
        
        # Add quadrant labels
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(overlay, "Upper Left", (10, mid_y - 10), font, 0.7, (255, 0, 0, 200), 2)
        cv2.putText(overlay, "Upper Right", (mid_x + 10, mid_y - 10), font, 0.7, (255, 0, 0, 200), 2)
        cv2.putText(overlay, "Lower Left", (10, height - 10), font, 0.7, (255, 0, 0, 200), 2)
        cv2.putText(overlay, "Lower Right", (mid_x + 10, height - 10), font, 0.7, (255, 0, 0, 200), 2)
        
        # Convert to PIL Image to save as PNG with transparency
        pil_img = Image.fromarray(overlay)
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format='PNG')
        
        return img_byte_arr.getvalue()
