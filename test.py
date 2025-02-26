"""
Simple script to test the Financial Data Harmonizer
"""
import os
import sys
import pandas as pd
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from harmonizer_app import FinancialHarmonizer

def create_test_file():
    """Create a sample invoice file for testing."""
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)
    
    # Create simple sample data
    sample_data = {
        'Date': ['2023-01-15', '2023-01-16', '2023-01-17'],
        'Invoice Number': ['INV001', 'INV002', 'INV003'],
        'Description': ['Office supplies', 'Software subscription', 'Consulting services'],
        'Amount': [125.50, 299.99, 750.00]
    }
    
    # Convert to DataFrame
    df = pd.DataFrame(sample_data)
    
    # Save as Excel
    file_path = test_dir / "sample_invoice.xlsx"
    df.to_excel(file_path, index=False)
    
    print(f"Created sample test file: {file_path}")
    return file_path

def create_mapping_file():
    """Create a sample mapping file for testing."""
    import json
    
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)
    
    mapping = {
        "invoice": "ExampleVendor",
        "statement": "ExampleVendor" 
    }
    
    file_path = test_dir / "mapping.json"
    with open(file_path, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"Created sample mapping file: {file_path}")
    return file_path

def test_single_file_processing():
    """Test processing a single file."""
    file_path = create_test_file()
    
    print("\n=== Testing Single File Processing ===")
    
    # Initialize the harmonizer
    harmonizer = FinancialHarmonizer()
    
    # Process the file
    result = harmonizer.process_file(file_path, "ExampleVendor")
    
    # Check results
    if result['success']:
        print(f"✓ Successfully processed {result['row_count']} rows")
        
        # Export the data
        output_path = Path("test_files") / "output.csv"
        export_result = harmonizer.export_results(str(output_path), "csv")
        
        if export_result['success']:
            print(f"✓ Results exported to {output_path}")
        else:
            print(f"✗ Export failed: {export_result.get('error')}")
    else:
        print(f"✗ Processing failed: {result.get('error')}")

def test_directory_processing():
    """Test processing a directory of files."""
    # Ensure we have a test file
    create_test_file()
    mapping_file = create_mapping_file()
    
    print("\n=== Testing Directory Processing ===")
    
    # Initialize the harmonizer
    harmonizer = FinancialHarmonizer()
    
    # Process the directory
    result = harmonizer.process_directory("test_files", {
        "sample_invoice": "ExampleVendor"
    })
    
    # Check results
    if result['success']:
        print(f"✓ Successfully processed {result['processed']} files")
        print(f"  Skipped: {result['skipped']} files")
        print(f"  Errors: {result['errors']} files")
        
        if harmonizer.master_data is not None and not harmonizer.master_data.empty:
            # Export the data
            output_path = Path("test_files") / "directory_output.csv"
            export_result = harmonizer.export_results(str(output_path), "csv")
            
            if export_result['success']:
                print(f"✓ Results exported to {output_path}")
            else:
                print(f"✗ Export failed: {export_result.get('error')}")
        else:
            print("✗ No data was processed")
    else:
        print(f"✗ Directory processing failed: {result.get('error')}")

def run_all_tests():
    """Run all tests."""
    test_single_file_processing()
    test_directory_processing()
    print("\n✓ All tests completed!")

if __name__ == "__main__":
    run_all_tests()
    os.system('python -m financial_harmonizer.cli process-file "test_files/sample_invoice.xlsx" ExampleVendor --output "test_files2/output.csv"')
