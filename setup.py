"""
Setup script for AI Architectural Search System
"""
import subprocess
import sys
import os


def create_virtual_environment():
    """Create a Python virtual environment"""
    print("Creating virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✓ Virtual environment created successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create virtual environment: {e}")
        return False
    return True


def install_dependencies():
    """Install required packages from requirements.txt"""
    print("Installing dependencies...")
    
    # Determine the correct pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = os.path.join("venv", "Scripts", "pip")
    else:  # Unix/Linux/macOS
        pip_path = os.path.join("venv", "bin", "pip")
    
    try:
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False
    return True


def main():
    """Main setup function"""
    print("Setting up AI Architectural Search System...")
    
    if not create_virtual_environment():
        sys.exit(1)
    
    if not install_dependencies():
        sys.exit(1)
    
    print("\n✓ Setup completed successfully!")
    print("\nTo activate the virtual environment:")
    if os.name == 'nt':  # Windows
        print("  venv\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("  source venv/bin/activate")
    
    print("\nTo run the application:")
    print("  streamlit run src/web/app.py")


if __name__ == "__main__":
    main()