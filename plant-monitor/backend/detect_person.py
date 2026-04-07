#!/usr/bin/env python3
"""
YOLO-based person detection for plant monitoring
Detects people in webcam images before plant analysis
"""

import json
import cv2
from pathlib import Path
from ultralytics import YOLO

# Load lightweight YOLO model (YOLOv8n - nano version)
MODEL = None

def get_model():
    """Lazy load YOLO model"""
    global MODEL
    if MODEL is None:
        MODEL = YOLO('yolov8n.pt')  # Lightweight pretrained model
    return MODEL

def detect_people(image_path):
    """
    Detect people in an image using YOLO
    
    Args:
        image_path: Path to image file
        
    Returns:
        dict: {
            'person_detected': bool,
            'person_count': int,
            'detections': [
                {
                    'class_name': str,
                    'confidence': float,
                    'bbox_xyxy': [x1, y1, x2, y2]
                }
            ]
        }
    """
    try:
        model = get_model()
        
        # Run inference
        results = model(image_path, verbose=False)
        
        # Extract person detections (class 0 in COCO dataset)
        person_detections = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls[0])
                
                # Filter for person class only (class_id = 0)
                if class_id == 0:
                    confidence = float(box.conf[0])
                    bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                    
                    person_detections.append({
                        'class_name': 'person',
                        'confidence': confidence,
                        'bbox_xyxy': bbox
                    })
        
        metadata = {
            'person_detected': len(person_detections) > 0,
            'person_count': len(person_detections),
            'detections': person_detections
        }
        
        return metadata
        
    except Exception as e:
        print(f"❌ Person detection failed: {e}")
        return {
            'person_detected': False,
            'person_count': 0,
            'detections': []
        }

def save_metadata_json(image_path, metadata):
    """
    Save detection metadata as JSON file
    
    Args:
        image_path: Original image path
        metadata: Detection metadata dict
        
    Returns:
        Path to saved JSON file
    """
    try:
        image_path = Path(image_path)
        json_path = image_path.parent / f"{image_path.stem}_detection.json"
        
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✓ Detection metadata saved: {json_path.name}")
        return str(json_path)
        
    except Exception as e:
        print(f"❌ Failed to save metadata JSON: {e}")
        return None

def draw_boxes_and_save(image_path, metadata):
    """
    Draw bounding boxes around detected people and save image
    
    Args:
        image_path: Original image path
        metadata: Detection metadata with bounding boxes
        
    Returns:
        Path to boxed image file
    """
    try:
        image_path = Path(image_path)
        boxed_path = image_path.parent / f"{image_path.stem}_boxed{image_path.suffix}"
        
        # Read image
        img = cv2.imread(str(image_path))
        
        if img is None:
            print(f"❌ Could not read image: {image_path}")
            return None
        
        # Draw boxes for each detection
        for detection in metadata['detections']:
            bbox = detection['bbox_xyxy']
            confidence = detection['confidence']
            
            # Convert to integers
            x1, y1, x2, y2 = map(int, bbox)
            
            # Draw rectangle (green color, thickness 2)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Add label with confidence
            label = f"Person {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            
            # Draw label background
            cv2.rectangle(img, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), (0, 255, 0), -1)
            
            # Draw label text
            cv2.putText(img, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        # Save boxed image
        cv2.imwrite(str(boxed_path), img)
        print(f"✓ Boxed image saved: {boxed_path.name}")
        
        return str(boxed_path)
        
    except Exception as e:
        print(f"❌ Failed to draw boxes: {e}")
        return None

def process_image_for_person_detection(image_path):
    """
    Complete pipeline: detect people, save metadata, save boxed image
    
    Args:
        image_path: Path to captured image
        
    Returns:
        dict: {
            'metadata': detection metadata,
            'json_path': path to JSON file,
            'boxed_image_path': path to boxed image
        }
    """
    print(f"\n🔍 Running person detection on: {Path(image_path).name}")
    
    # Detect people
    metadata = detect_people(image_path)
    
    print(f"👤 Person detected: {metadata['person_detected']}")
    print(f"👥 Person count: {metadata['person_count']}")
    
    # Save metadata JSON
    json_path = save_metadata_json(image_path, metadata)
    
    # Draw boxes and save
    boxed_image_path = draw_boxes_and_save(image_path, metadata)
    
    return {
        'metadata': metadata,
        'json_path': json_path,
        'boxed_image_path': boxed_image_path
    }

if __name__ == "__main__":
    # Test with a sample image
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python detect_person.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    result = process_image_for_person_detection(image_path)
    
    print("\n📊 Detection Results:")
    print(json.dumps(result['metadata'], indent=2))
