#!/usr/bin/env python3
"""
Test runner script for AI Architectural Search image processing components.
"""
import sys
import subprocess
from pathlib import Path


def run_tests():
    """Run the image processing unit tests."""
    print("Running unit tests for image processing components...")
    print("=" * 60)
    
    # Run pytest with verbose output
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/test_image_processor.py", 
        "-v", 
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n" + "=" * 60)
        print("✅ All tests passed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 60)
        print(f"❌ Tests failed with exit code {e.returncode}")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)