#!/usr/bin/env python3
"""
Test script for person detailed analysis
Analyzes an image to detect person and read clothing text
"""

import sys
from pathlib import Path
from vlm.vlm_analyzer import analyze_image
from vlm.prompt_templates import get_person_details_prompt

def test_person_analysis(image_path: str):
    """
    Test person analysis on an image
    
    Args:
        image_path: Path to image file
    """
    print(f"🔍 Analyzing person in image: {image_path}\n")
    
    # Run VLM analysis with person details prompt
    result = analyze_image(
        image_path=image_path,
        analysis_type="custom",
        custom_prompt=get_person_details_prompt()
    )
    
    if not result["success"]:
        print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
        return
    
    print("✅ Analysis complete!\n")
    
    # Extract analysis data
    analysis = result.get("analysis", {})
    
    # Display results
    print("=" * 60)
    print("PERSON DETECTION RESULTS")
    print("=" * 60)
    
    print(f"\n👤 Person Detected: {analysis.get('person_detected', False)}")
    print(f"👥 Person Count: {analysis.get('person_count', 0)}")
    print(f"📍 Position: {analysis.get('position', 'unknown')}")
    print(f"📏 Distance from Plant: {analysis.get('distance_from_plant', 'unknown')}")
    print(f"👁️  Facing Camera: {analysis.get('facing_camera', False)}")
    
    # Clothing details
    clothing = analysis.get('clothing', {})
    if clothing:
        print("\n" + "=" * 60)
        print("CLOTHING DETAILS")
        print("=" * 60)
        print(f"\n👕 Shirt Type: {clothing.get('shirt_type', 'unknown')}")
        print(f"🎨 Shirt Color: {clothing.get('shirt_color', 'unknown')}")
        print(f"📝 Has Text: {clothing.get('shirt_has_text', False)}")
        
        # Highlight shirt text
        shirt_text = clothing.get('shirt_text', 'none')
        if shirt_text and shirt_text not in ['none', 'unreadable']:
            print(f"✨ SHIRT TEXT: '{shirt_text}' ✨")
        else:
            print(f"📝 Shirt Text: {shirt_text}")
        
        print(f"🏷️  Has Logo: {clothing.get('shirt_has_logo', False)}")
        if clothing.get('shirt_has_logo'):
            print(f"🏷️  Logo: {clothing.get('shirt_logo_description', 'none')}")
        
        print(f"\n👖 Pants Type: {clothing.get('pants_type', 'unknown')}")
        print(f"🎨 Pants Color: {clothing.get('pants_color', 'unknown')}")
    
    # Accessories
    accessories = analysis.get('accessories', [])
    if accessories:
        print("\n" + "=" * 60)
        print("ACCESSORIES")
        print("=" * 60)
        for acc in accessories:
            print(f"  • {acc}")
    
    # Actions
    actions = analysis.get('actions', [])
    if actions:
        print("\n" + "=" * 60)
        print("ACTIONS")
        print("=" * 60)
        for action in actions:
            print(f"  • {action}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\n{analysis.get('summary', 'No summary available')}")
    
    # Confidence
    print(f"\n🎯 Confidence: {analysis.get('confidence', 'unknown')}")
    
    print("\n" + "=" * 60)
    print("\n✅ Analysis complete!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_person_analysis.py <image_path>")
        print("\nExample:")
        print("  python test_person_analysis.py /Volumes/SD-128GB/PlantMonitor/images/plant_20260410_220257.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not Path(image_path).exists():
        print(f"❌ Error: Image not found: {image_path}")
        sys.exit(1)
    
    test_person_analysis(image_path)
