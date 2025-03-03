"""
Provider Manager UI - Streamlit Version
"""
import os
import sys
import json
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path

# Initialize ProviderConfig
@st.cache_resource
def load_provider_config():
    try:
        from config.providers import ProviderConfig
        return ProviderConfig()
    except Exception as e:
        st.error(f"Error loading provider configuration: {e}")
        return None

def get_default_provider_config():
    """Get default provider configuration."""
    return {
        "ProviderName": "",
        "Description": "",
        "Flags": ["StandardFormat"],
        "Synonyms": [
            {"LogicalField": "date", "AlternateNames": ["Date", "Transaction Date", "Invoice Date"]},
            {"LogicalField": "reference", "AlternateNames": ["Reference", "Ref", "Invoice Number", "Invoice #"]},
            {"LogicalField": "description", "AlternateNames": ["Description", "Details", "Line Item", "Particulars"]},
            {"LogicalField": "amount", "AlternateNames": ["Amount", "Total", "Invoice Amount", "Value"]}
        ],
        "FilterTable": ["[amount] <> 0"],
        "Calculations": [
            {"NewField": "gst_amt", "Expression": "([amount] * 0.15)"},
            {"NewField": "excl_gst", "Expression": "([amount] - [gst_amt])"}
        ],
        "HardcodedFields": [
            {"FieldName": "provider", "Value": ""}
        ],
        "Examples": []
    }

def load_provider(provider_name):
    """Load an existing provider configuration."""
    provider_config = load_provider_config()
    if not provider_config:
        st.error("Provider configuration manager not available")
        return get_default_provider_config()
    
    try:
        provider_data = provider_config.get_provider_settings(provider_name)
        return provider_data
    except Exception as e:
        st.error(f"Failed to load provider {provider_name}: {e}")
        return get_default_provider_config()

def save_provider(provider_data):
    """Save provider configuration."""
    provider_config = load_provider_config()
    if not provider_config:
        st.error("Provider configuration manager not available")
        return False
    
    try:
        provider_name = provider_data["ProviderName"]
        if not provider_name:
            st.error("Provider name is required")
            return False
            
        # Update "provider" hardcoded field if it exists
        for field in provider_data.get("HardcodedFields", []):
            if field["FieldName"] == "provider" and not field["Value"]:
                field["Value"] = provider_name
        
        provider_config.save_provider(provider_data)
        
        # Update session state providers list if needed
        if "providers" in st.session_state:
            provider_name_upper = provider_name.upper()
            if provider_name_upper not in st.session_state.providers:
                st.session_state.providers.append(provider_name_upper)
            
        return True
    except Exception as e:
        st.error(f"Failed to save provider: {e}")
        return False

def reset_form():
    """Reset the form to default state."""
    st.session_state.edit_mode = False
    st.session_state.selected_provider = None
    
def show_provider_sidebar():
    """Provider selection sidebar component."""
    provider_config = load_provider_config()
    
    # Initialize session state variables
    if "providers" not in st.session_state:
        if provider_config:
            st.session_state.providers = list(provider_config.providers_cache.keys())
        else:
            st.session_state.providers = ["ExampleVendor"]
            
    if "selected_provider" not in st.session_state:
        st.session_state.selected_provider = None
        
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False
        
    if "create_method" not in st.session_state:
        st.session_state.create_method = "manual"  # 'manual' or 'schema_builder'
    
    # Create or edit options
    action = st.sidebar.radio("Action", ["Create New", "Edit Existing"], index=0 if not st.session_state.edit_mode else 1)
    
    if action == "Create New":
        st.session_state.edit_mode = False
        st.session_state.selected_provider = None
        
        # Choose creation method - manual or schema builder
        creation_method = st.sidebar.radio(
            "Creation Method",
            options=["Manual Creation", "Generate from Sample"],
            help="Choose how to create the provider"
        )
        
        if creation_method == "Manual Creation":
            st.session_state.create_method = "manual"
        else:
            st.session_state.create_method = "schema_builder"
            
    else:
        st.session_state.edit_mode = True
        st.session_state.create_method = "manual"  # Always manual in edit mode
        
        # Provider selection dropdown
        if st.session_state.providers:
            selected_index = 0
            if st.session_state.selected_provider in st.session_state.providers:
                selected_index = st.session_state.providers.index(st.session_state.selected_provider)
                
            selected = st.sidebar.selectbox(
                "Select Provider to Edit",
                options=st.session_state.providers,
                index=selected_index
            )
            
            if selected != st.session_state.selected_provider:
                st.session_state.selected_provider = selected
                st.rerun()
        else:
            st.sidebar.warning("No providers found")

    # Import/Export options
    st.sidebar.subheader("Import/Export")
    
    uploaded_file = st.sidebar.file_uploader("Import Provider JSON", type=["json"])
    if uploaded_file:
        try:
            provider_data = json.loads(uploaded_file.getvalue().decode('utf-8'))
            
            # Validate
            if "ProviderName" not in provider_data:
                st.sidebar.error("Invalid provider file: Missing ProviderName")
            else:
                # Save
                if save_provider(provider_data):
                    provider_name = provider_data["ProviderName"]
                    st.sidebar.success(f"Provider {provider_name} imported successfully")
                    st.session_state.selected_provider = provider_name.upper()
                    st.session_state.edit_mode = True
                    st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error importing provider: {str(e)}")
    
    # Export current provider
    if st.session_state.selected_provider and st.sidebar.button("Export Selected Provider"):
        try:
            provider_data = load_provider(st.session_state.selected_provider)
            if provider_data:
                json_str = json.dumps(provider_data, indent=2)
                st.sidebar.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"{provider_data['ProviderName']}_config.json",
                    mime="application/json"
                )
        except Exception as e:
            st.sidebar.error(f"Error exporting provider: {str(e)}")

