import cv2
import numpy as np
from pdf2image import convert_from_path
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    print("PyMuPDF not available, skipping PDF vector extraction")
    PYMUPDF_AVAILABLE = False
from PIL import Image
import json

def detect_lines_and_colors(pdf_path, page_num=0, dpi=150):
    """
    Detect lines and background colors from PDF
    """
    results = {
        "lines": [],
        "background_colors": [],
        "checkboxes": []
    }
    
    # Method 1: Using pdf2image + OpenCV for line detection
    pages = convert_from_path(pdf_path, dpi=dpi, first_page=page_num+1, last_page=page_num+1)
    if not pages:
        return results
    
    # Convert PIL image to OpenCV format
    img = cv2.cvtColor(np.array(pages[0]), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Detect lines
    results["lines"] = detect_lines(gray, dpi)
    
    # Detect background colors
    results["background_colors"] = detect_background_colors(img, dpi)
    
    # Detect checkboxes
    results["checkboxes"] = detect_checkboxes(gray, dpi)
    
    # Method 2: Using PyMuPDF for more precise PDF elements (if available)
    if PYMUPDF_AVAILABLE:
        try:
            doc = fitz.open(pdf_path)
            if page_num < len(doc):
                page = doc[page_num]
                pymupdf_results = extract_pdf_elements(page)
                
                # Merge results (PyMuPDF often more accurate)
                results["pdf_drawings"] = pymupdf_results["drawings"]
                results["pdf_shapes"] = pymupdf_results["shapes"]
            doc.close()
        except Exception as e:
            print(f"PyMuPDF error: {e}")
    else:
        results["pdf_drawings"] = []
        results["pdf_shapes"] = []
    return results

def detect_lines(gray_image, dpi):
    """
    Detect horizontal and vertical lines using HoughLinesP
    """
    lines_data = []
    
    # More aggressive edge detection for cleaner lines
    edges = cv2.Canny(gray_image, 100, 200, apertureSize=3)
    
    # Detect lines with stricter parameters
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=200, 
                           minLineLength=100, maxLineGap=5)
    
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # Convert pixels to points (assuming 150 DPI)
            points_per_pixel = 72 / dpi
            x1_pt = x1 * points_per_pixel
            y1_pt = y1 * points_per_pixel
            x2_pt = x2 * points_per_pixel
            y2_pt = y2 * points_per_pixel
            
            # Determine orientation
            length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
            angle = np.arctan2(y2-y1, x2-x1) * 180 / np.pi
            
            if abs(angle) < 10 or abs(angle-180) < 10:
                orientation = "horizontal"
            elif abs(angle-90) < 10 or abs(angle+90) < 10:
                orientation = "vertical"
            else:
                orientation = "diagonal"
            
            # Detect if line is dotted (simple approach)
            line_style = detect_line_style(gray_image, x1, y1, x2, y2)
            
            lines_data.append({
                "element_type": "line",
                "orientation": orientation,
                "line_style": line_style,
                "position": {
                    "x1": round(x1_pt, 2),
                    "y1": round(y1_pt, 2),
                    "x2": round(x2_pt, 2),
                    "y2": round(y2_pt, 2),
                    "units": "points"
                },
                "length": round(length * points_per_pixel, 2),
                "angle": round(angle, 2)
            })
    
    return lines_data

def detect_line_style(gray_image, x1, y1, x2, y2):
    """
    Simple dotted line detection by sampling points along the line
    """
    num_samples = 20
    black_count = 0
    
    for i in range(num_samples):
        t = i / (num_samples - 1)
        x = int(x1 + t * (x2 - x1))
        y = int(y1 + t * (y2 - y1))
        
        if 0 <= x < gray_image.shape[1] and 0 <= y < gray_image.shape[0]:
            if gray_image[y, x] < 128:  # Dark pixel
                black_count += 1
    
    # If less than 70% of samples are black, likely dotted
    if black_count / num_samples < 0.7:
        return "dotted"
    else:
        return "solid"

