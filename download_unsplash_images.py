#!/usr/bin/env python3
"""
Download high-quality architectural images from Unsplash for the AI search demo.

This script uses the Unsplash API to download real architectural photography
organized by material type and building style.

Usage:
    1. Get a free API key from https://unsplash.com/developers
    2. Set environment variable: export UNSPLASH_ACCESS_KEY="your_key_here"
    3. Run: python download_unsplash_images.py
"""

import os
import requests
import time
from pathlib import Path
from typing import List, Dict
import json


class UnsplashImageDownloader:
    """Download architectural images from Unsplash API."""
    
    def __init__(self, access_key: str = None, base_dir: str = "images"):
        self.access_key = access_key or os.getenv('UNSPLASH_ACCESS_KEY')
        if not self.access_key:
            raise ValueError(
                "Unsplash API key required. Get one at https://unsplash.com/developers\n"
                "Set it with: export UNSPLASH_ACCESS_KEY='your_key_here'"
            )
        
        self.base_dir = Path(base_dir)
        self.api_base = "https://api.unsplash.com"
        self.headers = {
            "Authorization": f"Client-ID {self.access_key}"
        }
        
        # Define search queries for different architectural categories
        self.categories = {
            "brick_buildings": [
                "brick building architecture",
                "red brick facade",
                "brick apartment building",
                "historic brick architecture",
                "modern brick building"
            ],
            "glass_steel": [
                "glass steel building",
                "modern office tower",
                "glass facade architecture",
                "contemporary skyscraper",
                "steel frame building"
            ],
            "stone_facades": [
                "stone building facade",
                "limestone architecture",
                "granite building",
                "marble architecture",
                "stone cathedral"
            ],
            "mixed_materials": [
                "mixed material architecture",
                "contemporary building design",
                "modern architecture facade",
                "architectural detail materials",
                "innovative building design"
            ]
        }
    
    def search_photos(self, query: str, per_page: int = 10) -> List[Dict]:
        """Search for photos on Unsplash."""
        url = f"{self.api_base}/search/photos"
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": "landscape",
            "content_filter": "high"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except requests.exceptions.RequestException as e:
            print(f"Error searching for '{query}': {e}")
            return []
    
    def download_image(self, photo: Dict, output_path: Path) -> bool:
        """Download a single image from Unsplash."""
        try:
            # Use the 'regular' size (good quality, reasonable file size)
            image_url = photo['urls']['regular']
            
            # Download image
            response = requests.get(image_url, stream=True)
            response.raise_for_status()
            
            # Save image
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Trigger download tracking (required by Unsplash API terms)
            if 'links' in photo and 'download_location' in photo['links']:
                requests.get(
                    photo['links']['download_location'],
                    headers=self.headers
                )
            
            return True
            
        except Exception as e:
            print(f"Error downloading image: {e}")
            return False
    
    def download_category(self, category: str, queries: List[str], 
                         images_per_query: int = 2) -> List[Dict]:
        """Download images for a specific category."""
        category_path = self.base_dir / category
        category_path.mkdir(parents=True, exist_ok=True)
        
        downloaded_images = []
        image_counter = 1
        
        print(f"\n📸 Downloading {category.replace('_', ' ').title()} images...")
        
        for query in queries:
            print(f"  Searching: {query}")
            photos = self.search_photos(query, per_page=images_per_query)
            
            for photo in photos[:images_per_query]:
                # Create filename
                photo_id = photo['id']
                filename = f"{category}_{image_counter:02d}.jpg"
                output_path = category_path / filename
                
                # Download image
                if self.download_image(photo, output_path):
                    # Store metadata
                    image_info = {
                        "filename": filename,
                        "category": category,
                        "unsplash_id": photo_id,
                        "photographer": photo['user']['name'],
                        "photographer_url": photo['user']['links']['html'],
                        "photo_url": photo['links']['html'],
                        "description": photo.get('description') or photo.get('alt_description', ''),
                        "width": photo['width'],
                        "height": photo['height']
                    }
                    downloaded_images.append(image_info)
                    
                    print(f"    ✓ Downloaded: {filename} by {photo['user']['name']}")
                    image_counter += 1
                else:
                    print(f"    ✗ Failed to download image")
                
                # Rate limiting - be nice to the API
                time.sleep(1)
        
        return downloaded_images
    
    def download_all_categories(self, images_per_query: int = 2) -> Dict:
        """Download images for all categories."""
        print("🏗️  AI Architectural Search - Unsplash Image Downloader")
        print("=" * 60)
        
        all_metadata = {
            "source": "Unsplash",
            "license": "Unsplash License (free to use)",
            "attribution_required": True,
            "categories": {}
        }
        
        total_downloaded = 0
        
        for category, queries in self.categories.items():
            images = self.download_category(category, queries, images_per_query)
            all_metadata["categories"][category] = images
            total_downloaded += len(images)
            
            print(f"  ✓ Downloaded {len(images)} images for {category}")
        
        # Save metadata
        metadata_path = self.base_dir / "unsplash_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(all_metadata, f, indent=2)
        
        print(f"\n✅ Total images downloaded: {total_downloaded}")
        print(f"📄 Metadata saved to: {metadata_path}")
        
        # Create attribution file
        self.create_attribution_file(all_metadata)
        
        return all_metadata
    
    def create_attribution_file(self, metadata: Dict):
        """Create an attribution file for Unsplash photographers."""
        attribution_path = self.base_dir / "ATTRIBUTIONS.md"
        
        with open(attribution_path, 'w') as f:
            f.write("# Image Attributions\n\n")
            f.write("All images are from [Unsplash](https://unsplash.com) and are free to use under the [Unsplash License](https://unsplash.com/license).\n\n")
            f.write("## Photographers\n\n")
            
            for category, images in metadata["categories"].items():
                f.write(f"### {category.replace('_', ' ').title()}\n\n")
                for img in images:
                    f.write(f"- **{img['filename']}** by [{img['photographer']}]({img['photographer_url']})\n")
                    f.write(f"  - Photo: {img['photo_url']}\n")
                    if img['description']:
                        f.write(f"  - Description: {img['description']}\n")
                    f.write("\n")
        
        print(f"📝 Attribution file created: {attribution_path}")
    
    def validate_downloads(self) -> Dict:
        """Validate downloaded images."""
        validation = {
            "total_images": 0,
            "categories": {},
            "all_valid": True
        }
        
        for category in self.categories.keys():
            category_path = self.base_dir / category
            if category_path.exists():
                jpg_files = list(category_path.glob("*.jpg"))
                validation["categories"][category] = len(jpg_files)
                validation["total_images"] += len(jpg_files)
        
        return validation