def basic_information_section(provider_data):
    """Basic information section of the UI."""
    st.subheader("Basic Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        provider_name = st.text_input(
            "Provider Name", 
            value=provider_data.get("ProviderName", ""),
            help="Name of the provider (e.g., 'XeroBank', 'AmazonAWS')"
        )
        
        st.write("Configuration Flags")
        flags = provider_data.get("Flags", ["StandardFormat"])
        
        standard_format = st.checkbox("StandardFormat", 
                                     value="StandardFormat" in flags,
                                     help="Use standard field mapping")
        
        has_header = st.checkbox("HasHeader", 
                                value="HasHeader" in flags,
                                help="Files have header rows")
        
        skip_empty = st.checkbox("SkipEmpty", 
                                value="SkipEmpty" in flags,
                                help="Skip empty rows/cells")
        
        updated_flags = []
        if standard_format:
            updated_flags.append("StandardFormat")
        if has_header:
            updated_flags.append("HasHeader")
        if skip_empty:
            updated_flags.append("SkipEmpty")
            
    with col2:
        description = st.text_area(
            "Description", 
            value=provider_data.get("Description", ""),
            height=100,
            help="Describe the purpose of this provider configuration"
        )
        
        examples_text = st.text_area(
            "File Examples (one per line)", 
            value="\n".join(provider_data.get("Examples", [])),
            height=80,
            help="List example filenames or patterns that this provider handles"
        )
        examples = [line for line in examples_text.split("\n") if line.strip()]
    
    # Update the provider data
    provider_data["ProviderName"] = provider_name
    provider_data["Description"] = description
    provider_data["Flags"] = updated_flags
    provider_data["Examples"] = examples
    
    return provider_data

def column_mappings_section(provider_data):
    """Column mappings section of the UI."""
    st.subheader("Column Mappings")
    st.write("Define how columns in your files map to standard field names")
    
    # Get existing synonyms
    synonyms = provider_data.get("Synonyms", [])
    
    # Create a DataFrame for editing
    synonyms_data = []
    for s in synonyms:
        logical_field = s.get("LogicalField", "")
        alternate_names = s.get("AlternateNames", [])
        synonyms_data.append({
            "Logical Field": logical_field,
            "Alternate Names": ", ".join(alternate_names)
        })
    
    if not synonyms_data:
        # Add default fields if no data exists
        synonyms_data = [
            {"Logical Field": "", "Alternate Names": ""}
        ]
    
    # Convert to DataFrame for the editor
    df = pd.DataFrame(synonyms_data)
    
    # Create the data editor
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True
    )
    
    if st.button("Add Default Mappings"):
        default_mappings = {
            "date": ["Date", "Transaction Date", "Invoice Date", "Due Date"],
            "reference": ["Reference", "Ref", "Invoice Number", "Invoice #"],
            "description": ["Description", "Details", "Line Item", "Particulars"],
            "amount": ["Amount", "Total", "Invoice Amount", "Value"]
        }
        
        new_rows = []
        existing_fields = edited_df["Logical Field"].tolist()
        
        for field, alternatives in default_mappings.items():
            if field not in existing_fields:
                new_rows.append({
                    "Logical Field": field,
                    "Alternate Names": ", ".join(alternatives)
                })
        
        if new_rows:
            edited_df = pd.concat([edited_df, pd.DataFrame(new_rows)], ignore_index=True)
    
    # Extract updated synonym data
    updated_synonyms = []
    for _, row in edited_df.iterrows():
        logical_field = row["Logical Field"].strip()
        alternate_names = [name.strip() for name in row["Alternate Names"].split(",") if name.strip()]
        
        if logical_field and alternate_names:
            updated_synonyms.append({
                "LogicalField": logical_field,
                "AlternateNames": alternate_names
            })
    
    # Update provider data
    provider_data["Synonyms"] = updated_synonyms
    
    return provider_data