def detect_background_colors(img, dpi):
    """
    Detect significant background colors by clustering
    """
    from sklearn.cluster import KMeans
    import warnings
    warnings.filterwarnings('ignore')
    
    colors_data = []
    height, width = img.shape[:2]
    points_per_pixel = 72 / dpi
    
    # Sample fewer, larger regions
    grid_size = 100  # Larger regions
    min_region_size = 50 * 50  # Minimum significant area
    
    # Collect all non-white colors first
    all_colors = []
    positions = []
    
    for y in range(0, height-grid_size, grid_size):
        for x in range(0, width-grid_size, grid_size):
            region = img[y:y+grid_size, x:x+grid_size]
            if region.size > 0:
                # Get dominant color in region
                avg_color = np.mean(region.reshape(-1, 3), axis=0)
                
                # Skip near-white backgrounds (be more strict)
                if np.mean(avg_color) < 230 and np.std(avg_color) > 10:  # Not white and has variation
                    all_colors.append(avg_color)
                    positions.append((x, y, grid_size, grid_size))
    
    if len(all_colors) < 2:
        return colors_data
    
    # Cluster colors to find distinct background colors
    all_colors = np.array(all_colors)
    n_clusters = min(5, len(all_colors))  # Max 5 distinct colors
    
    try:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        color_labels = kmeans.fit_predict(all_colors)
        
        # Group regions by color cluster
        for cluster_id in range(n_clusters):
            cluster_positions = [positions[i] for i in range(len(positions)) if color_labels[i] == cluster_id]
            
            if len(cluster_positions) > 2:  # Only if color appears in multiple regions
                cluster_color = kmeans.cluster_centers_[cluster_id]
                
                # Find bounding box of all regions with this color
                min_x = min(pos[0] for pos in cluster_positions)
                min_y = min(pos[1] for pos in cluster_positions)
                max_x = max(pos[0] + pos[2] for pos in cluster_positions)
                max_y = max(pos[1] + pos[3] for pos in cluster_positions)
                
                colors_data.append({
                    "element_type": "background_color",
                    "position": {
                        "x": round(min_x * points_per_pixel, 2),
                        "y": round(min_y * points_per_pixel, 2),
                        "width": round((max_x - min_x) * points_per_pixel, 2),
                        "height": round((max_y - min_y) * points_per_pixel, 2),
                        "units": "points"
                    },
                    "color": {
                        "rgb": [int(cluster_color[2]), int(cluster_color[1]), int(cluster_color[0])],  # BGR to RGB
                        "hex": "#{:02x}{:02x}{:02x}".format(int(cluster_color[2]), int(cluster_color[1]), int(cluster_color[0]))
                    },
                    "region_count": len(cluster_positions)
                })
    except:
        pass  # Skip clustering if it fails
    
    return colors_data

