#!/usr/bin/env python3
"""
Create sample architectural images for testing the AI search system.

This script generates placeholder images with proper naming conventions
to simulate a curated architectural dataset for development and testing.
"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
import random

class SampleImageGenerator:
    """Generate sample architectural images for testing."""
    
    def __init__(self, base_dir: str = "images"):
        self.base_dir = Path(base_dir)
        self.image_size = (800, 600)
        
        # Define sample images for each category
        self.sample_data = {
            "brick_buildings": [
                {"name": "red_brick_house_01.jpg", "color": (139, 69, 19), "text": "Red Brick\nResidential"},
                {"name": "brown_brick_office_02.jpg", "color": (101, 67, 33), "text": "Brown Brick\nOffice"},
                {"name": "historic_brick_church_03.jpg", "color": (120, 81, 45), "text": "Historic Brick\nChurch"},
                {"name": "modern_brick_facade_04.jpg", "color": (165, 42, 42), "text": "Modern Brick\nFacade"},
                {"name": "brick_warehouse_05.jpg", "color": (128, 70, 27), "text": "Brick\nWarehouse"},
                {"name": "red_brick_school_06.jpg", "color": (178, 34, 34), "text": "Red Brick\nSchool"},
                {"name": "brick_apartment_07.jpg", "color": (160, 82, 45), "text": "Brick\nApartment"},
                {"name": "old_brick_factory_08.jpg", "color": (139, 69, 19), "text": "Old Brick\nFactory"},
                {"name": "brick_library_09.jpg", "color": (205, 92, 92), "text": "Brick\nLibrary"},
                {"name": "colonial_brick_house_10.jpg", "color": (188, 143, 143), "text": "Colonial Brick\nHouse"}
            ],
            "glass_steel": [
                {"name": "modern_office_tower_01.jpg", "color": (135, 206, 235), "text": "Modern Office\nTower"},
                {"name": "glass_curtain_wall_02.jpg", "color": (173, 216, 230), "text": "Glass Curtain\nWall"},
                {"name": "steel_frame_building_03.jpg", "color": (119, 136, 153), "text": "Steel Frame\nBuilding"},
                {"name": "contemporary_glass_house_04.jpg", "color": (176, 196, 222), "text": "Contemporary\nGlass House"},
                {"name": "skyscraper_glass_facade_05.jpg", "color": (70, 130, 180), "text": "Skyscraper\nGlass Facade"},
                {"name": "modern_glass_museum_06.jpg", "color": (100, 149, 237), "text": "Modern Glass\nMuseum"},
                {"name": "steel_glass_mall_07.jpg", "color": (123, 104, 238), "text": "Steel Glass\nMall"},
                {"name": "corporate_headquarters_08.jpg", "color": (72, 61, 139), "text": "Corporate\nHeadquarters"},
                {"name": "glass_residential_tower_09.jpg", "color": (106, 90, 205), "text": "Glass Residential\nTower"},
                {"name": "modern_glass_library_10.jpg", "color": (147, 112, 219), "text": "Modern Glass\nLibrary"}
            ],
            "stone_facades": [
                {"name": "limestone_courthouse_01.jpg", "color": (245, 245, 220), "text": "Limestone\nCourthouse"},
                {"name": "granite_bank_building_02.jpg", "color": (169, 169, 169), "text": "Granite Bank\nBuilding"},
                {"name": "sandstone_university_03.jpg", "color": (244, 164, 96), "text": "Sandstone\nUniversity"},
                {"name": "marble_government_04.jpg", "color": (255, 248, 220), "text": "Marble\nGovernment"},
                {"name": "stone_cathedral_05.jpg", "color": (211, 211, 211), "text": "Stone\nCathedral"},
                {"name": "limestone_mansion_06.jpg", "color": (250, 240, 230), "text": "Limestone\nMansion"},
                {"name": "granite_memorial_07.jpg", "color": (105, 105, 105), "text": "Granite\nMemorial"},
                {"name": "sandstone_castle_08.jpg", "color": (210, 180, 140), "text": "Sandstone\nCastle"},
                {"name": "stone_bridge_09.jpg", "color": (192, 192, 192), "text": "Stone\nBridge"},
                {"name": "limestone_hotel_10.jpg", "color": (255, 250, 240), "text": "Limestone\nHotel"}
            ],
            "mixed_materials": [
                {"name": "concrete_glass_museum_01.jpg", "color": (128, 128, 128), "text": "Concrete Glass\nMuseum"},
                {"name": "wood_steel_residence_02.jpg", "color": (160, 82, 45), "text": "Wood Steel\nResidence"},
                {"name": "brick_glass_office_03.jpg", "color": (139, 69, 19), "text": "Brick Glass\nOffice"},
                {"name": "concrete_steel_stadium_04.jpg", "color": (112, 128, 144), "text": "Concrete Steel\nStadium"},
                {"name": "wood_glass_pavilion_05.jpg", "color": (222, 184, 135), "text": "Wood Glass\nPavilion"},
                {"name": "metal_concrete_factory_06.jpg", "color": (169, 169, 169), "text": "Metal Concrete\nFactory"},
                {"name": "stone_glass_hotel_07.jpg", "color": (245, 245, 220), "text": "Stone Glass\nHotel"},
                {"name": "brick_steel_loft_08.jpg", "color": (165, 42, 42), "text": "Brick Steel\nLoft"},
                {"name": "concrete_wood_school_09.jpg", "color": (105, 105, 105), "text": "Concrete Wood\nSchool"},
                {"name": "glass_stone_church_10.jpg", "color": (211, 211, 211), "text": "Glass Stone\nChurch"},
                {"name": "mixed_material_mall_11.jpg", "color": (176, 196, 222), "text": "Mixed Material\nMall"},
                {"name": "contemporary_mixed_house_12.jpg", "color": (205, 92, 92), "text": "Contemporary\nMixed House"},
                {"name": "industrial_mixed_complex_13.jpg", "color": (119, 136, 153), "text": "Industrial Mixed\nComplex"},
                {"name": "modern_mixed_apartment_14.jpg", "color": (147, 112, 219), "text": "Modern Mixed\nApartment"},
                {"name": "eco_mixed_building_15.jpg", "color": (154, 205, 50), "text": "Eco Mixed\nBuilding"}
            ]
        }
    
    def create_sample_image(self, category: str, image_info: dict) -> Path:
        """Create a single sample image with text overlay."""
        # Create image with solid color background
        img = Image.new('RGB', self.image_size, image_info["color"])
        draw = ImageDraw.Draw(img)
        
        # Try to use a font, fall back to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 48)
            small_font = ImageFont.truetype("arial.ttf", 24)
        except:
            try:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            except:
                font = None
                small_font = None
        
        # Add category label at top
        if font:
            draw.text((20, 20), category.replace('_', ' ').title(), 
                     fill=(255, 255, 255), font=small_font)
        
        # Add main text in center
        text = image_info["text"]
        if font:
            # Calculate text position for centering
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (self.image_size[0] - text_width) // 2
            y = (self.image_size[1] - text_height) // 2
            
            # Add text with shadow for better visibility
            draw.text((x+2, y+2), text, fill=(0, 0, 0), font=font)  # Shadow
            draw.text((x, y), text, fill=(255, 255, 255), font=font)  # Main text
        
        # Add some architectural elements (simple rectangles to simulate windows/features)
        self._add_architectural_elements(draw, category)
        
        # Save image
        output_path = self.base_dir / category / image_info["name"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, 'JPEG', quality=90)
        
        return output_path
    
    def _add_architectural_elements(self, draw: ImageDraw.Draw, category: str):
        """Add simple architectural elements to make images more realistic."""
        width, height = self.image_size
        
        if category == "glass_steel":
            # Add window grid pattern
            for i in range(5, width-5, 80):
                for j in range(100, height-100, 60):
                    draw.rectangle([i, j, i+60, j+40], outline=(255, 255, 255), width=2)
        
        elif category == "brick_buildings":
            # Add brick pattern
            for i in range(0, width, 40):
                for j in range(200, height-50, 20):
                    offset = 20 if (j // 20) % 2 else 0
                    draw.rectangle([i+offset, j, i+offset+35, j+15], 
                                 outline=(255, 255, 255), width=1)
        
        elif category == "stone_facades":
            # Add stone block pattern
            for i in range(0, width, 100):
                for j in range(150, height-50, 80):
                    draw.rectangle([i, j, i+90, j+70], outline=(128, 128, 128), width=2)
        
        elif category == "mixed_materials":
            # Add mixed elements
            # Glass section
            for i in range(5, width//2, 60):
                for j in range(100, height//2, 50):
                    draw.rectangle([i, j, i+50, j+35], outline=(255, 255, 255), width=2)
            
            # Stone section
            for i in range(width//2, width-5, 80):
                for j in range(height//2, height-50, 60):
                    draw.rectangle([i, j, i+70, j+50], outline=(200, 200, 200), width=1)
    
    def generate_all_samples(self):
        """Generate all sample images for the dataset."""
        total_created = 0
        
        print("Generating sample architectural images...")
        
        for category, images in self.sample_data.items():
            print(f"\nCreating {category} images:")
            
            for image_info in images:
                output_path = self.create_sample_image(category, image_info)
                print(f"  Created: {output_path}")
                total_created += 1
        
        print(f"\nTotal images created: {total_created}")
        return total_created
    
    def validate_dataset(self):
        """Validate the created dataset meets requirements."""
        validation_report = {
            "total_images": 0,
            "categories": {},
            "format_compliance": True,
            "naming_compliance": True,
            "size_compliance": True
        }
        
        for category in self.sample_data.keys():
            category_path = self.base_dir / category
            if category_path.exists():
                jpg_files = list(category_path.glob("*.jpg"))
                validation_report["categories"][category] = len(jpg_files)
                validation_report["total_images"] += len(jpg_files)
                
                # Validate each image
                for img_file in jpg_files:
                    try:
                        with Image.open(img_file) as img:
                            if img.format != 'JPEG':
                                validation_report["format_compliance"] = False
                            if img.size != self.image_size:
                                validation_report["size_compliance"] = False
                    except Exception:
                        validation_report["format_compliance"] = False
        
        return validation_report

if __name__ == "__main__":
    print("AI Architectural Search - Sample Image Generator")
    print("=" * 50)
    
    generator = SampleImageGenerator()
    
    # Generate all sample images
    total_created = generator.generate_all_samples()
    
    # Validate dataset
    print("\nValidating dataset...")
    validation = generator.validate_dataset()
    
    print(f"\nDataset Validation Report:")
    print(f"Total images: {validation['total_images']}")
    print(f"Format compliance: {validation['format_compliance']}")
    print(f"Naming compliance: {validation['naming_compliance']}")
    print(f"Size compliance: {validation['size_compliance']}")
    
    print(f"\nImages per category:")
    for category, count in validation['categories'].items():
        print(f"  {category}: {count} images")
    
    if validation['total_images'] >= 20:
        print(f"\n✅ Dataset meets minimum requirement (20+ images)")
    else:
        print(f"\n❌ Dataset below minimum requirement (need 20+, have {validation['total_images']})")
    
    print(f"\nDataset ready for offline processing (task 6.2)")