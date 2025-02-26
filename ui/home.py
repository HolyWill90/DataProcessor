"""
Home screen for Financial Data Harmonizer
"""
import streamlit as st

def show_home():
    """Display the home screen."""
    st.title("Financial Data Harmonizer")
    
    st.write("### Welcome to the Financial Data Harmonizer")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("""
        The Financial Data Harmonizer is a powerful tool for standardizing and processing
        financial data from multiple sources. It helps you:
        
        - **Extract** data from various file formats (Excel, CSV)
        - **Transform** data using customizable provider rules
        - **Load** data into a standardized format for analysis
        
        Get started by selecting a section from the sidebar navigation.
        """)
        
        st.divider()
        
        st.write("### Quick Start")
        
        quick_start = st.expander("How to Process Files", expanded=True)
        with quick_start:
            st.write("""
            1. Go to **Process Files** in the sidebar
            2. Upload or select files to process
            3. Choose the appropriate provider for each file
            4. View and export the harmonized data
            """)
            
            if st.button("Go to Process Files"):
                st.session_state.page = "processfiles"
                st.rerun()
        
        provider_start = st.expander("Managing Providers", expanded=False)
        with provider_start:
            st.write("""
            1. Go to **Provider Manager** in the sidebar
            2. Create a new provider or edit an existing one
            3. Configure column mappings, filters, and calculations
            4. Save your provider configuration
            """)
            
            if st.button("Go to Provider Manager"):
                st.session_state.page = "providermanager"
                st.rerun()
        
    with col2:
        # Stats/info panel
        st.write("### System Info")
        info_container = st.container(border=True)
        
        try:
            # Try to import main modules
            import sys
            with info_container:
                st.write(f"Python: {sys.version.split()[0]}")
                st.write(f"Streamlit: {st.__version__}")
                
                try:
                    from config.providers import ProviderConfig
                    provider_config = ProviderConfig()
                    provider_count = len(provider_config.providers_cache)
                    st.metric("Providers Available", provider_count)
                    st.write("✅ System ready")
                except Exception:
                    st.write("⚠️ Provider config not available")
                
        except Exception as e:
            with info_container:
                st.error(f"System initialization error: {str(e)}")
                st.write("⚠️ Some features may be unavailable")
