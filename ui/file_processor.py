"""
File processor module for Financial Data Harmonizer
"""
import streamlit as st
import pandas as pd
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import traceback

# Import utility functions
try:
    sys.path.append(str(Path(__file__).parent.parent))
    from utils import load_file_with_encoding_fallback, make_dataframe_arrow_compatible
except ImportError:
    st.error("Could not import utility functions. Some features may not work correctly.")
    # Define fallback functions if import fails
    def load_file_with_encoding_fallback(file_path, file_obj=None):
        if file_obj is not None:
            if hasattr(file_obj, 'name') and (file_obj.name.endswith('.xlsx') or file_obj.name.endswith('.xls')):
                return pd.read_excel(file_obj)
            else:
                return pd.read_csv(file_obj)
        else:
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                return pd.read_excel(file_path)
            else:
                return pd.read_csv(file_path)
    
    def make_dataframe_arrow_compatible(df):
        return df

def load_providers():
    """Load available provider configurations."""
    try:
        # Try to import provider config if available
        sys.path.append(str(Path(__file__).parent.parent))
        from config.providers import ProviderConfig
        provider_config = ProviderConfig()
        providers = list(provider_config.providers_cache.keys())
        return providers, provider_config
    except Exception as e:
        st.warning(f"Could not load provider configurations: {e}")
        return ["ExampleVendor"], None

def process_files(files, provider_name, provider_config=None):
    """Process the uploaded files with the selected provider."""
    if not provider_config:
        # Try to initialize the harmonizer directly
        try:
            sys.path.append(str(Path(__file__).parent.parent))
            from harmonizer_app import FinancialHarmonizer
            harmonizer = FinancialHarmonizer()
        except Exception as e:
            st.error(f"Error initializing harmonizer: {e}")
            st.exception(e)
            return None
    else:
        # Use the provided config
        try:
            from harmonizer_app import FinancialHarmonizer
            harmonizer = FinancialHarmonizer()
        except Exception as e:
            st.error(f"Error initializing harmonizer: {e}")
            st.exception(e)
            return None
    
    results = []
    
    with st.spinner("Processing files..."):
        for file in files:
            try:
                # For uploaded files, we need to save them temporarily
                temp_file_path = Path(f"temp_{file.name}")
                with open(temp_file_path, "wb") as f:
                    f.write(file.getbuffer())
                
                # Process the file
                result = harmonizer.process_file(
                    file_path=str(temp_file_path),
                    provider_name=provider_name
                )
                results.append(result)
                
                # Remove temp file
                if temp_file_path.exists():
                    os.remove(temp_file_path)
                
            except Exception as e:
                st.error(f"Error processing {file.name}: {e}")
                results.append({"success": False, "error": str(e), "file": file.name})
    
    return harmonizer, results

