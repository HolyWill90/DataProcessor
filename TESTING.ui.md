# Financial Harmonizer UI Testing Guide

This guide helps you test the new UI organization to ensure everything is working correctly.

## Testing the UI Structure

1. **Verify File Structure**

   Run the cleanup verification script:
   ```
   python financial_harmonizer/cleanup_ui.py
   ```
   
   This will check that all the necessary files are in place and identify redundant files.

2. **Test the Launcher**

   Run the main launcher:
   ```
   python financial_harmonizer/launcher.py
   ```
   
   The launcher should:
   - Check for running instances
   - Attempt to launch the Streamlit UI if available
   - Fall back to Tkinter UI if Streamlit is unavailable

3. **Test Direct UI Launch**

   Test each UI independently:
   
   Streamlit UI:
   ```
   python financial_harmonizer/streamlit_app.py
   ```
   
   Tkinter UI:
   ```
   python financial_harmonizer/tkinter_app.py
   ```

## UI Features to Test

### Streamlit UI

1. **Navigation**
   - Click through all sidebar navigation options (Home, Process Files, Provider Manager, Settings)
   - Verify each page loads correctly

2. **Provider Management**
   - View existing providers
   - Create a new test provider
   - Edit an existing provider

3. **File Processing**
   - Upload a test file (sample files are in test_files directory)
   - Process the file with a selected provider

4. **Settings**
   - View and modify application settings
   - Run diagnostics

### Tkinter UI

1. **Navigation**
   - Click through all navigation buttons
   - Verify each screen loads correctly

2. **Provider Management**
   - View available providers

3. **File Processing**
   - Add test files
   - Select a provider
   - Attempt to process files

## Cleanup Process

After testing, you can clean up redundant files:

1. **Identify Redundant Files**:
   ```
   python financial_harmonizer/cleanup_ui.py
   ```

2. **Delete Redundant Files**:
   ```
   python financial_harmonizer/delete_redundant_files.py
   ```
   
   Choose option 1 to delete all redundant files, or option 2 to select specific files.

## Troubleshooting

### If Streamlit UI Fails:

1. Check Streamlit installation:
   ```
   pip install streamlit==1.22.0
   ```

2. Verify the UI modules:
   ```
   python -c "import streamlit; print('Streamlit OK')"
   ```

3. Try the Tkinter UI as a fallback:
   ```
   python financial_harmonizer/tkinter_app.py
   ```

### If Tkinter UI Fails:

1. Check Tkinter installation (should be included with Python):
   ```
   python -c "import tkinter; print('Tkinter OK')"
   ```

2. Verify proper imports in ui_tkinter/app.py

### General Issues:

If you encounter any issues, check:
1. Python version (3.6+ recommended)
2. All dependencies are installed
3. File paths are correct
4. No syntax errors in the code