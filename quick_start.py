"""
Quick start script for the Financial Data Harmonizer with minimal dependencies.
This script will install only the essential dependencies and run a basic test.
"""
import os
import sys
import subprocess
from pathlib import Path

def install_core_requirements():
    """Install only the core required packages."""
    print("Installing core required packages...")
    
    # List of core required packages (no optional dependencies)
    core_packages = [
        "pandas>=1.5.0",
        "openpyxl>=3.1.0",
        "pyyaml>=6.0",
        "python-dateutil>=2.8.2",
    ]
    
    # Install core packages
    for package in core_packages:
        print(f"Installing {package.split('>=')[0]}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ Successfully installed {package}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package}")
    
    print("\nCore packages installed successfully!")

def create_test_file():
    """Create a sample test file."""
    try:
        import pandas as pd
        
        test_dir = Path(__file__).parent / "test_files"
        test_dir.mkdir(exist_ok=True)
        
        # Create sample data
        data = {
            "Date": ["2023-01-15", "2023-01-16", "2023-01-17"],
            "Invoice Number": ["INV001", "INV002", "INV003"],
            "Description": ["Office supplies", "Software subscription", "Consulting services"],
            "Amount": [125.50, 299.99, 750.00]
        }
        
        df = pd.DataFrame(data)
        file_path = test_dir / "sample_invoice.xlsx"
        df.to_excel(file_path, index=False)
        
        print(f"Created sample file: {file_path}")
        return file_path
    except Exception as e:
        print(f"Failed to create test file: {str(e)}")
        return None

def run_test():
    """Run a minimal test using the API directly."""
    print("\nRunning minimal test...")
    
    # Add the parent directory to the path if needed
    if str(Path(__file__).parent) not in sys.path:
        sys.path.append(str(Path(__file__).parent))
    
    try:
        from harmonizer_app import FinancialHarmonizer
        
        # Create test file
        test_file = create_test_file()
        if not test_file:
            return False
        
        # Make sure output directory exists
        output_dir = Path(__file__).parent / "test_files2"
        output_dir.mkdir(exist_ok=True)
        
        # Initialize harmonizer
        print("Initializing Financial Harmonizer...")
        harmonizer = FinancialHarmonizer()
        
        # Process file
        print("Processing file...")
        result = harmonizer.process_file(test_file, "ExampleVendor")
        
        if result["success"]:
            print(f"✓ Successfully processed {result['row_count']} rows")
            
            # Export results
            output_path = output_dir / "output.csv"
            export_result = harmonizer.export_results(str(output_path), "csv")
            
            if export_result["success"]:
                print(f"✓ Results exported to: {output_path}")
                print(f"✓ Log exported to: {output_path}.log.json")
                return True
            else:
                print(f"✗ Export failed: {export_result.get('error')}")
                return False
        else:
            print(f"✗ Processing failed: {result.get('error')}")
            return False
    
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("==== Financial Data Harmonizer Quick Start ====\n")
    
    # Install core requirements
    install_core_requirements()
    
    # Run test
    success = run_test()
    
    if success:
        print("\n✓ Quick start test completed successfully!")
        print("\nTo run with CLI features, install additional packages:")
        print("  pip install typer rich")
        print("\nFor SharePoint integration:")
        print("  pip install shareplum")
    else:
        print("\n✗ Quick start test failed")
        print("Please check the error messages above")

if __name__ == "__main__":
    main()
