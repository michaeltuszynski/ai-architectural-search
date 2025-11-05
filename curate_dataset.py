#!/usr/bin/env python3
"""
Dataset Curation Script for AI Architectural Search

This script provides guidance and utilities for curating a diverse architectural 
image dataset with proper organization and naming conventions.

Requirements:
- 20-50 diverse architectural photographs
- JPEG format only
- Organized by material types and architectural features
- Consistent naming conventions
"""

import os
import shutil
from pathlib import Path
from PIL import Image
import json
from typing import List, Dict, Any

class DatasetCurator:
    """Handles curation and organization of architectural image dataset."""
    
    def __init__(self, base_dir: str = "images"):
        self.base_dir = Path(base_dir)
        self.categories = {
            "brick_buildings": {
                "description": "Buildings with prominent brick construction",
                "keywords": ["red brick", "brown brick", "brick facade", "brick wall"],
                "target_count": 10
            },
            "glass_steel": {
                "description": "Modern buildings with glass and steel construction",
                "keywords": ["glass facade", "steel frame", "curtain wall", "modern"],
                "target_count": 10
            },
            "stone_facades": {
                "description": "Buildings with natural stone exteriors",
                "keywords": ["limestone", "granite", "sandstone", "stone wall"],
                "target_count": 10
            },
            "mixed_materials": {
                "description": "Buildings combining multiple materials",
                "keywords": ["mixed materials", "concrete and glass", "wood and steel"],
                "target_count": 15
            }
        }
        
    def create_directory_structure(self):
        """Create the organized directory structure for images."""
        for category in self.categories.keys():
            category_path = self.base_dir / category
            category_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {category_path}")
    
    def validate_image(self, image_path: Path) -> bool:
        """Validate that an image meets our requirements."""
        try:
            with Image.open(image_path) as img:
                # Check if it's a valid image
                img.verify()
                
                # Check format
                if img.format != 'JPEG':
                    return False
                    
                # Check minimum dimensions (should be reasonable size)
                width, height = img.size
                if width < 200 or height < 200:
                    return False
                    
                return True
        except Exception:
            return False
    
    def convert_to_jpeg(self, image_path: Path, output_path: Path) -> bool:
        """Convert an image to JPEG format if needed."""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (for PNG with transparency)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Save as JPEG with high quality
                img.save(output_path, 'JPEG', quality=90, optimize=True)
                return True
        except Exception as e:
            print(f"Error converting {image_path}: {e}")
            return False
    
    def generate_filename(self, category: str, description: str, index: int) -> str:
        """Generate consistent filename based on category and description."""
        # Clean description for filename
        clean_desc = description.lower().replace(' ', '_').replace('-', '_')
        clean_desc = ''.join(c for c in clean_desc if c.isalnum() or c == '_')
        
        return f"{category}_{clean_desc}_{index:02d}.jpg"
    
    def organize_images(self, source_dir: Path):
        """Organize images from a source directory into categorized structure."""
        if not source_dir.exists():
            print(f"Source directory {source_dir} does not exist")
            return
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        
        for image_file in source_dir.rglob('*'):
            if image_file.suffix.lower() in image_extensions:
                print(f"Processing: {image_file}")
                
                # You would manually categorize or use AI to categorize
                # For now, prompt user for category
                print(f"Available categories: {list(self.categories.keys())}")
                category = input(f"Which category for {image_file.name}? ").strip()
                
                if category in self.categories:
                    description = input("Brief description (e.g., 'red_brick_house'): ").strip()
                    
                    # Generate new filename
                    existing_count = len(list((self.base_dir / category).glob('*.jpg')))
                    new_filename = self.generate_filename(category, description, existing_count + 1)
                    output_path = self.base_dir / category / new_filename
                    
                    # Convert and copy
                    if self.convert_to_jpeg(image_file, output_path):
                        print(f"Added: {output_path}")
                    else:
                        print(f"Failed to process: {image_file}")
    
    def generate_curation_report(self) -> Dict[str, Any]:
        """Generate a report of the current dataset status."""
        report = {
            "total_images": 0,
            "categories": {},
            "naming_convention": "category_description_index.jpg",
            "format": "JPEG",
            "status": "ready_for_processing"
        }
        
        for category, info in self.categories.items():
            category_path = self.base_dir / category
            images = list(category_path.glob('*.jpg'))
            
            report["categories"][category] = {
                "count": len(images),
                "target": info["target_count"],
                "description": info["description"],
                "keywords": info["keywords"],
                "files": [img.name for img in images]
            }
            report["total_images"] += len(images)
        
        return report
    
    def save_curation_report(self, filename: str = "dataset_curation_report.json"):
        """Save curation report to JSON file."""
        report = self.generate_curation_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Curation report saved to: {filename}")
        return report

def print_curation_guidelines():
    """Print guidelines for manual image curation."""
    guidelines = """
    ARCHITECTURAL IMAGE DATASET CURATION GUIDELINES
    =============================================
    
    TARGET: 20-50 diverse architectural photographs
    
    RECOMMENDED SOURCES (Free/Creative Commons):
    - Unsplash.com (search: architecture, buildings, facade)
    - Pexels.com (architecture category)
    - Pixabay.com (buildings, architecture)
    - Wikimedia Commons (architectural photography)
    
    CATEGORIES TO COLLECT:
    
    1. BRICK BUILDINGS (10 images)
       - Red brick residential houses
       - Brown brick commercial buildings
       - Historic brick structures
       - Modern brick facades
    
    2. GLASS & STEEL (10 images)
       - Modern office buildings
       - Skyscrapers with curtain walls
       - Contemporary residential glass houses
       - Mixed glass and steel structures
    
    3. STONE FACADES (10 images)
       - Limestone buildings
       - Granite structures
       - Sandstone facades
       - Natural stone walls
    
    4. MIXED MATERIALS (15 images)
       - Concrete and glass combinations
       - Wood and steel structures
       - Brick and glass buildings
       - Multi-material modern architecture
    
    QUALITY REQUIREMENTS:
    - High resolution (minimum 800x600 pixels)
    - Clear, well-lit photographs
    - Buildings as primary subject
    - Diverse architectural styles and periods
    - Various angles and perspectives
    
    NAMING CONVENTION:
    category_description_index.jpg
    Examples:
    - brick_buildings_red_brick_house_01.jpg
    - glass_steel_modern_office_tower_01.jpg
    - stone_facades_limestone_courthouse_01.jpg
    - mixed_materials_concrete_glass_museum_01.jpg
    
    TECHNICAL REQUIREMENTS:
    - JPEG format only
    - RGB color space
    - Quality setting 90% or higher
    - No watermarks or text overlays
    """
    
    print(guidelines)

if __name__ == "__main__":
    print("AI Architectural Search - Dataset Curation Tool")
    print("=" * 50)
    
    curator = DatasetCurator()
    
    # Print guidelines
    print_curation_guidelines()
    
    # Create directory structure
    print("\nCreating directory structure...")
    curator.create_directory_structure()
    
    # Generate initial report
    print("\nGenerating curation report...")
    report = curator.save_curation_report()
    
    print(f"\nCurrent dataset status:")
    print(f"Total images: {report['total_images']}")
    for category, info in report['categories'].items():
        print(f"  {category}: {info['count']}/{info['target']} images")
    
    print("\nNext steps:")
    print("1. Download images from recommended sources")
    print("2. Place images in appropriate category folders")
    print("3. Follow naming conventions")
    print("4. Run this script again to validate dataset")
    print("5. Proceed to task 6.2 for offline processing")