def detect_checkboxes(gray_image, dpi):
    """
    Detect checkbox squares using template matching and contour detection
    """
    checkboxes = []
    points_per_pixel = 72 / dpi
    
    # Method 1: Template matching for empty checkboxes
    # Create checkbox template (empty square)
    template_size = 20
    template = np.ones((template_size, template_size), dtype=np.uint8) * 255
    cv2.rectangle(template, (2, 2), (template_size-3, template_size-3), 0, 2)
    
    # Match template
    result = cv2.matchTemplate(gray_image, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.6
    locations = np.where(result >= threshold)
    
    for pt in zip(*locations[::-1]):
        checkboxes.append({
            "element_type": "checkbox",
            "detection_method": "template_matching",
            "position": {
                "x": round(pt[0] * points_per_pixel, 2),
                "y": round(pt[1] * points_per_pixel, 2),
                "width": round(template_size * points_per_pixel, 2),
                "height": round(template_size * points_per_pixel, 2),
                "units": "points"
            },
            "confidence": float(result[pt[1], pt[0]])
        })
    
    # Method 2: Contour detection with stricter filtering
    # Apply morphological operations to clean up the image
    kernel = np.ones((3,3), np.uint8)
    cleaned = cv2.morphologyEx(gray_image, cv2.MORPH_CLOSE, kernel)
    
    # Find contours
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        # Approximate contour to polygon
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Check if it's roughly square/rectangular with 4 corners
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # More specific checkbox criteria
            aspect_ratio = w / h if h != 0 else 0
            extent = area / (w * h) if (w * h) != 0 else 0
            
            # Filter for checkbox-sized squares with good properties
            if (15 <= w <= 35 and 15 <= h <= 35 and  # Size range
                0.8 <= aspect_ratio <= 1.2 and       # Square-ish
                0.7 <= extent <= 1.0 and             # Fill ratio
                200 <= area <= 1000):                # Area range
                
                # Check if it's likely a checkbox (not just any rectangle)
                # Look for mostly empty interior
                roi = gray_image[y+3:y+h-3, x+3:x+w-3]
                if roi.size > 0:
                    interior_mean = np.mean(roi)
                    if interior_mean > 200:  # Mostly white interior
                        checkboxes.append({
                            "element_type": "checkbox",
                            "detection_method": "contour_analysis",
                            "position": {
                                "x": round(x * points_per_pixel, 2),
                                "y": round(y * points_per_pixel, 2),
                                "width": round(w * points_per_pixel, 2),
                                "height": round(h * points_per_pixel, 2),
                                "units": "points"
                            },
                            "properties": {
                                "aspect_ratio": round(aspect_ratio, 2),
                                "extent": round(extent, 2),
                                "area": round(area * (points_per_pixel ** 2), 2),
                                "interior_brightness": round(interior_mean, 1)
                            }
                        })
    
    # Remove duplicate detections (same position)
    unique_checkboxes = []
    for cb in checkboxes:
        is_duplicate = False
        for existing in unique_checkboxes:
            if (abs(cb["position"]["x"] - existing["position"]["x"]) < 10 and
                abs(cb["position"]["y"] - existing["position"]["y"]) < 10):
                is_duplicate = True
                break
        if not is_duplicate:
            unique_checkboxes.append(cb)
    
    return unique_checkboxes

def extract_pdf_elements(page):
    """
    Extract drawing elements directly from PDF using PyMuPDF
    """
    drawings = page.get_drawings()
    shapes = []
    
    for drawing in drawings:
        for item in drawing["items"]:
            if item[0] == "l":  # Line
                x1, y1, x2, y2 = item[1:5]
                shapes.append({
                    "type": "line",
                    "coordinates": {
                        "x1": round(x1, 2),
                        "y1": round(y1, 2), 
                        "x2": round(x2, 2),
                        "y2": round(y2, 2),
                        "units": "points"
                    }
                })
            elif item[0] == "re":  # Rectangle
                x, y, w, h = item[1:5]
                shapes.append({
                    "type": "rectangle",
                    "coordinates": {
                        "x": round(x, 2),
                        "y": round(y, 2),
                        "width": round(w, 2),
                        "height": round(h, 2),
                        "units": "points"
                    }
                })
    
    return {
        "drawings": drawings,
        "shapes": shapes
    }

# Usage example
if __name__ == "__main__":
    pdf_path = "f1040.pdf"  # Replace with your PDF path
    
    try:
        results = detect_lines_and_colors(pdf_path, page_num=0, dpi=150)
        
        # Save results to JSON
        with open("detected_elements.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"Detected {len(results['lines'])} lines")
        print(f"Detected {len(results['background_colors'])} colored regions")
        print(f"Detected {len(results['checkboxes'])} potential checkboxes")
        
        # Print first few results
        if results['lines']:
            print("\nFirst line detected:")
            print(json.dumps(results['lines'][0], indent=2))
            
    except Exception as e:
        print(f"Error processing PDF: {e}")
        print("Make sure you have installed: pip install opencv-python pdf2image PyMuPDF pillow")