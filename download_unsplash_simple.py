#!/usr/bin/env python3
"""
Download high-quality architectural images from Unsplash without API key.

This script uses Unsplash Source (https://source.unsplash.com) to download
random architectural images. No API key required!

Usage: python download_unsplash_simple.py
"""

import requests
import time
from pathlib import Path
from typing import List, Dict
import json


class SimpleUnsplashDownloader:
    """Download architectural images using Unsplash Source."""
    
    def __init__(self, base_dir: str = "images"):
        self.base_dir = Path(base_dir)
        
        # Define categories with specific search terms
        self.categories = {
            "brick_buildings": {
                "queries": ["brick,building", "brick,architecture", "brick,facade"],
                "count": 10
            },
            "glass_steel": {
                "queries": ["glass,building", "modern,architecture", "skyscraper"],
                "count": 10
            },
            "stone_facades": {
                "queries": ["stone,building", "marble,architecture", "granite,building"],
                "count": 10
            },
            "mixed_materials": {
                "queries": ["contemporary,architecture", "modern,building", "architectural,design"],
                "count": 15
            }
        }
    
    def download_image(self, query: str, output_path: Path, width: int = 1200, 
                      height: int = 800) -> bool:
        """Download a random image from Unsplash Source."""
        try:
            # Unsplash Source URL format
            url = f"https://source.unsplash.com/{width}x{height}/?{query}"
            
            print(f"    Downloading from: {query}")
            
            # Download with redirect following
            response = requests.get(url, allow_redirects=True, timeout=30)
            response.raise_for_status()
            
            # Save image
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            # Verify it's a valid image
            if output_path.stat().st_size < 10000:  # Less than 10KB is suspicious
                print(f"    ⚠️  Warning: Image seems too small")
                return False
            
            return True
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
            return False
    
    def download_category(self, category: str, config: Dict) -> int:
        """Download images for a specific category."""
        category_path = self.base_dir / category
        category_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📸 Downloading {category.replace('_', ' ').title()}...")
        
        downloaded = 0
        queries = config["queries"]
        target_count = config["count"]
        
        # Distribute downloads across queries
        images_per_query = (target_count + len(queries) - 1) // len(queries)
        
        image_counter = 1
        
        for query in queries:
            for i in range(images_per_query):
                if downloaded >= target_count:
                    break
                
                filename = f"{category}_{image_counter:02d}.jpg"
                output_path = category_path / filename
                
                if self.download_image(query, output_path):
                    print(f"    ✓ {filename}")
                    downloaded += 1
                    image_counter += 1
                else:
                    print(f"    ✗ Failed: {filename}")
                
                # Rate limiting - be respectful
                time.sleep(2)
        
        print(f"  ✓ Downloaded {downloaded} images")
        return downloaded
    
    def download_all_categories(self) -> Dict:
        """Download images for all categories."""
        print("🏗️  AI Architectural Search - Simple Unsplash Downloader")
        print("=" * 60)
        print("Using Unsplash Source (no API key required)")
        print("This will take several minutes...\n")
        
        results = {
            "source": "Unsplash Source",
            "license": "Unsplash License (free to use)",
            "categories": {}
        }
        
        total_downloaded = 0
        
        for category, config in self.categories.items():
            count = self.download_category(category, config)
            results["categories"][category] = count
            total_downloaded += count
        
        # Save summary
        summary_path = self.base_dir / "download_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Total images downloaded: {total_downloaded}")
        print(f"📄 Summary saved to: {summary_path}")
        
        # Create attribution
        self.create_attribution()
        
        return results
    
    def create_attribution(self):
        """Create attribution file."""
        attribution_path = self.base_dir / "ATTRIBUTIONS.md"
        
        with open(attribution_path, 'w') as f:
            f.write("# Image Attributions\n\n")
            f.write("All images are from [Unsplash](https://unsplash.com) ")
            f.write("and are free to use under the [Unsplash License](https://unsplash.com/license).\n\n")
            f.write("Images were downloaded using Unsplash Source, which provides ")
            f.write("random high-quality photos from their collection.\n\n")
            f.write("## Categories\n\n")
            
            for category in self.categories.keys():
                f.write(f"- **{category.replace('_', ' ').title()}**: ")
                f.write(f"Architectural photography from Unsplash\n")
        
        print(f"📝 Attribution file created: {attribution_path}")


def main():
    """Main execution."""
    print("🏗️  Simple Unsplash Architectural Image Downloader")
    print("=" * 60)
    print("\nThis script will download ~45 high-quality architectural images")
    print("from Unsplash. No API key required!\n")
    
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    try:
        downloader = SimpleUnsplashDownloader()
        results = downloader.download_all_categories()
        
        print("\n" + "=" * 60)
        print("📊 Download Complete!")
        print(f"   Total images: {sum(results['categories'].values())}")
        for category, count in results['categories'].items():
            print(f"   - {category.replace('_', ' ').title()}: {count} images")
        
        print("\n✅ Success!")
        print("\nNext steps:")
        print("1. Review images in 'images/' directory")
        print("2. Run: python run_offline_processing.py")
        print("3. Run: streamlit run app.py")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
