"""
Settings UI for Financial Data Harmonizer
"""
import os
import json
import streamlit as st
from pathlib import Path
import subprocess
import sys
import shutil
import importlib

def show_settings():
    """Settings UI for the application."""
    st.title("Settings")
    
    # Create tabs for different settings categories
    tab1, tab2, tab3 = st.tabs(["Application", "Advanced", "Diagnostics"])
    
    with tab1:
        st.subheader("Application Settings")
        
        # Get settings path
        settings_path = Path(__file__).parent.parent / "config" / "settings.json"
        
        # Default settings
        default_settings = {
            "output_directory": "",
            "default_export_format": "csv",
            "auto_detect_provider": True,
            "theme": "light",
            "sharepoint_enabled": False,
            "sharepoint_site": "",
            "auto_update": True
        }
        
        # Load settings
        settings = default_settings.copy()
        if settings_path.exists():
            try:
                with open(settings_path, "r") as f:
                    loaded_settings = json.load(f)
                    settings.update(loaded_settings)
            except Exception as e:
                st.error(f"Error loading settings: {e}")
        
        # Output directory
        settings["output_directory"] = st.text_input(
            "Default Output Directory",
            value=settings.get("output_directory", ""),
            help="Where harmonized files will be saved by default"
        )
        
        # Output format
        settings["default_export_format"] = st.radio(
            "Default Export Format",
            options=["csv", "excel"],
            horizontal=True,
            index=0 if settings.get("default_export_format") == "csv" else 1,
            help="Format to use when exporting data"
        )
        
        # Auto-detect provider
        settings["auto_detect_provider"] = st.checkbox(
            "Auto-detect Provider",
            value=settings.get("auto_detect_provider", True),
            help="Automatically match files to providers based on name"
        )
        
        # Theme
        settings["theme"] = st.selectbox(
            "UI Theme",
            options=["light", "dark", "system"],
            index=["light", "dark", "system"].index(settings.get("theme", "light")),
            help="Visual theme for the application"
        )
        
        # Save settings button
        if st.button("Save Settings", type="primary", use_container_width=True):
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(settings_path), exist_ok=True)
                
                # Write settings
                with open(settings_path, "w") as f:
                    json.dump(settings, f, indent=2)
                
                st.success("Settings saved successfully!")
            except Exception as e:
                st.error(f"Error saving settings: {e}")
    
    with tab2:
        st.subheader("Advanced Settings")
        
        # SharePoint integration settings
        st.write("### SharePoint Integration")
        
        settings["sharepoint_enabled"] = st.checkbox(
            "Enable SharePoint Integration",
            value=settings.get("sharepoint_enabled", False),
            help="Connect to SharePoint to retrieve files"
        )
        
        if settings["sharepoint_enabled"]:
            # Check if shareplum is installed
            try:
                importlib.import_module("shareplum")
                sharepoint_available = True
            except ImportError:
                sharepoint_available = False
                st.warning("SharePoint integration requires the shareplum package, which is not installed.")
                if st.button("Install SharePoint Requirements"):
                    try:
                        subprocess.check_call([
                            sys.executable, "-m", "pip", "install", "shareplum"
                        ])
                        st.success("SharePoint requirements installed successfully! Please restart the application.")
                    except Exception as e:
                        st.error(f"Failed to install requirements: {e}")
            
            if sharepoint_available:
                settings["sharepoint_site"] = st.text_input(
                    "SharePoint Site URL",
                    value=settings.get("sharepoint_site", ""),
                    help="URL of the SharePoint site (e.g., https://company.sharepoint.com/sites/mysite)"
                )
                
                # SharePoint credentials
                col1, col2 = st.columns(2)
                
                with col1:
                    sharepoint_username = st.text_input(
                        "SharePoint Username",
                        type="default",
                        help="Your SharePoint username"
                    )
                
                with col2:
                    sharepoint_password = st.text_input(
                        "SharePoint Password",
                        type="password",
                        help="Your SharePoint password"
                    )
                
                if sharepoint_username and sharepoint_password:
                    if st.button("Test SharePoint Connection"):
                        try:
                            from shareplum import Site, Office365
                            auth = Office365(settings["sharepoint_site"], username=sharepoint_username, password=sharepoint_password)
                            site = Site(settings["sharepoint_site"], auth.GetCookie())
                            st.success("SharePoint connection successful!")
                            
                            # Save credentials securely
                            creds_path = Path(__file__).parent.parent / "config" / "sharepoint_credentials.json"
                            with open(creds_path, "w") as f:
                                json.dump({
                                    "username": sharepoint_username,
                                    "password": sharepoint_password
                                }, f)
                            
                        except Exception as e:
                            st.error(f"SharePoint connection failed: {e}")
        
        # Save advanced settings button
        if st.button("Save Advanced Settings", type="primary", use_container_width=True):
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(settings_path), exist_ok=True)
                
                # Write settings
                with open(settings_path, "w") as f:
                    json.dump(settings, f, indent=2)
                
                st.success("Advanced settings saved successfully!")
            except Exception as e:
                st.error(f"Error saving advanced settings: {e}")
    
    with tab3:
        st.subheader("Diagnostics & Troubleshooting")
        
        # System info
        st.write("### System Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Python Version:** {sys.version.split()[0]}")
            st.write(f"**Platform:** {sys.platform}")
            
            try:
                import pandas as pd
                st.write(f"**Pandas Version:** {pd.__version__}")
            except:
                st.write("**Pandas Version:** Not installed")
                
            try:
                import streamlit as st_version
                st.write(f"**Streamlit Version:** {st_version.__version__}")
            except:
                st.write("**Streamlit Version:** Not installed")
        
        with col2:
            config_dir = Path(__file__).parent.parent / "config"
            st.write(f"**Config Directory:** {config_dir}")
            
            # Count providers
            provider_config_dir = config_dir / "providers"
            provider_count = len(list(provider_config_dir.glob("*.json"))) if provider_config_dir.exists() else 0
            st.write(f"**Provider Configurations:** {provider_count}")
            
            # Check if settings file exists
            settings_exists = (config_dir / "settings.json").exists()
            st.write(f"**Settings File:** {'Exists' if settings_exists else 'Missing'}")
        
        # Run diagnostics
        st.write("### Diagnostics")
        
        if st.button("Run Diagnostics"):
            with st.spinner("Running diagnostics..."):
                diagnostics_results = []
                
                # Check Python environment
                diagnostics_results.append({
                    "Test": "Python Environment",
                    "Status": "✅ OK",
                    "Details": f"Python {sys.version.split()[0]}"
                })
                
                # Check required packages
                required_packages = ["pandas", "numpy", "streamlit", "openpyxl"]
                for package in required_packages:
                    try:
                        module = importlib.import_module(package)
                        version = getattr(module, "__version__", "Unknown")
                        diagnostics_results.append({
                            "Test": f"Package: {package}",
                            "Status": "✅ OK",
                            "Details": f"Version {version}"
                        })
                    except ImportError:
                        diagnostics_results.append({
                            "Test": f"Package: {package}",
                            "Status": "❌ Missing",
                            "Details": "Package not installed"
                        })
                
                # Check config directory
                if config_dir.exists():
                    diagnostics_results.append({
                        "Test": "Config Directory",
                        "Status": "✅ OK",
                        "Details": str(config_dir)
                    })
                else:
                    diagnostics_results.append({
                        "Test": "Config Directory",
                        "Status": "❌ Missing",
                        "Details": "Directory not found"
                    })
                    
                # Check provider configurations
                provider_dir = config_dir / "providers"
                if provider_dir.exists():
                    provider_files = list(provider_dir.glob("*.json"))
                    if provider_files:
                        diagnostics_results.append({
                            "Test": "Provider Configurations",
                            "Status": "✅ OK",
                            "Details": f"{len(provider_files)} provider(s) found"
                        })
                    else:
                        diagnostics_results.append({
                            "Test": "Provider Configurations",
                            "Status": "⚠️ Warning",
                            "Details": "No provider configurations found"
                        })
                else:
                    diagnostics_results.append({
                        "Test": "Provider Configurations",
                        "Status": "❌ Missing",
                        "Details": "Provider directory not found"
                    })
                
                # Display results
                st.subheader("Diagnostics Results")
                for result in diagnostics_results:
                    st.write(f"{result['Status']} **{result['Test']}:** {result['Details']}")
        
        # Reset application
        st.write("### Application Reset")
        
        reset_expander = st.expander("Reset Application")
        with reset_expander:
            st.warning("This will reset the application to its default state. All settings and custom configurations will be lost.")
            
            reset_type = st.radio(
                "Reset Type",
                options=["Settings Only", "Providers Only", "Complete Reset"],
                horizontal=True,
                help="Choose what to reset"
            )
            
            if st.button("Reset Application", type="primary"):
                confirm = st.popover("Are you sure?")
                with confirm:
                    if st.button("Yes, I'm sure", type="primary"):
                        if reset_type == "Settings Only":
                            # Delete settings file
                            if (config_dir / "settings.json").exists():
                                (config_dir / "settings.json").unlink()
                            st.success("Settings reset to defaults.")
                            
                        elif reset_type == "Providers Only":
                            # Delete all provider files except example.json
                            if provider_dir.exists():
                                for provider_file in provider_dir.glob("*.json"):
                                    if provider_file.name.lower() != "example.json":
                                        provider_file.unlink()
                                st.success("Provider configurations reset.")
                            
                        elif reset_type == "Complete Reset":
                            # Delete entire config directory and recreate with defaults
                            if config_dir.exists():
                                shutil.rmtree(config_dir)
                            
                            # Recreate directories
                            os.makedirs(config_dir, exist_ok=True)
                            os.makedirs(config_dir / "providers", exist_ok=True)
                            
                            # Create example provider
                            example_provider = {
                                "ProviderName": "ExampleVendor",
                                "Description": "Example provider created after reset",
                                "Flags": ["StandardFormat"],
                                "Synonyms": [
                                    {"LogicalField": "date", "AlternateNames": ["Date", "Transaction Date"]},
                                    {"LogicalField": "amount", "AlternateNames": ["Amount", "Total"]},
                                    {"LogicalField": "description", "AlternateNames": ["Description", "Details"]},
                                    {"LogicalField": "reference", "AlternateNames": ["Reference", "Ref"]}
                                ]
                            }
                            
                            with open(config_dir / "providers" / "example.json", "w") as f:
                                json.dump(example_provider, f, indent=2)
                            
                            st.success("Application completely reset to defaults.")