def filters_calculations_section(provider_data):
    """Filters and calculations section of the UI."""
    st.subheader("Filters & Calculations")
    
    tab1, tab2 = st.tabs(["Filters", "Calculations"])
    
    with tab1:
        st.write("Define filters to apply to the data")
        st.caption("Examples: [amount] <> 0, [description] IS NOT NULL, [date] > '2023-01-01'")
        
        # Get existing filters
        filters = provider_data.get("FilterTable", ["[amount] <> 0"])
        
        # Create filter editor
        filters_text = st.text_area(
            "Filters (one filter per line)",
            value="\n".join(filters),
            height=200
        )
        
        # Update filters
        updated_filters = [line.strip() for line in filters_text.split("\n") if line.strip()]
        provider_data["FilterTable"] = updated_filters
    
    with tab2:
        st.write("Define calculated fields")
        st.caption("Examples - Field: gst_amt, Expression: ([amount] * 0.15)")
        
        # Get existing calculations
        calculations = provider_data.get("Calculations", [])
        
        # Create calculations DataFrame
        calc_data = []
        for c in calculations:
            calc_data.append({
                "Field Name": c.get("NewField", ""),
                "Expression": c.get("Expression", "")
            })
        
        if not calc_data:
            calc_data = [
                {"Field Name": "gst_amt", "Expression": "([amount] * 0.15)"},
                {"Field Name": "excl_gst", "Expression": "([amount] - [gst_amt])"}
            ]
        
        # Create data editor
        edited_calc_df = st.data_editor(
            pd.DataFrame(calc_data),
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True
        )
        
        # Extract updated calculation data
        updated_calculations = []
        for _, row in edited_calc_df.iterrows():
            field_name = row["Field Name"].strip()
            expression = row["Expression"].strip()
            
            if field_name and expression:
                updated_calculations.append({
                    "NewField": field_name,
                    "Expression": expression
                })
        
        # Update provider data
        provider_data["Calculations"] = updated_calculations
    
    return provider_data

