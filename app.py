#!/usr/bin/env python3
"""
Entry point for cloud deployment (Hugging Face Spaces, Railway, etc.).
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(current_dir))

# Set environment variables for cloud deployment
os.environ.setdefault('ENVIRONMENT', 'production')
os.environ.setdefault('MEMORY_OPTIMIZATION', 'true')
os.environ.setdefault('CPU_ONLY_MODE', 'true')
os.environ.setdefault('LOG_LEVEL', 'WARNING')
os.environ.setdefault('MAX_RESULTS', '5')
os.environ.setdefault('BATCH_SIZE', '16')
os.environ.setdefault('MAX_IMAGE_SIZE', '256,256')

# Handle Railway's PORT environment variable
if 'PORT' in os.environ:
    # Railway sets PORT - configure Streamlit to use it
    os.environ['STREAMLIT_SERVER_PORT'] = os.environ['PORT']
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'

# Import and run the main application
if __name__ == "__main__":
    from src.web.app import main
    main()