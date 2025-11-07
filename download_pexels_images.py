#!/usr/bin/env python3
"""
Download high-quality architectural images from Pexels.

Pexels offers a free API with generous limits (200 requests/hour, 20,000/month).
Get a free API key at: https://www.pexels.com/api/

Usage:
    1. Get free API key from https://www.pexels.com/api/
    2. Set: export PEXELS_API_KEY="your_key_here"
    3. Run: python download_pexels_images.py
"""

import os
import requests
import time
from pathlib import Path
from typing import List, Dict
import json


class PexelsImageDownloader:
    """Download architectural images from Pexels API."""
    
    def __init__(self, api_key: str = None, base_dir: str = "images"):
        self.api_key = api_key or os.getenv('PEXELS_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Pexels API key required. Get one free at https://www.pexels.com/api/\n"
                "Set it with: export PEXELS_API_KEY='your_key_here'"
            )
        
        self.base_dir = Path(base_dir)
        self.api_base = "https://api.pexels.com/v1"
        self.headers = {
            "Authorization": self.api_key
        }
        
        # Define search queries for architectural categories
        self.categories = {
            "brick_buildings": {
                "queries": [
                    "brick building",
                    "brick architecture",
                    "red brick facade"
                ],
                "per_query": 4
            },
            "glass_steel": {
                "queries": [
                    "glass building",
                    "modern skyscraper",
                    "steel architecture"
                ],
                "per_query": 4
            },
            "stone_facades": {
                "queries": [
                    "stone building",
                    "marble architecture",
                    "granite facade"
                ],
                "per_query": 4
            },
            "mixed_materials": {
                "queries": [
                    "contemporary architecture",
                    "modern building design",
                    "architectural facade"
                ],
                "per_query": 5
            }
        }
    
    def search_photos(self, query: str, per_page: int = 15) -> List[Dict]:
        """Search for photos on Pexels."""
        url = f"{self.api_base}/search"
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": "landscape"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('photos', [])
        except requests.exceptions.RequestException as e:
            print(f"    ✗ Error searching '{query}': {e}")
            return []
    
    def download_image(self, photo: Dict, output_path: Path) -> bool:
        """Download a single image."""
        try:
            # Use 'large' size (good quality, reasonable file size)
            image_url = photo['src']['large']
            
            response = requests.get(image_url, stream=True, timeout=30)
            response.raise_for_status()
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
            
        except Exception as e:
            print(f"    ✗ Download error: {e}")
            return False
    
    def download_category(self, category: str, config: Dict) -> List[Dict]:
        """Download images for a category."""
        category_path = self.base_dir / category
        category_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📸 {category.replace('_', ' ').title()}")
        
        downloaded_images = []
        image_counter = 1
        
        for query in config["queries"]:
            print(f"  Searching: {query}")
            photos = self.search_photos(query, per_page=config["per_query"])
            
            for photo in photos[:config["per_query"]]:
                filename = f"{category}_{image_counter:02d}.jpg"
                output_path = category_path / filename
                
                if self.download_image(photo, output_path):
                    image_info = {
                        "filename": filename,
                        "category": category,
                        "pexels_id": photo['id'],
                        "photographer": photo['photographer'],
                        "photographer_url": photo['photographer_url'],
                        "photo_url": photo['url'],
                        "description": photo.get('alt', ''),
                        "width": photo['width'],
                        "height": photo['height']
                    }
                    downloaded_images.append(image_info)
                    print(f"    ✓ {filename} by {photo['photographer']}")
                    image_counter += 1
                
                time.sleep(0.5)  # Rate limiting
        
        return downloaded_images
    
    def download_all(self) -> Dict:
        """Download all categories."""
        print("🏗️  Pexels Architectural Image Downloader")
        print("=" * 60)
        
        metadata = {
            "source": "Pexels",
            "license": "Pexels License (free to use)",
            "attribution_required": False,
            "categories": {}
        }
        
        total = 0
        
        for category, config in self.categories.items():
            images = self.download_category(category, config)
            metadata["categories"][category] = images
            total += len(images)
            print(f"  ✓ {len(images)} images downloaded")
        
        # Save metadata
        metadata_path = self.base_dir / "pexels_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n✅ Total: {total} images")
        print(f"📄 Metadata: {metadata_path}")
        
        self.create_attribution(metadata)
        
        return metadata
    
    def create_attribution(self, metadata: Dict):
        """Create attribution file."""
        path = self.base_dir / "ATTRIBUTIONS.md"
        
        with open(path, 'w') as f:
            f.write("# Image Attributions\n\n")
            f.write("Images from [Pexels](https://www.pexels.com) - ")
            f.write("Free to use under [Pexels License](https://www.pexels.com/license/).\n\n")
            
            for category, images in metadata["categories"].items():
                f.write(f"## {category.replace('_', ' ').title()}\n\n")
                for img in images:
                    f.write(f"- **{img['filename']}** by [{img['photographer']}]({img['photographer_url']})\n")
                f.write("\n")
        
        print(f"📝 Attribution: {path}")


def main():
    """Main function."""
    api_key = os.getenv('PEXELS_API_KEY')
    
    if not api_key:
        print("❌ Pexels API key not found!\n")
        print("Get a free API key:")
        print("1. Go to https://www.pexels.com/api/")
        print("2. Sign up (free)")
        print("3. Copy your API key")
        print("4. Run: export PEXELS_API_KEY='your_key_here'")
        print("\nThen run this script again.")
        return
    
    try:
        downloader = PexelsImageDownloader(api_key=api_key)
        
        print("\nDownloading ~45 architectural images...")
        print("This will take a few minutes.\n")
        
        metadata = downloader.download_all()
        
        print("\n" + "=" * 60)
        print("📊 Summary:")
        for cat, images in metadata["categories"].items():
            print(f"   {cat.replace('_', ' ').title()}: {len(images)} images")
        
        print("\n✅ Complete!")
        print("\nNext steps:")
        print("1. Review images in 'images/' directory")
        print("2. Run: python run_offline_processing.py")
        print("3. Run: streamlit run app.py")
        
    except ValueError as e:
        print(f"\n❌ {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
