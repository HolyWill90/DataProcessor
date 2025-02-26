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
    
    # Create or edit options
    action = st.sidebar.radio("Action", ["Create New", "Edit Existing"], index=0 if not st.session_state.edit_mode else 1)
    
    if action == "Create New":
        st.session_state.edit_mode = False
        st.session_state.selected_provider = None
    else:
        st.session_state.edit_mode = True
        
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
                st.experimental_rerun()
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
                    st.experimental_rerun()
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
    
    tab1, tab2, tab3 = st.tabs(["Hardcoded Fields", "Header Extraction", "JSON View"])
    
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

def show_provider_manager():
    """Main provider manager UI function."""
    st.title("Provider Configuration Manager")
    st.write("Create and manage provider configurations for Financial Data Harmonizer")
    
    # Provider sidebar
    show_provider_sidebar()
    
    # If we're editing, load the provider data
    if st.session_state.edit_mode and st.session_state.selected_provider:
        provider_data = load_provider(st.session_state.selected_provider)
    else:
        provider_data = get_default_provider_config()
    
    # Create tabs for the different sections
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
            st.experimental