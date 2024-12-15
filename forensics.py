import os
from PIL import Image, ImageChops
import exifread
import subprocess
import cv2
import matplotlib.pyplot as plt
import numpy as np

# Helper function to open an image and handle exceptions
def open_image(image_path):
    """Opens an image and handles errors."""
    try:
        img = Image.open(image_path)
        return img
    except Exception as e:
        return {"error": f"Failed to open image: {str(e)}"}

# Function to extract basic metadata (non-EXIF) from an image
def extract_basic_metadata(image_path):
    """Extract basic image metadata."""
    img = open_image(image_path)
    if isinstance(img, dict) and 'error' in img:
        return img  # Return error if image opening fails
    return img.info

# Function to extract EXIF metadata from an image
def extract_exif_metadata(image_path):
    """Extract EXIF metadata from an image."""
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f)
        return tags
    except Exception as e:
        return {"error": f"Failed to read EXIF metadata: {str(e)}"}

# Function to extract metadata using ExifTool
def extract_exiftool_metadata(image_path):
    """Extract metadata using ExifTool."""
    try:
        result = subprocess.run(['exiftool', image_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            return {"error": result.stderr.decode('utf-8')}
        return result.stdout.decode('utf-8')
    except Exception as e:
        return {"error": f"Failed to run ExifTool: {str(e)}"}

# Function to detect clone patterns in an image using edge detection
def detect_clone_patterns(image_path):
    """Detect clone patterns (e.g., duplicated regions) in an image."""
    image = cv2.imread(image_path, 0)  # Grayscale
    if image is None:
        return {"error": "Failed to read the image for clone detection."}
    edges = cv2.Canny(image, 100, 200)
    return edges

# Perform Error Level Analysis (ELA) to detect inconsistencies in compression
def perform_ela_analysis(image_path, quality=90):
    """Perform ELA to detect inconsistencies due to image editing."""
    original = open_image(image_path)
    if isinstance(original, dict) and 'error' in original:
        return original  # Return error if image opening fails
    ela_path = "ela_image.jpg"
    try:
        original.save(ela_path, 'JPEG', quality=quality)
        ela_image = Image.open(ela_path)
        diff = ImageChops.difference(original, ela_image)
        return diff
    except Exception as e:
        return {"error": f"Failed to perform ELA: {str(e)}"}

# Check if an image is likely a screenshot
def check_image_for_screenshot(image_path):
    """Check for potential screenshots based on image resolution and metadata."""
    img = open_image(image_path)
    if isinstance(img, dict) and 'error' in img:
        return img  # Return error if image opening fails
    width, height = img.size

    # List of common screen resolutions with a tolerance for aspect ratios
    common_resolutions = [
        (1920, 1080), (1366, 768), (1280, 720), (1440, 900),
        (1680, 1050), (1280, 800), (2560, 1440), (3840, 2160)
    ]

    # Adding tolerance: Allow some variation in the aspect ratio (e.g., 90-110% of common resolutions)
    for res in common_resolutions:
        if (width >= res[0] * 0.9 and width <= res[0] * 1.1) and \
           (height >= res[1] * 0.9 and height <= res[1] * 1.1):
            return "Possible Screenshot (Common Screen Resolution)", 35  # 35% score for screenshot-like resolution

    # Check if EXIF metadata is minimal or missing (common in screenshots)
    exif_metadata = extract_exif_metadata(image_path)
    if not exif_metadata or ('Image' not in exif_metadata):
        return "Possible Screenshot (Missing or Minimal EXIF Data)", 50  # 50% score if metadata is minimal

    return "Original Image (Not a Screenshot)", 0

# Check for potential forgery based on metadata and analysis
def check_image_for_forgery(image_path):
    """Check for forgery based on metadata and image analysis, and calculate a forgery score."""
    forgery_score = 0

    # Check metadata for signs of forgery
    basic_metadata = extract_basic_metadata(image_path)
    exif_metadata = extract_exif_metadata(image_path)
    exiftool_metadata = extract_exiftool_metadata(image_path)

    # Software-related metadata indicating forgery
    if 'Software' in basic_metadata and basic_metadata['Software']:
        forgery_score += 40  # 20% for software usage metadata

    # Check ExifTool for software signatures indicating manipulation
    if 'Inkscape' in exiftool_metadata or 'Photoshop' in exiftool_metadata:
        forgery_score += 40  # 25% for specific software signatures indicating editing

    return forgery_score

# Main execution function to analyze the image
def analyze_image(image_path):
    """Analyze an image for screenshots, forgery, and visual inconsistencies."""
    print(f"Analyzing image: {image_path}")
    
    # Screenshot check
    screenshot_result, screenshot_score = check_image_for_screenshot(image_path)
    print(f"Screenshot check result: {screenshot_result}, Score: {screenshot_score}%")
    
    # Forgery check
    forgery_score = check_image_for_forgery(image_path)
    print(f"Forgery check result: Forgery Score: {forgery_score}%")
    
    # Final forgery score (combined)
    total_forgery_score = forgery_score + screenshot_score
    total_forgery_score = min(total_forgery_score, 100)  # Cap the score at 100%

    print(f"Total Forgery Probability: {total_forgery_score}%")
    
    # Optional: Perform Clone Detection
    clone_edges = detect_clone_patterns(image_path)
    if isinstance(clone_edges, np.ndarray):
        plt.imshow(clone_edges, cmap='gray')
        plt.title("Clone Detection (Edges)")
        plt.show()
    else:
        print(clone_edges)
    
    # Optional: Perform ELA Analysis
    ela_result = perform_ela_analysis(image_path)
    if isinstance(ela_result, Image.Image):
        ela_result.show()
    else:
        print(ela_result)

# Example usage
if __name__ == "__main__":
    image_path = "path_to_image"  # Update this path with your image location
    analyze_image(image_path)
