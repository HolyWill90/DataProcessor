"""
Setup script for the Financial Data Harmonizer.
This will install all required dependencies and create necessary directories.
"""
import os
import sys
import subprocess
from pathlib import Path

def install_requirements():
    """Install required packages."""
    print("Installing required packages...")
    
    # Check if pip is available
    try:
        import pip
    except ImportError:
        print("ERROR: pip not found. Please install pip first.")
        sys.exit(1)
    
    # List of required packages
    required_packages = [
        "pandas>=1.5.0",
        "openpyxl>=3.1.0",
        "pyyaml>=6.0",
        "python-dateutil>=2.8.2",
        "typer>=0.9.0",
        "rich>=13.0.0",
        "loguru>=0.7.0"
    ]
    
    # Optional packages
    optional_packages = [
        "shareplum>=0.5.1",  # For SharePoint integration
        "fastapi>=0.95.0",   # For API capabilities
        "uvicorn>=0.22.0"    # ASGI server for FastAPI
    ]
    
    # Install required packages
    for package in required_packages:
        print(f"Installing {package.split('>=')[0]}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ Successfully installed {package}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package}")
            print("Please install it manually with:")
            print(f"  pip install {package}")
    
    # Ask about optional packages
    print("\nWould you like to install optional packages?")
    print("1. SharePoint integration")
    print("2. API capabilities")
    print("3. All optional packages")
    print("4. Skip optional packages")
    
    choice = input("Enter your choice (1-4): ")
    
    if choice == "1":
        packages_to_install = [optional_packages[0]]
    elif choice == "2":
        packages_to_install = optional_packages[1:3]
    elif choice == "3":
        packages_to_install = optional_packages
    else:
        packages_to_install = []
        
    for package in packages_to_install:
        print(f"Installing {package.split('>=')[0]}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ Successfully installed {package}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package}")
    
    print("\nAll required packages installed successfully!")

def create_directories():
    """Create necessary directories."""
    print("\nCreating necessary directories...")
    
    base_dir = Path(__file__).parent
    
    # Directories to create
    directories = [
        "config/providers",
        "core",
        "transformers",
        "connectors",
        "test_files",
        "test_files2"
    ]
    
    for directory in directories:
        dir_path = base_dir / directory
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created {directory}")
        else:
            print(f"✓ {directory} already exists")
    
    print("All directories created successfully!")

def main():
    print("==== Financial Data Harmonizer Setup ====\n")
    
    # Install requirements
    install_requirements()
    
    # Create directories
    create_directories()
    
    print("\n==== Setup Complete ====")
    print("\nTo test the application, run:")
    print("  python financial_harmonizer/test.py")
    print("\nOr process a file directly:")
    print("  python -m financial_harmonizer.cli process-file \"financial_harmonizer/test_files/sample_invoice.xlsx\" ExampleVendor --output \"financial_harmonizer/test_files2/output.csv\"")

if __name__ == "__main__":
    main()
