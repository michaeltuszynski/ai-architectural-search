#!/usr/bin/env python3
"""
Startup script for the AI Architectural Search Streamlit application.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'streamlit',
        'torch',
        'transformers', 
        'clip-by-openai',
        'pillow',
        'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        logger.info("Please install missing packages with: pip install -r requirements.txt")
        return False
    
    return True


def check_image_directory():
    """Check if image directory exists and has images."""
    image_dir = Path("images")
    
    if not image_dir.exists():
        logger.warning(f"Image directory '{image_dir}' does not exist")
        logger.info("Creating image directory...")
        image_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        subdirs = ["brick_buildings", "glass_steel", "stone_facades", "mixed_materials"]
        for subdir in subdirs:
            (image_dir / subdir).mkdir(exist_ok=True)
        
        logger.warning("Image directory created but is empty. Please add images before running the application.")
        return False
    
    # Count images in directory
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    image_count = 0
    
    for ext in image_extensions:
        image_count += len(list(image_dir.rglob(f"*{ext}")))
        image_count += len(list(image_dir.rglob(f"*{ext.upper()}")))
    
    if image_count == 0:
        logger.warning("No images found in image directory")
        logger.info("Please add architectural images to the 'images' directory before running the application")
        return False
    
    logger.info(f"Found {image_count} images in directory")
    return True


def check_metadata():
    """Check if image metadata exists."""
    metadata_file = Path("image_metadata.json")
    
    if not metadata_file.exists():
        logger.warning("Image metadata file not found")
        logger.info("You may need to run the offline image processing first")
        logger.info("Run: python -m src.processors.offline_processor")
        return False
    
    logger.info("Image metadata file found")
    return True


def run_streamlit_app():
    """Run the Streamlit application."""
    app_path = Path("src/web/app.py")
    
    if not app_path.exists():
        logger.error(f"Application file not found: {app_path}")
        return False
    
    logger.info("Starting Streamlit application...")
    
    # Streamlit command
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        str(app_path),
        "--server.port", "8501",
        "--server.address", "localhost",
        "--browser.gatherUsageStats", "false"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Streamlit application: {e}")
        return False
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        return True


def main():
    """Main startup function."""
    logger.info("AI Architectural Search - Starting Application")
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed")
        sys.exit(1)
    
    # Check image directory
    if not check_image_directory():
        logger.error("Image directory check failed")
        logger.info("Please add images to the 'images' directory and run offline processing")
        sys.exit(1)
    
    # Check metadata (warning only)
    if not check_metadata():
        logger.warning("Metadata check failed - application may not work properly")
    
    # Run the application
    success = run_streamlit_app()
    
    if success:
        logger.info("Application finished successfully")
    else:
        logger.error("Application failed to start")
        sys.exit(1)


if __name__ == "__main__":
    main()