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

# Start Streamlit programmatically to avoid Railway's command injection issues
if __name__ == "__main__":
    import streamlit.web.cli as stcli
    
    # Get port from Railway or use default
    port = int(os.environ.get('PORT', 8501))
    
    # Configure Streamlit arguments
    sys.argv = [
        "streamlit",
        "run",
        __file__,
        "--server.port", str(port),
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    
    # Start Streamlit
    stcli.main()

# This is the actual Streamlit app content
from src.web.app import main
main()