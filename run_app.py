#!/usr/bin/env python3
"""
Proper entry point that runs Streamlit as a module to preserve package structure.
"""
import sys
import os
from pathlib import Path

# Set up environment
os.environ.setdefault('ENVIRONMENT', 'production')
os.environ.setdefault('MEMORY_OPTIMIZATION', 'true')
os.environ.setdefault('CPU_ONLY_MODE', 'true')
os.environ.setdefault('LOG_LEVEL', 'WARNING')
os.environ.setdefault('MAX_RESULTS', '5')
os.environ.setdefault('BATCH_SIZE', '16')
os.environ.setdefault('MAX_IMAGE_SIZE', '256,256')

# Handle Railway's PORT
if 'PORT' in os.environ:
    port = os.environ['PORT']
    os.environ['STREAMLIT_SERVER_PORT'] = port
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'

# Run streamlit with proper module path
if __name__ == "__main__":
    from streamlit.web import cli as stcli
    sys.argv = ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
    if 'PORT' in os.environ:
        sys.argv.extend(["--server.port", os.environ['PORT']])
    sys.exit(stcli.main())
