"""
Streamlit UI entry point for Financial Data Harmonizer
"""
import os
import sys
import streamlit as st
from pathlib import Path

def main():
    """Main entry point for Streamlit UI."""
    # Add the project root to the path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Set up page config
    st.set_page_config(
        page_title="Financial Data Harmonizer",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state for navigation
    if 'page' not in st.session_state:
        st.session_state.page = "home"
    
    # Sidebar navigation
    st.sidebar.title("Financial Data Harmonizer")
    
    # Navigation buttons
    nav_options = ["Home", "Process Files", "Provider Manager", "Settings"]
    default_index = 0
    
    if st.session_state.page in ["home", "processfiles", "providermanager", "settings"]:
        page_map = {"home": 0, "processfiles": 1, "providermanager": 2, "settings": 3}
        default_index = page_map.get(st.session_state.page, 0)
    
    page = st.sidebar.radio("Navigation", nav_options, index=default_index)
    
    # Set the current page in session state
    st.session_state.page = page.lower().replace(" ", "")
    
    # Version info
    st.sidebar.divider()
    st.sidebar.caption("Version 1.0.0")
    
    # Try to display the selected page
    try:
        if st.session_state.page == "home":
            from ui.home import show_home
            show_home()
        elif st.session_state.page == "processfiles":
            from ui.file_processor import show_file_processor
            show_file_processor()
        elif st.session_state.page == "providermanager":
            from ui.provider_manager import show_provider_manager
            show_provider_manager()
        elif st.session_state.page == "settings":
            from ui.settings import show_settings
            show_settings()
        else:
            st.warning(f"Unknown page: {st.session_state.page}")
    except ImportError as e:
        st.error(f"Error: Could not load page module: {e}")
        st.info("Please make sure all UI components are properly installed.")
        st.code("1. ui/__init__.py exists\n2. ui directory contains all required modules\n3. Python path includes the project directory")
    except Exception as e:
        st.error(f"Error loading page: {e}")
        st.exception(e)

if __name__ == "__main__":
    main()