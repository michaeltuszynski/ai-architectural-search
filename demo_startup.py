#!/usr/bin/env python3
"""
Demo startup script for AI Architectural Search System.

This script provides an easy way to start the demo with proper validation
and user-friendly error handling.
"""

import os
import sys
import time
import subprocess
import logging
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models.config import AppConfig
from src.processors.search_engine import SearchEngine


class DemoLauncher:
    """
    Demo launcher that validates system readiness and starts the Streamlit application.
    """
    
    def __init__(self):
        """Initialize the demo launcher."""
        self.logger = logging.getLogger(__name__)
        self.config = None
        self.search_engine = None
    
    def validate_system_requirements(self) -> bool:
        """
        Validate that all system requirements are met.
        
        Returns:
            bool: True if system is ready, False otherwise
        """
        print("🔍 Validating System Requirements...")
        print("-" * 40)
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8 or higher is required")
            return False
        print(f"✅ Python version: {sys.version.split()[0]}")
        
        # Check required packages
        required_packages = [
            'streamlit',
            'torch', 
            'transformers',
            'clip',
            'PIL',
            'numpy'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                if package == 'clip':
                    import clip
                elif package == 'PIL':
                    from PIL import Image
                else:
                    __import__(package)
                print(f"✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package}")
        
        if missing_packages:
            print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
            print("Please install with: pip install -r requirements.txt")
            return False
        
        # Check image directory
        image_dir = Path("images")
        if not image_dir.exists():
            print("❌ Image directory not found")
            return False
        
        # Count images
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        image_count = 0
        for ext in image_extensions:
            image_count += len(list(image_dir.rglob(f"*{ext}")))
            image_count += len(list(image_dir.rglob(f"*{ext.upper()}")))
        
        if image_count == 0:
            print("❌ No images found in image directory")
            return False
        print(f"✅ Found {image_count} images")
        
        # Check metadata
        metadata_file = Path("image_metadata.json")
        if not metadata_file.exists():
            print("❌ Image metadata not found")
            print("Please run: python run_offline_processing.py")
            return False
        print("✅ Image metadata found")
        
        return True
    
    def validate_search_system(self) -> bool:
        """
        Validate that the search system is working correctly.
        
        Returns:
            bool: True if search system is ready, False otherwise
        """
        print("\n🧪 Validating Search System...")
        print("-" * 40)
        
        try:
            # Load configuration
            self.config = AppConfig.load_config()
            print("✅ Configuration loaded")
            
            # Initialize search engine
            print("🔄 Initializing search engine...")
            self.search_engine = SearchEngine(self.config)
            
            # Validate readiness
            readiness = self.search_engine.validate_search_readiness()
            
            if not readiness['ready']:
                print("❌ Search system not ready:")
                for issue in readiness['issues']:
                    print(f"   • {issue}")
                return False
            
            print("✅ Search engine initialized")
            
            # Test a simple query
            print("🔄 Testing search functionality...")
            start_time = time.time()
            results, _ = self.search_engine.search("brick buildings")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if results:
                print(f"✅ Search test passed ({len(results)} results in {response_time:.3f}s)")
            else:
                print("⚠️  Search test returned no results (system may still work)")
            
            # Get system statistics
            stats = readiness['statistics']
            print(f"✅ System ready: {stats['total_images']} images indexed")
            
            return True
            
        except Exception as e:
            print(f"❌ Search system validation failed: {e}")
            return False
    
    def start_streamlit_app(self, port: int = 8501, host: str = "localhost") -> bool:
        """
        Start the Streamlit application.
        
        Args:
            port: Port to run the application on
            host: Host address to bind to
            
        Returns:
            bool: True if startup successful, False otherwise
        """
        print(f"\n🚀 Starting Demo Application...")
        print("-" * 40)
        
        app_path = Path("src/web/app.py")
        if not app_path.exists():
            print(f"❌ Application file not found: {app_path}")
            return False
        
        print(f"🌐 Starting Streamlit on http://{host}:{port}")
        print("📝 Use Ctrl+C to stop the application")
        print()
        
        # Streamlit command
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            str(app_path),
            "--server.port", str(port),
            "--server.address", host,
            "--browser.gatherUsageStats", "false",
            "--server.headless", "false"
        ]
        
        try:
            # Start Streamlit
            subprocess.run(cmd, check=True)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start Streamlit: {e}")
            return False
        except KeyboardInterrupt:
            print("\n🛑 Application stopped by user")
            return True
    
    def cleanup(self):
        """Clean up resources."""
        if self.search_engine:
            self.search_engine.cleanup()
    
    def run_demo(self, port: Optional[int] = None, host: Optional[str] = None) -> bool:
        """
        Run the complete demo startup process.
        
        Args:
            port: Optional port override
            host: Optional host override
            
        Returns:
            bool: True if demo started successfully, False otherwise
        """
        print("🏗️  AI Architectural Search - Demo Launcher")
        print("=" * 50)
        
        try:
            # Validate system requirements
            if not self.validate_system_requirements():
                print("\n❌ System requirements not met. Please fix the issues above.")
                return False
            
            # Validate search system
            if not self.validate_search_system():
                print("\n❌ Search system validation failed. Please check the configuration.")
                return False
            
            print("\n✅ All validations passed! Starting demo...")
            
            # Use config values or defaults
            demo_port = port or (self.config.web_port if self.config else 8501)
            demo_host = host or (self.config.web_host if self.config else "localhost")
            
            # Start the application
            success = self.start_streamlit_app(demo_port, demo_host)
            
            if success:
                print("\n🎉 Demo completed successfully!")
            else:
                print("\n❌ Demo startup failed!")
            
            return success
            
        except Exception as e:
            print(f"\n❌ Demo launcher failed: {e}")
            return False
        
        finally:
            self.cleanup()