def main():
    """Main execution function."""
    print("🏗️  Unsplash Architectural Image Downloader")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv('UNSPLASH_ACCESS_KEY')
    if not api_key:
        print("\n❌ ERROR: Unsplash API key not found!")
        print("\nTo get started:")
        print("1. Go to https://unsplash.com/developers")
        print("2. Create a free account and register a new application")
        print("3. Copy your Access Key")
        print("4. Set it as an environment variable:")
        print("   export UNSPLASH_ACCESS_KEY='your_access_key_here'")
        print("\nThen run this script again.")
        return
    
    try:
        # Create downloader
        downloader = UnsplashImageDownloader(access_key=api_key)
        
        # Download images (2 per query = ~10 images per category = ~40 total)
        print("\nStarting download...")
        print("This will download approximately 40 high-quality architectural images.")
        print("Please wait, this may take a few minutes...\n")
        
        metadata = downloader.download_all_categories(images_per_query=2)
        
        # Validate
        validation = downloader.validate_downloads()
        
        print("\n" + "=" * 60)
        print("📊 Download Summary:")
        print(f"   Total images: {validation['total_images']}")
        for category, count in validation['categories'].items():
            print(f"   - {category.replace('_', ' ').title()}: {count} images")
        
        print("\n✅ Download complete!")
        print("\nNext steps:")
        print("1. Review the images in the 'images/' directory")
        print("2. Run offline processing to generate embeddings:")
        print("   python run_offline_processing.py")
        print("3. Start the web app:")
        print("   streamlit run app.py")
        
    except ValueError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