def advanced_settings_section(provider_data):
    """Advanced settings section of the UI."""
    st.subheader("Advanced Settings")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Hardcoded Fields", "Header Extraction", "Unpivot Settings", "JSON View"])
    
    with tab1:
        st.write("Define fields with constant values")
        
        # Get existing hardcoded fields
        hardcoded = provider_data.get("HardcodedFields", [])
        
        # Create hardcoded DataFrame
        hardcoded_data = []
        for h in hardcoded:
            hardcoded_data.append({
                "Field Name": h.get("FieldName", ""),
                "Value": h.get("Value", "")
            })
        
        if not hardcoded_data:
            hardcoded_data = [
                {"Field Name": "provider", "Value": provider_data.get("ProviderName", "")}
            ]
        
        # Create data editor
        edited_hardcoded_df = st.data_editor(
            pd.DataFrame(hardcoded_data),
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True
        )
        
        # Extract updated hardcoded data
        updated_hardcoded = []
        for _, row in edited_hardcoded_df.iterrows():
            field_name = row["Field Name"].strip()
            value = row["Value"].strip()
            
            if field_name:
                updated_hardcoded.append({
                    "FieldName": field_name,
                    "Value": value
                })
        
        # Update provider data
        provider_data["HardcodedFields"] = updated_hardcoded
    
    with tab2:
        st.write("Define rules to extract values from header text")
        st.caption("This feature requires advanced configuration")
        
        # Get existing extraction settings
        header_extraction = provider_data.get("HeaderExtraction", [])
        
        # Show as JSON for now (advanced feature)
        if header_extraction:
            st.json(header_extraction)
        else:
            st.info("No header extraction rules defined. Use the JSON view to add this advanced feature.")
    
    with tab3:
        st.write("Configure unpivot settings to transform wide-format data into long-format")
        st.caption("This transforms columns into rows, which is useful for reorganizing data with many similar columns")
        
        # Get existing unpivot settings
        unpivot_settings = provider_data.get("UnpivotColumns", {})
        key_columns = unpivot_settings.get("KeyColumns", [])
        value_columns = unpivot_settings.get("ValueColumns", [])
        
        # Create form for unpivot settings
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Key Columns (these remain as identifiers)")
            key_columns_text = st.text_area(
                "Key Columns (one per line)",
                value="\n".join(key_columns),
                height=150,
                help="These columns uniquely identify each row and won't be unpivoted"
            )
            
            # Extract key columns
            updated_key_columns = [line.strip() for line in key_columns_text.split("\n") if line.strip()]
            
        with col2:
            st.write("Value Columns (name and value pair)")
            value_columns_text = st.text_area(
                "Value Columns (one per line)",
                value="\n".join(value_columns),
                height=150,
                help="First value will be the attribute name column, second will be the value column"
            )
            
            # Extract value columns
            updated_value_columns = [line.strip() for line in value_columns_text.split("\n") if line.strip()]
        
        # Example and explanation
        with st.expander("Unpivot Example"):
            st.write("""
            **Before unpivot**: Wide format with multiple value columns
            
            | date | customer | product_a | product_b | product_c |
            |------|----------|-----------|-----------|-----------|
            | 2023-01-01 | ABC Corp | 100 | 200 | 300 |
            | 2023-01-02 | XYZ Inc | 150 | 250 | 350 |
            
            **After unpivot** with KeyColumns=["date", "customer"] and ValueColumns=["product", "amount"]:
            
            | date | customer | product | amount |
            |------|----------|---------|--------|
            | 2023-01-01 | ABC Corp | product_a | 100 |
            | 2023-01-01 | ABC Corp | product_b | 200 |
            | 2023-01-01 | ABC Corp | product_c | 300 |
            | 2023-01-02 | XYZ Inc | product_a | 150 |
            | 2023-01-02 | XYZ Inc | product_b | 250 |
            | 2023-01-02 | XYZ Inc | product_c | 350 |
            """)
        
        # Update the provider data with new unpivot settings
        if updated_key_columns or updated_value_columns:
            provider_data["UnpivotColumns"] = {
                "KeyColumns": updated_key_columns,
                "ValueColumns": updated_value_columns
            }
        elif "UnpivotColumns" in provider_data:
            # Remove unpivot settings if empty
            if not key_columns and not value_columns:
                del provider_data["UnpivotColumns"]
    
    with tab4:
        st.write("View and edit the raw JSON configuration")
        
        # Create a copy for JSON editing
        json_data = json.dumps(provider_data, indent=2)
        
        edited_json = st.text_area("JSON Configuration", value=json_data, height=400)
        
        if st.button("Update from JSON"):
            try:
                updated_data = json.loads(edited_json)
                # Validate essential fields
                if "ProviderName" not in updated_data:
                    st.error("JSON must contain 'ProviderName' field")
                else:
                    # Replace provider data with JSON version
                    for key, value in updated_data.items():
                        provider_data[key] = value
                    st.success("Configuration updated from JSON")
            except Exception as e:
                st.error(f"Invalid JSON: {str(e)}")
    
    return provider_data

