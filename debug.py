"""
Debug script to help troubleshoot issues with the Financial Data Harmonizer
"""
import os
import sys
import traceback
from pathlib import Path

def check_directory_structure():
    """Check that all necessary directories and files exist."""
    print("=== Checking Directory Structure ===")
    
    root_dir = Path(__file__).parent
    print(f"Root directory: {root_dir}")
    
    # Check main module files
    required_files = [
        "__init__.py",
        "harmonizer_app.py",
        "cli.py",
        "requirements.txt"
    ]
    
    for file in required_files:
        file_path = root_dir / file
        exists = file_path.exists()
        print(f"  {'✓' if exists else '✗'} {file}")
        
    # Check directories
    required_dirs = ["config", "core", "transformers", "connectors"]
    for dir_name in required_dirs:
        dir_path = root_dir / dir_name
        exists = dir_path.exists()
        print(f"  {'✓' if exists else '✗'} {dir_name}/")
        
        if exists:
            # Check __init__.py in each directory
            init_file = dir_path / "__init__.py"
            init_exists = init_file.exists()
            print(f"    {'✓' if init_exists else '✗'} {dir_name}/__init__.py")
            
    # Check provider configs
    provider_dir = root_dir / "config" / "providers"
    if provider_dir.exists():
        print(f"  ✓ config/providers/")
        example_json = provider_dir / "example.json"
        exists = example_json.exists()
        print(f"    {'✓' if exists else '✗'} config/providers/example.json")
    else:
        print(f"  ✗ config/providers/ (directory missing)")
        
    # Check test directories
    test_files_dir = root_dir / "test_files"
    test_files_exists = test_files_dir.exists()
    print(f"  {'✓' if test_files_exists else '✗'} test_files/")
    
    test_files2_dir = root_dir / "test_files2"
    test_files2_exists = test_files2_dir.exists()
    print(f"  {'✓' if test_files2_exists else '✗'} test_files2/")
    
    # Create missing directories
    if not test_files_dir.exists():
        test_files_dir.mkdir()
        print("  ✓ Created test_files/ directory")
        
    if not test_files2_dir.exists():
        test_files2_dir.mkdir()
        print("  ✓ Created test_files2/ directory")
        
    if not provider_dir.exists():
        provider_dir.mkdir(parents=True)
        print("  ✓ Created config/providers/ directory")

def check_dependencies():
    """Check required Python packages."""
    print("\n=== Checking Dependencies ===")
    required_packages = [
        "pandas", 
        "openpyxl", 
        "pyyaml",
        "python-dateutil",
        "typer",
        "rich"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - not installed")
            print(f"    Please install with: pip install {package}")

def create_test_file():
    """Create a sample test file."""
    print("\n=== Creating Sample Test File ===")
    
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
        
        print(f"  ✓ Created sample file: {file_path}")
        
    except Exception as e:
        print(f"  ✗ Failed to create test file: {str(e)}")
        traceback.print_exc()

def test_import():
    """Test importing main modules."""
    print("\n=== Testing Module Imports ===")
    
    modules = [
        "config.providers",
        "core.file_processor",
        "transformers.transform_pipeline",
        "harmonizer_app"
    ]
    
    # Add the parent directory to path if needed
    if str(Path(__file__).parent) not in sys.path:
        sys.path.append(str(Path(__file__).parent))
    
    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except Exception as e:
            print(f"  ✗ {module} - import error")
            print(f"    Error: {str(e)}")
            traceback.print_exc()

def test_run():
    """Test running the harmonizer manually."""
    print("\n=== Testing Manual Run ===")
    
    # Add the parent directory to path if needed
    if str(Path(__file__).parent) not in sys.path:
        sys.path.append(str(Path(__file__).parent))
    
    try:
        from harmonizer_app import FinancialHarmonizer
        
        # Create test file if needed
        test_file = Path(__file__).parent / "test_files" / "sample_invoice.xlsx"
        if not test_file.exists():
            create_test_file()
        
        # Initialize harmonizer
        harmonizer = FinancialHarmonizer()
        
        # Process file
        print("  Processing file...")
        result = harmonizer.process_file(test_file, "ExampleVendor")
        
        if result["success"]:
            print(f"  ✓ Successfully processed {result['row_count']} rows")
            
            # Export results
            output_path = Path(__file__).parent / "test_files2" / "debug_output.csv"
            export_result = harmonizer.export_results(str(output_path), "csv")
            
            if export_result["success"]:
                print(f"  ✓ Results exported to: {output_path}")
                print(f"  ✓ Log exported to: {output_path}.log.json")
            else:
                print(f"  ✗ Export failed: {export_result.get('error')}")
        else:
            print(f"  ✗ Processing failed: {result.get('error')}")
    
    except Exception as e:
        print(f"  ✗ Test run failed: {str(e)}")
        traceback.print_exc()

def check_example_provider():
    """Check the example provider configuration."""
    print("\n=== Checking Example Provider Configuration ===")
    
    provider_path = Path(__file__).parent / "config" / "providers" / "example.json"
    
    if not provider_path.exists():
        print(f"  ✗ Missing provider configuration: {provider_path}")
        print("  Creating example provider configuration...")
        
        # Create directory if needed
        provider_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create example provider
        example_config = {
            "ProviderName": "ExampleVendor",
            "Flags": ["StandardFormat"],
            "Synonyms": [
                {
                    "LogicalField": "date",
                    "AlternateNames": ["Date", "Transaction Date", "Invoice Date", "Doc Date"]
                },
                {
                    "LogicalField": "amount",
                    "AlternateNames": ["Amount", "Total", "Invoice Amount", "Value"]
                },
                {
                    "LogicalField": "description",
                    "AlternateNames": ["Description", "Details", "Line Item", "Particulars"]
                },
                {
                    "LogicalField": "reference",
                    "AlternateNames": ["Reference", "Ref", "Invoice Number", "Invoice #"]
                }
            ],
            "FilterTable": ["[amount] <> 0"],
            "Calculations": [
                {
                    "NewField": "gst_amt",
                    "Expression": "([amount] * 0.15)"
                },
                {
                    "NewField": "excl_gst",
                    "Expression": "([amount] - [gst_amt])"
                }
            ],
            "HardcodedFields": [
                {
                    "FieldName": "provider",
                    "Value": "ExampleVendor"
                }
            ]
        }
        
        try:
            import json
            with open(provider_path, 'w') as f:
                json.dump(example_config, f, indent=2)
            print(f"  ✓ Created example provider configuration: {provider_path}")
        except Exception as e:
            print(f"  ✗ Failed to create example provider: {str(e)}")
    else:
        print(f"  ✓ Example provider configuration exists: {provider_path}")
        
        try:
            import json
            with open(provider_path, 'r') as f:
                config = json.load(f)
            if "ProviderName" in config and config["ProviderName"] == "ExampleVendor":
                print("  ✓ ExampleVendor configuration is valid")
            else:
                print("  ✗ Invalid provider configuration - missing ProviderName")
        except Exception as e:
            print(f"  ✗ Error reading provider configuration: {str(e)}")

def main():
    """Run all checks."""
    print("Financial Data Harmonizer - Troubleshooting\n")
    
    check_directory_structure()
    check_dependencies()
    check_example_provider()
    create_test_file()
    test_import()
    test_run()
    
    print("\n=== Next Steps ===")
    print("1. If all checks passed, try running this command again:")
    print("   python -m financial_harmonizer.cli process-file \"test_files/sample_invoice.xlsx\" ExampleVendor --output \"test_files2/output.csv\"")
    print("\n2. If checks failed, fix the issues and run this debug script again")

if __name__ == "__main__":
    main()
