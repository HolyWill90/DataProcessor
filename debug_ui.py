"""
Debug UI for Financial Data Harmonizer
This simple file helps diagnose Streamlit issues
"""
import os
import sys
import traceback

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Try to import streamlit
try:
    import streamlit as st
    
    # Set up simple page config
    st.set_page_config(
        page_title="Financial Harmonizer Debug",
        page_icon="🛠️",
        layout="wide"
    )
    
    st.title("Financial Harmonizer Debug Mode")
    
    # Display system info
    st.write("### System Information")
    st.write(f"Python version: {sys.version}")
    st.write(f"Streamlit version: {st.__version__}")
    st.write(f"Current directory: {current_dir}")
    
    # Check UI directory
    ui_dir = os.path.join(current_dir, "ui")
    st.write(f"UI directory: {ui_dir}")
    
    if os.path.exists(ui_dir):
        st.success(f"✅ UI directory exists")
        
        # List files in UI directory
        files = os.listdir(ui_dir)
        st.write("Files in UI directory:")
        for file in files:
            st.write(f"- {file}")
            
        # Check for required modules
        required_modules = ["home.py", "provider_manager.py", "file_processor.py", "settings.py"]
        missing = [mod for mod in required_modules if mod not in files]
        
        if missing:
            st.error(f"❌ Missing required modules: {', '.join(missing)}")
        else:
            st.success("✅ All required UI modules found")
            
        # Try to import each module
        for module_name in required_modules:
            if module_name in files:
                try:
                    module_path = f"ui.{module_name[:-3]}"
                    st.write(f"Trying to import {module_path}...")
                    
                    # Dynamic import attempt
                    __import__(module_path)
                    st.success(f"✅ Successfully imported {module_path}")
                except Exception as e:
                    st.error(f"❌ Failed to import {module_path}: {str(e)}")
                    st.code(traceback.format_exc())
    else:
        st.error(f"❌ UI directory not found at {ui_dir}")
        
    # Check if ui/__init__.py exists
    init_path = os.path.join(ui_dir, "__init__.py")
    if os.path.exists(init_path):
        st.success("✅ ui/__init__.py exists")
    else:
        st.error("❌ ui/__init__.py missing")
        
        # Create the file if missing
        if st.button("Create ui/__init__.py"):
            try:
                os.makedirs(ui_dir, exist_ok=True)
                with open(init_path, "w") as f:
                    f.write('"""UI components for Financial Data Harmonizer"""\n')
                st.success("✅ Created ui/__init__.py")
            except Exception as e:
                st.error(f"❌ Failed to create file: {str(e)}")
    
except Exception as e:
    print(f"Critical error in debug UI: {e}")
    traceback.print_exc()
    
    # Try to display in console if streamlit fails
    print("\n==== FINANCIAL HARMONIZER DEBUG ====")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {current_dir}")
    
    ui_dir = os.path.join(current_dir, "ui")
    print(f"UI directory: {ui_dir}")
    
    if os.path.exists(ui_dir):
        print("UI directory exists")
        print("Files in UI directory:")
        for file in os.listdir(ui_dir):
            print(f"- {file}")
    else:
        print("UI directory not found")