def generate_schema_from_sample():
    """Generate a provider schema from a sample file."""
    st.subheader("Generate Provider from Sample File")
    st.write("Upload a sample file to automatically generate a provider schema")
    
    # Check if schema_builder module is available
    try:
        from schema_builder.ai_schema_generator import AISchemaGenerator, save_schema
        from core.file_processor import FileProcessor
        from transformers.transform_pipeline import TransformPipeline
        
        # Initialize file processor for schema generation
        if "file_processor" not in st.session_state:
            st.session_state.file_processor = FileProcessor(
                transform_pipeline=TransformPipeline(),
                provider_config=load_provider_config()
            )
        
        # Load settings for Claude API key with full debug
        settings_path = Path(__file__).parent.parent / "config" / "settings.json"
        claude_api_key = os.environ.get("CLAUDE_API_KEY", "")  # Try environment variable first
        use_claude = True
        
        # Debug mode helps diagnose issues with API key loading
        debug_mode = False  # Set to false to hide debugging messages
        
        if debug_mode:
            st.write("Loading API key...")
            if claude_api_key:
                st.success("Found API key in environment variables!")
        
        # Check if the settings file exists
        if settings_path.exists():
            if debug_mode:
                st.success(f"Settings file found at {settings_path}")
            
            try:
                with open(settings_path, "r") as f:
                    settings_content = f.read()
                    
                if settings_content.strip():
                    import json
                    settings = json.loads(settings_content)
                    
                    # Only update API key if not already found in environment
                    if not claude_api_key and settings.get("claude_api_key"):
                        claude_api_key = settings.get("claude_api_key", "")
                    
                    use_claude = settings.get("use_claude_for_schema", True)
                    
                    # Debug feedback
                    if debug_mode:
                        st.write(f"API key in settings: {'Present' if settings.get('claude_api_key') else 'Not found'}")
                        st.write(f"Final API key status: {'Available for use' if claude_api_key else 'Not available'}")
                        if claude_api_key:
                            st.success("API key found!")
                        else:
                            st.warning("API key is empty in settings file.")
                elif debug_mode:
                    st.warning("Settings file is empty.")
            except Exception as e:
                if debug_mode:
                    st.error(f"Error loading settings: {e}")
                # Don't show error to users in non-debug mode
            
        elif debug_mode:
            st.warning(f"Settings file not found at {settings_path}")
            
        # Also check environment variables 
        env_api_key = os.environ.get("CLAUDE_API_KEY", "")
        if not claude_api_key and env_api_key:
            if debug_mode:
                st.success("API key found in environment variables!")
            claude_api_key = env_api_key
                
        # File upload
        sample_file = st.file_uploader(
            "Upload a sample Excel or CSV file",
            type=["xlsx", "xls", "csv"]
        )
        
        if sample_file:
            # Preview uploaded file
            try:
                from ui.file_processor import load_file_with_encoding_fallback, make_dataframe_arrow_compatible
                df = load_file_with_encoding_fallback(sample_file.name, file_obj=sample_file)
                
                st.write(f"Uploaded: {sample_file.name}")
                st.write(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
                
                # File preview
                with st.expander("Preview Data"):
                    df_display = make_dataframe_arrow_compatible(df.head(10))
                    st.dataframe(df_display)
                
                # Schema generation options
                st.divider()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Use AI checkbox - checked by default if API key is available
                    use_ai = st.checkbox(
                        "Use AI for schema generation", 
                        value=use_claude and claude_api_key != "",
                        help="Use Claude AI to generate an optimized schema"
                    )
                
                with col2:
                    # Provider name
                    default_name = os.path.splitext(sample_file.name)[0].replace(" ", "")
                    custom_name = st.text_input(
                        "Provider Name",
                        value=default_name,
                        help="Name for the provider (defaults to filename)"
                    )
                
                # Let the user enter an API key directly if not found in settings
                if use_ai and not claude_api_key:
                    st.warning("Claude API key not found in settings.")
                    
                    # Offer option to enter API key directly
                    direct_api_key = st.text_input(
                        "Enter Claude API Key",
                        type="password",
                        help="Enter your API key directly here, or add it to settings for future use"
                    )
                    
                    # Update the API key if provided
                    if direct_api_key:
                        claude_api_key = direct_api_key
                        st.success("API key entered! Will be used for this session.")
                    else:
                        # Add a button to go to settings
                        if st.button("Go to Settings to Add API Key Permanently"):
                            st.session_state.page = "settings"
                            st.rerun()
                    
                    # Offer option to save to settings
                    if direct_api_key and st.button("Save API Key to Settings"):
                        try:
                            # Load current settings or create new ones
                            settings = {}
                            if settings_path.exists():
                                with open(settings_path, "r") as f:
                                    content = f.read().strip()
                                    if content:
                                        settings = json.loads(content)
                            
                            # Update settings with the new API key
                            settings["claude_api_key"] = direct_api_key
                            settings["use_claude_for_schema"] = True
                            
                            # Make sure the config directory exists
                            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
                            
                            # Write the updated settings
                            with open(settings_path, "w") as f:
                                json.dump(settings, f, indent=2)
                                
                            st.success("API key saved to settings file!")
                        except Exception as e:
                            st.error(f"Error saving API key to settings: {e}")
                    
                    # Still go to settings if they prefer
                    if st.button("Go to Settings Page"):
                        st.session_state.page = "settings"
                        st.rerun()
                        
                    # Set use_ai false only if key is still missing
                    if not claude_api_key:
                        st.info("Proceeding with basic schema generation instead.")
                        use_ai = False
                
                # Check for data anonymization option with preview
                anonymize = st.checkbox(
                    "Anonymize sensitive data", 
                    value=True,
                    help="Replace potentially sensitive information before processing"
                )
                st.caption("Recommended for financial data containing customer names, account numbers, etc.")
                
                # Show preview of anonymization if requested
                if anonymize and len(df) > 0:
                    try:
                        with st.expander("Preview of anonymized data", expanded=False):
                            # Import the anonymizer
                            try:
                                from schema_builder.anonymizer.data_anonymizer import DataAnonymizer
                                anonymizer = DataAnonymizer()
                                
                                # Anonymize a sample of the data (up to 5 rows)
                                sample_df = df.head(min(5, len(df)))
                                anonymized_sample = anonymizer.anonymize_dataframe(sample_df)
                                
                                # Display comparison
                                st.write("### Before anonymization:")
                                st.dataframe(make_dataframe_arrow_compatible(sample_df))
                                
                                st.write("### After anonymization:")
                                st.dataframe(make_dataframe_arrow_compatible(anonymized_sample))
                                
                                st.info("All sensitive information like names, identifiers, and account numbers will be replaced with safe placeholder values before processing.")
                            except ImportError:
                                st.warning("Anonymization preview not available - anonymizer module not found")
                    except Exception as anon_err:
                        st.warning(f"Could not preview anonymization: {anon_err}")
                        # Continue without preview
                
                # Generate button
                if st.button("Generate Provider Schema", type="primary"):
                    with st.spinner("Generating schema..."):
                        try:
                            # Write to temporary file
                            temp_file_path = Path(f"temp_schema_sample_{sample_file.name}")
                            
                            # Save based on file type
                            if sample_file.name.lower().endswith((".xlsx", ".xls")):
                                df.to_excel(temp_file_path, index=False)
                            else:
                                df.to_csv(temp_file_path, index=False)
                            
                            # Process with AI or basic approach
                            try:
                                # Direct use of schema generator based on user selections
                                if use_ai and claude_api_key:
                                    # For AI generation with Claude
                                    st.info("Using Claude AI for schema generation...")
                                    
                                    try:
                                        # First create a proper JSON-serializable version of the data
                                        # to avoid NaT serialization errors
                                        from schema_builder.ai_schema_generator import CustomJSONEncoder
                                        import pandas as pd
                                        import numpy as np
                                        import json
                                        
                                        # Load and preprocess data to handle NaT values
                                        df_clean = pd.read_csv(temp_file_path) if str(temp_file_path).endswith('.csv') else pd.read_excel(temp_file_path)
                                        
                                        # Replace NaT values with None
                                        for col in df_clean.select_dtypes(include=['datetime64']).columns:
                                            df_clean[col] = df_clean[col].astype(object).where(~pd.isna(df_clean[col]), None)
                                        
                                        # Now use the existing schema generator
                                        from schema_builder.ai.schema_generator import AISchemaGenerator as DirectGenerator
                                        import json
                                        
                                        # Create the generator with correct API key
                                        generator = DirectGenerator(api_key=claude_api_key)
                                        
                                        # Skip anonymization if the user unchecked it
                                        schema = generator.generate_schema(
                                            df=df_clean,
                                            provider_name=custom_name,
                                            header_text="", 
                                            skip_anonymization=not anonymize
                                        )
                                        
                                        # Return in expected format
                                        result = {
                                            'success': True,
                                            'schema': schema
                                        }
                                    except AttributeError as attr_err:
                                        # If generate_schema doesn't work, try generate_schema_from_file
                                        if "generate_schema" in str(attr_err):
                                            st.info("Using file-based schema generation...")
                                            from schema_builder.ai.schema_generator import AISchemaGenerator as DirectGenerator
                                            generator = DirectGenerator(api_key=claude_api_key)
                                            schema = generator.generate_schema_from_file(
                                                file_path=str(temp_file_path),
                                                provider_name=custom_name,
                                                skip_anonymization=not anonymize
                                            )
                                            result = {'success': True, 'schema': schema}
                                        else:
                                            raise
                                else:
                                    # For basic generation without AI
                                    st.info("Using basic schema generation (no AI)...")
                                    # Use basic schema generation
                                    result = st.session_state.file_processor.generate_schema_with_ai(
                                        sample_file_path=temp_file_path,
                                        ai_service=None
                                    )
                                    
                            except Exception as schema_error:
                                st.error(f"Schema generation error: {schema_error}")
                                # Fallback to basic schema generation
                                st.info("Falling back to basic schema generation...")
                                result = st.session_state.file_processor.generate_schema_with_ai(
                                    sample_file_path=temp_file_path,
                                    ai_service=None
                                )
                            
                            # Remove temporary file
                            if temp_file_path.exists():
                                os.remove(temp_file_path)
                            
                            if result.get('success', False):
                                schema = result.get('schema', {})
                                
                                # Override provider name if specified
                                if custom_name:
                                    schema["ProviderName"] = custom_name
                                    for field in schema.get("HardcodedFields", []):
                                        if field.get("FieldName") == "provider":
                                            field["Value"] = custom_name
                                
                                # Display generated schema
                                st.success("Schema generated successfully!")
                                
                                # Store the generated schema in session state
                                if "generated_schema" not in st.session_state:
                                    st.session_state.generated_schema = schema
                                else:
                                    st.session_state.generated_schema = schema
                                
                                # Options for working with the schema
                                options_col1, options_col2 = st.columns(2)
                                
                                with options_col1:
                                    if st.button("Review Schema", use_container_width=True):
                                        st.session_state.schema_view_mode = "review"
                                
                                with options_col2:
                                    if st.button("Edit in Provider Editor", type="primary", use_container_width=True):
                                        # Create container for showing the editor directly within this page
                                        st.session_state.schema_view_mode = "editor"
                                        # Store schema for the editor to use
                                        st.session_state.prefilled_provider = schema
                                        st.rerun()  # Refresh to show editor
                                
                                # Only show review if in review mode
                                if "schema_view_mode" not in st.session_state:
                                    st.session_state.schema_view_mode = "review"
                                
                                if st.session_state.schema_view_mode == "editor":
                                    # Show the embedded provider editor
                                    st.subheader("Edit Generated Provider")
                                    
                                    # Use the schema from session state
                                    provider_data = st.session_state.prefilled_provider
                                    
                                    # Create tabs for the provider editor sections
                                    form_tab1, form_tab2, form_tab3, form_tab4 = st.tabs(["Basic Information", "Column Mappings", "Filters & Calculations", "Advanced Settings"])
                                    
                                    with form_tab1:
                                        provider_data = basic_information_section(provider_data)
                                        
                                    with form_tab2:
                                        provider_data = column_mappings_section(provider_data)
                                        
                                    with form_tab3:
                                        provider_data = filters_calculations_section(provider_data)
                                        
                                    with form_tab4:
                                        provider_data = advanced_settings_section(provider_data)
                                    
                                    # Save button for the embedded editor
                                    col1, col2, col3 = st.columns([1, 1, 2])
                                    with col1:
                                        if st.button("Save Provider", type="primary", use_container_width=True):
                                            if not provider_data.get("ProviderName", "").strip():
                                                st.error("Provider name is required")
                                            else:
                                                if save_provider(provider_data):
                                                    prov_name = provider_data.get('ProviderName', '')
                                                    st.success(f"Provider {prov_name} saved successfully!")
                                    
                                    with col2:
                                        if st.button("Back to Schema Review", use_container_width=True):
                                            st.session_state.schema_view_mode = "review"
                                            st.rerun()
                                    
                                elif st.session_state.schema_view_mode == "review":
                                    # Use two tabs for review and editing
                                    review_tab, json_tab = st.tabs(["Review Schema", "Edit JSON"])
                                    
                                    with review_tab:
                                        st.subheader("Review Generated Schema")
                                        
                                        # Display schema sections in expandable sections
                                        with st.expander("Basic Information", expanded=True):
                                            st.write(f"**Provider Name:** {schema.get('ProviderName', '')}")
                                            st.write(f"**Description:** {schema.get('Description', '')}")
                                            st.write("**Flags:**")
                                            for flag in schema.get('Flags', []):
                                                st.write(f"- {flag}")
                                        
                                        with st.expander("Column Mappings", expanded=True):
                                            st.write("**Field Mappings:**")
                                            for synonym in schema.get('Synonyms', []):
                                                logical_field = synonym.get('LogicalField', '')
                                                alternate_names = synonym.get('AlternateNames', [])
                                                st.write(f"- **{logical_field}**: {', '.join(alternate_names)}")
                                        
                                        with st.expander("Filters & Calculations"):
                                            st.write("**Filters:**")
                                            for filter_expr in schema.get('FilterTable', []):
                                                st.write(f"- {filter_expr}")
                                                
                                            st.write("**Calculations:**")
                                            for calc in schema.get('Calculations', []):
                                                new_field = calc.get('NewField', '')
                                                expression = calc.get('Expression', '')
                                                st.write(f"- **{new_field}**: {expression}")
                                        
                                        with st.expander("Advanced Settings"):
                                            st.write("**Hardcoded Fields:**")
                                            for field in schema.get('HardcodedFields', []):
                                                field_name = field.get('FieldName', '')
                                                value = field.get('Value', '')
                                                st.write(f"- **{field_name}**: {value}")
                                                
                                            if 'HeaderExtraction' in schema and schema['HeaderExtraction']:
                                                st.write("**Header Extraction Rules:**")
                                                for rule in schema.get('HeaderExtraction', []):
                                                    field_name = rule.get('FieldName', '')
                                                    start_delim = rule.get('StartDelim', '')
                                                    end_delim = rule.get('EndDelim', '')
                                                    st.write(f"- **{field_name}**: from '{start_delim}' to '{end_delim}'")
                                                    
                                            if 'UnpivotColumns' in schema and schema['UnpivotColumns']:
                                                st.write("**Unpivot Settings:**")
                                                unpivot = schema.get('UnpivotColumns', {})
                                                st.write(f"- **Key Columns:** {', '.join(unpivot.get('KeyColumns', []))}")
                                                st.write(f"- **Value Columns:** {', '.join(unpivot.get('ValueColumns', []))}")
                                    
                                    with json_tab:
                                        st.subheader("Edit Schema JSON")
                                        schema_json = json.dumps(schema, indent=2)
                                        edited_schema_json = st.text_area(
                                            "JSON Schema",
                                            value=schema_json,
                                            height=400
                                        )
                                        
                                        try:
                                            edited_schema = json.loads(edited_schema_json)
                                            schema = edited_schema  # Update schema with edited version
                                            st.session_state.generated_schema = schema  # Update session state
                                        except Exception:
                                            st.error("Invalid JSON format")
                                    
                                    # Save button - only show in review mode
                                    st.write("### Quick Save")
                                    st.write("Save the schema as-is, or edit it in the Provider Editor for more control:")
                                    
                                    if st.button("Save Provider", type="primary"):
                                        provider_config = load_provider_config()
                                        result = save_schema(schema, provider_config)
                                        
                                        if result.get('success', False):
                                            provider_name = result.get('provider_name', schema.get('ProviderName', 'Unknown'))
                                            st.success(f"Provider '{provider_name}' saved successfully!")
                                            
                                            # Add button to edit the new provider
                                            if st.button("Edit Saved Provider"):
                                                st.session_state.edit_mode = True
                                                st.session_state.selected_provider = provider_name.upper()
                                                st.session_state.create_method = "manual"
                                                st.rerun()
                                        else:
                                            st.error(f"Error saving provider: {result.get('error', 'Unknown error')}")
                            else:
                                st.error(f"Error generating schema: {result.get('error', 'Unknown error')}")
                                
                        except Exception as e:
                            st.error(f"Error during schema generation: {str(e)}")
                            with st.expander("See detailed error"):
                                import traceback
                                st.code(traceback.format_exc())
                
            except Exception as e:
                st.error(f"Error loading file: {str(e)}")
        
    except ImportError as e:
        st.warning(f"Schema Builder module not available: {e}")
        st.info("Make sure all required dependencies are installed:")
        st.code("pip install -r requirements.txt")

def show_provider_manager():
    """Main provider manager UI function."""
    st.title("Provider Configuration Manager")
    st.write("Create and manage provider configurations for Financial Data Harmonizer")
    
    # Provider sidebar
    show_provider_sidebar()
    
    # Determine which UI to show based on create method
    if not st.session_state.edit_mode and st.session_state.create_method == "schema_builder":
        # Show the schema builder interface for new provider creation
        generate_schema_from_sample()
    else:
        # Show the standard provider editor (either for editing or manual creation)
        if st.session_state.edit_mode and st.session_state.selected_provider:
            # Edit existing provider
            provider_data = load_provider(st.session_state.selected_provider)
        elif "prefilled_provider" in st.session_state and not st.session_state.edit_mode:
            # We're coming from schema generation with a prefilled schema
            provider_data = st.session_state.prefilled_provider
            # Leave prefilled_provider in session state for now
            # since we might need it if the user reloads the page
        else:
            # Brand new provider
            provider_data = get_default_provider_config()
        
        # Create tabs for the provider editor sections
        tab1, tab2, tab3, tab4 = st.tabs(["Basic Information", "Column Mappings", "Filters & Calculations", "Advanced Settings"])
        
        with tab1:
            provider_data = basic_information_section(provider_data)
            
        with tab2:
            provider_data = column_mappings_section(provider_data)
            
        with tab3:
            provider_data = filters_calculations_section(provider_data)
            
        with tab4:
            provider_data = advanced_settings_section(provider_data)
        
        # Save button
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("Save Provider", type="primary", use_container_width=True):
                if not provider_data.get("ProviderName", "").strip():
                    st.error("Provider name is required")
                else:
                    if save_provider(provider_data):
                        st.success(f"Provider {provider_data['ProviderName']} saved successfully!")
                        # Reset form for next creation or stay in edit mode
                        if not st.session_state.edit_mode:
                            reset_form()
        
        with col2:
            if st.button("Reset Form", use_container_width=True):
                reset_form()
                st.rerun()