def print_demo_instructions():
    """Print demo usage instructions."""
    print("\n📖 Demo Instructions:")
    print("-" * 20)
    print("1. The web interface will open in your browser")
    print("2. Enter natural language queries like:")
    print("   🔥 HIGH PRIORITY (Must work perfectly):")
    print("      • 'red brick buildings'")
    print("      • 'stone facades'") 
    print("      • 'glass and steel structures'")
    print("      • 'buildings with large windows'")
    print("   📋 SUPPORTING QUERIES:")
    print("      • 'modern office buildings'")
    print("      • 'residential houses'")
    print("      • 'institutional buildings'")
    print("3. View results with confidence scores and descriptions")
    print("4. Try different queries to explore the dataset")
    print("5. Use Ctrl+C in this terminal to stop the demo")
    print("\n💡 Demo Tips:")
    print("   • Start with high-priority queries for best results")
    print("   • Each query should return results in under 5 seconds")
    print("   • Look for diverse architectural styles in results")
    print("   • Check confidence scores to gauge result quality")


def main():
    """Main demo launcher function."""
    # Configure logging
    logging.basicConfig(level=logging.WARNING)  # Reduce log noise for demo
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="AI Architectural Search Demo Launcher")
    parser.add_argument("--port", type=int, default=8501, help="Port to run the demo on")
    parser.add_argument("--host", type=str, default="localhost", help="Host to bind to")
    parser.add_argument("--validate-only", action="store_true", help="Only validate system, don't start demo")
    parser.add_argument("--prepare", action="store_true", help="Run full demo preparation with query testing")
    
    args = parser.parse_args()
    
    # Create launcher
    launcher = DemoLauncher()
    
    try:
        if args.prepare:
            # Run comprehensive demo preparation
            print("🎪 For comprehensive demo preparation with query testing:")
            print("   python prepare_demo.py")
            print("\n🔍 Running basic system validation...")
            
            requirements_ok = launcher.validate_system_requirements()
            search_ok = launcher.validate_search_system() if requirements_ok else False
            
            if requirements_ok and search_ok:
                print("\n✅ Basic validation passed!")
                print("💡 Run 'python prepare_demo.py' for full demo readiness testing.")
            else:
                print("\n❌ Basic validation failed!")
            sys.exit(0 if (requirements_ok and search_ok) else 1)
            
        elif args.validate_only:
            # Only run validation
            print("🏗️  AI Architectural Search - System Validation")
            print("=" * 50)
            
            requirements_ok = launcher.validate_system_requirements()
            search_ok = launcher.validate_search_system() if requirements_ok else False
            
            if requirements_ok and search_ok:
                print("\n✅ System validation passed! Ready for demo.")
                print("💡 For comprehensive demo preparation: python prepare_demo.py")
                sys.exit(0)
            else:
                print("\n❌ System validation failed!")
                sys.exit(1)
        else:
            # Run full demo
            print_demo_instructions()
            success = launcher.run_demo(args.port, args.host)
            sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print("\n🛑 Demo launcher interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        launcher.cleanup()


if __name__ == "__main__":
    main()