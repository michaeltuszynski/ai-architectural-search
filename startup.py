#!/usr/bin/env python3
"""
Optimized startup script for cloud deployment.
Handles model preloading and system optimization.
"""

import os
import sys
import time
import logging
import psutil
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import get_config


def check_system_resources():
    """Check available system resources and log warnings."""
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('.')
    
    logging.info(f"System Resources:")
    logging.info(f"  Memory: {memory.total / (1024**3):.1f}GB total, {memory.available / (1024**3):.1f}GB available")
    logging.info(f"  Disk: {disk.total / (1024**3):.1f}GB total, {disk.free / (1024**3):.1f}GB free")
    logging.info(f"  CPU cores: {psutil.cpu_count()}")
    
    # Warn about low resources
    if memory.available < 1.5 * 1024**3:  # Less than 1.5GB
        logging.warning(f"Low memory available: {memory.available / (1024**3):.1f}GB")
    
    if disk.free < 1 * 1024**3:  # Less than 1GB
        logging.warning(f"Low disk space: {disk.free / (1024**3):.1f}GB")


def optimize_for_cloud():
    """Apply cloud-specific optimizations."""
    config = get_config()
    
    # Set PyTorch to use CPU only if configured
    if config.cpu_only_mode:
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        logging.info("Configured for CPU-only mode")
    
    # Memory optimization settings
    if config.memory_optimization:
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
        os.environ['OMP_NUM_THREADS'] = '2'
        logging.info("Applied memory optimization settings")
    
    # Disable unnecessary features for production
    if config.is_production():
        os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
        os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
        os.environ['STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION'] = 'false'
        logging.info("Applied production optimizations")


def preload_models():
    """Preload models to reduce cold start time."""
    try:
        logging.info("Preloading CLIP model...")
        start_time = time.time()
        
        # Import and initialize model manager
        from src.processors.model_manager import ModelManager
        config = get_config()
        
        model_manager = ModelManager(config)
        model_manager.load_model()  # This will cache the model
        
        load_time = time.time() - start_time
        logging.info(f"Model preloaded successfully in {load_time:.2f} seconds")
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to preload models: {e}")
        return False


def verify_deployment():
    """Verify that the deployment is ready."""
    try:
        # Check if required files exist
        config = get_config()
        
        if not Path(config.image_directory).exists():
            logging.error(f"Images directory not found: {config.image_directory}")
            return False
        
        if not Path(config.metadata_file).exists():
            logging.error(f"Metadata file not found: {config.metadata_file}")
            return False
        
        # Count available images
        image_count = len(list(Path(config.image_directory).rglob("*.jpg")))
        logging.info(f"Found {image_count} images in dataset")
        
        if image_count == 0:
            logging.warning("No images found in dataset")
            return False
        
        logging.info("Deployment verification successful")
        return True
        
    except Exception as e:
        logging.error(f"Deployment verification failed: {e}")
        return False


def main():
    """Main startup function."""
    # Configure logging
    config = get_config()
    
    logging.info("Starting AI Architectural Search System...")
    logging.info(f"Environment: {config.environment}")
    logging.info(f"Memory optimization: {config.memory_optimization}")
    logging.info(f"CPU only mode: {config.cpu_only_mode}")
    
    # Check system resources
    check_system_resources()
    
    # Apply optimizations
    optimize_for_cloud()
    
    # Verify deployment
    if not verify_deployment():
        logging.error("Deployment verification failed")
        sys.exit(1)
    
    # Preload models (optional, continue even if it fails)
    if config.enable_model_caching:
        preload_models()
    
    logging.info("Startup completed successfully")
    
    # Start the Streamlit application
    import subprocess
    
    port = os.getenv('PORT', '8501')
    cmd = [
        'streamlit', 'run', 'src/web/app.py',
        '--server.port', port,
        '--server.address', '0.0.0.0',
        '--server.headless', 'true'
    ]
    
    logging.info(f"Starting Streamlit on port {port}")
    subprocess.run(cmd)


if __name__ == "__main__":
    main()