# Testing the Financial Data Harmonizer

This guide will help you run and test the Financial Data Harmonizer with sample data.

## Setup

1. **Environment Setup**:
   ```bash
   # Create a virtual environment
   python -m venv venv
   
   # Activate the virtual environment
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Directory Structure**:
   Make sure your directory structure matches this:
   ```
   financial_harmonizer/
   ├── __init__.py
   ├── cli.py
   ├── harmonizer_app.py
   ├── requirements.txt
   ├── config/
   │   ├── __init__.py
   │   ├── providers.py
   │   └── providers/
   │       └── example.json
   ├── connectors/
   │   ├── __init__.py
   │   └── sharepoint_connector.py
   ├── core/
   │   ├── __init__.py
   │   └── file_processor.py
   ├── transformers/
   │   ├── __init__.py
   │   └── transform_pipeline.py
   └── test_files/  # Create this directory for test files
   ```

## Basic Testing

### 1. Create a test file

Create a sample Excel file in the `test_files` directory. For example, create `test_files/sample_invoice.xlsx` with columns like Date, Description, Amount, Reference.

### 2. Process a single file