def show_file_processor():
    """Display the file processing UI"""
    st.title("Process Files")
    
    # Load providers
    providers, provider_config = load_providers()
    
    # Provider selection
    st.subheader("Provider Configuration")
    selected_provider = st.selectbox(
        "Select Provider", 
        options=providers,
        help="Select the data provider configuration to use for processing"
    )
    
    # File upload section
    st.subheader("Upload Files")
    uploaded_files = st.file_uploader(
        "Upload Excel or CSV files",
        accept_multiple_files=True,
        type=['xlsx', 'xls', 'csv']
    )
    
    if uploaded_files:
        st.write(f"Uploaded {len(uploaded_files)} file(s):")
        for file in uploaded_files:
            st.write(f"- {file.name} ({file.size} bytes)")
            
        # Display a simple preview of the first file
        if st.button("Preview First File"):
            try:
                first_file = uploaded_files[0]
                df = load_file_with_encoding_fallback(first_file.name, file_obj=first_file)
                
                # Make DataFrame Arrow-compatible for display
                df_display = make_dataframe_arrow_compatible(df)
                    
                st.write("File Preview:")
                st.dataframe(df_display.head(10))
            except Exception as e:
                st.error(f"Error previewing file: {str(e)}")
                with st.expander("See detailed error"):
                    st.code(traceback.format_exc())
        
        # Process files button
        if st.button("Process Files", type="primary"):
            if not selected_provider:
                st.error("Please select a provider configuration")
            else:
                harmonizer, results = process_files(uploaded_files, selected_provider, provider_config)
                
                if harmonizer and results:
                    # Show results summary
                    success_count = sum(1 for r in results if r.get("success", False))
                    error_count = len(results) - success_count
                    
                    st.subheader("Processing Results")
                    st.write(f"Processed {len(results)} files")
                    st.write(f"Success: {success_count}, Errors: {error_count}")
                    
                    # Show any errors
                    if error_count > 0:
                        with st.expander("Show Errors"):
                            for result in results:
                                if not result.get("success", False):
                                    st.error(f"- {result.get('file', 'Unknown file')}: {result.get('error', 'Unknown error')}")
                    
                    # Show processed data
                    if hasattr(harmonizer, 'master_data') and harmonizer.master_data is not None:
                        df = harmonizer.master_data
                        
                        # Make DataFrame Arrow-compatible for display
                        df_display = make_dataframe_arrow_compatible(df)
                        
                        st.subheader("Processed Data")
                        st.write(f"Total rows: {len(df)}, Total columns: {len(df.columns)}")
                        
                        with st.container():
                            st.dataframe(df_display)
                        
                        # Export options
                        st.subheader("Export Options")
                        export_format = st.radio("Export Format", ["CSV", "Excel"])
                        export_filename = st.text_input("Filename", "processed_data")
                        
                        if st.button("Export Data"):
                            try:
                                format_type = export_format.lower()
                                if format_type == "excel":
                                    output_path = f"{export_filename}.xlsx"
                                else:
                                    output_path = f"{export_filename}.csv"
                                
                                export_result = harmonizer.export_results(
                                    output_path=output_path,
                                    format=format_type
                                )
                                
                                if export_result.get("success", False):
                                    # Provide download link
                                    with open(output_path, "rb") as file:
                                        st.download_button(
                                            label=f"Download {export_format} File",
                                            data=file,
                                            file_name=os.path.basename(output_path),
                                            mime="application/octet-stream"
                                        )
                                else:
                                    st.error(f"Error exporting data: {export_result.get('error', 'Unknown error')}")
                            except Exception as e:
                                st.error(f"Error exporting data: {e}")
                                with st.expander("See detailed error"):
                                    st.code(traceback.format_exc())
    else:
        st.info("Please upload one or more Excel/CSV files to process")
        
        # Show sample data option
        if st.button("Use Sample Data"):
            sample_data = {
                "date": ["2023-01-01", "2023-01-15", "2023-01-31"],
                "reference": ["INV-001", "INV-002", "INV-003"],
                "description": ["Office supplies", "Software license", "Consulting"],
                "amount": [120.50, 499.99, 1200.00]
            }
            df = pd.DataFrame(sample_data)
            
            # Make sample data Arrow-compatible for display
            df_display = make_dataframe_arrow_compatible(df)
            
            st.write("Sample Data:")
            st.dataframe(df_display)
            
            # Demo processing
            if st.button("Process Sample Data"):
                st.session_state.sample_processed = True
                
                st.subheader("Sample Processing Results")
                st.write("Processed 1 file")
                st.write("Success: 1, Errors: 0")
                
                # Enhanced sample data with calculated fields
                processed_data = df.copy()
                processed_data["gst_amt"] = processed_data["amount"] * 0.15
                processed_data["excl_gst"] = processed_data["amount"] - processed_data["gst_amt"]
                
                # Make processed data Arrow-compatible for display
                processed_display = make_dataframe_arrow_compatible(processed_data)
                
                st.subheader("Processed Sample Data")
                st.write(f"Total rows: {len(processed_data)}, Total columns: {len(processed_data.columns)}")
                st.dataframe(processed_display)
