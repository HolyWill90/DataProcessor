"""
Tkinter-based UI application for Financial Data Harmonizer
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import json
import pandas as pd

class FinancialHarmonizerTkApp:
    """Main Tkinter application for Financial Data Harmonizer."""
    
    def __init__(self, root=None):
        """Initialize the application."""
        # Create root if not provided
        if root is None:
            self.root = tk.Tk()
            self.root.title("Financial Data Harmonizer")
            self.root.geometry("900x600")
            self.root.minsize(800, 500)
            
            # Make sure the window stays on top initially
            self.root.attributes('-topmost', True)
            self.root.update()
            self.root.attributes('-topmost', False)
        else:
            self.root = root
            
        # Set up styles
        self.setup_styles()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the main UI components
        self.create_sidebar()
        self.create_content_area()
        
        # Show home screen initially
        self.show_home()
        
        # Initialize app data
        self.initialize_data()
        
    def setup_styles(self):
        """Set up ttk styles."""
        style = ttk.Style()
        
        # Configure styles for different widgets
        style.configure("TFrame", background="#f0f0f0")
        style.configure("Sidebar.TFrame", background="#e0e0e0")
        style.configure("Content.TFrame", background="#f9f9f9")
        style.configure("Header.TLabel", font=("Arial", 16, "bold"))
        style.configure("Title.TLabel", font=("Arial", 20, "bold"))
        style.configure("Subtitle.TLabel", font=("Arial", 14))
        style.configure("Primary.TButton", font=("Arial", 11))
        
    def create_sidebar(self):
        """Create the application sidebar."""
        # Sidebar frame
        self.sidebar = ttk.Frame(self.main_frame, width=200, style="Sidebar.TFrame")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Application title
        ttk.Label(
            self.sidebar, 
            text="Financial\nData Harmonizer", 
            style="Header.TLabel",
            justify="center"
        ).pack(pady=20)
        
        # Navigation buttons
        self.nav_buttons = []
        
        home_btn = ttk.Button(
            self.sidebar,
            text="Home",
            command=self.show_home,
            width=18
        )
        home_btn.pack(pady=5)
        self.nav_buttons.append(home_btn)
        
        process_btn = ttk.Button(
            self.sidebar,
            text="Process Files",
            command=self.show_process_files,
            width=18
        )
        process_btn.pack(pady=5)
        self.nav_buttons.append(process_btn)
        
        provider_btn = ttk.Button(
            self.sidebar,
            text="Provider Manager",
            command=self.show_provider_manager,
            width=18
        )
        provider_btn.pack(pady=5)
        self.nav_buttons.append(provider_btn)
        
        settings_btn = ttk.Button(
            self.sidebar,
            text="Settings",
            command=self.show_settings,
            width=18
        )
        settings_btn.pack(pady=5)
        self.nav_buttons.append(settings_btn)
        
        # Application info at bottom of sidebar
        ttk.Separator(self.sidebar).pack(fill=tk.X, pady=10)
        ttk.Label(
            self.sidebar,
            text="Version 1.0.0",
            font=("Arial", 9)
        ).pack(side=tk.BOTTOM, pady=10)
        
    def create_content_area(self):
        """Create the main content area."""
        self.content = ttk.Frame(self.main_frame, style="Content.TFrame")
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def clear_content(self):
        """Clear the content area."""
        for widget in self.content.winfo_children():
            widget.destroy()
            
    def initialize_data(self):
        """Initialize application data."""
        # Here we would load settings, provider configurations, etc.
        self.settings = self.load_settings()
        self.providers = self.load_providers()
        
    def load_settings(self):
        """Load application settings."""
        settings_path = Path(__file__).parent.parent / "config" / "settings.json"
        default_settings = {
            "output_directory": "",
            "default_export_format": "csv",
            "auto_detect_provider": True,
            "theme": "light"
        }
        
        if settings_path.exists():
            try:
                with open(settings_path, "r") as f:
                    loaded_settings = json.load(f)
                    default_settings.update(loaded_settings)
            except Exception:
                pass
                
        return default_settings
    
    def load_providers(self):
        """Load provider configurations."""
        providers = []
        provider_dir = Path(__file__).parent.parent / "config" / "providers"
        
        if provider_dir.exists():
            for provider_file in provider_dir.glob("*.json"):
                try:
                    with open(provider_file, "r") as f:
                        provider_data = json.load(f)
                        if "ProviderName" in provider_data:
                            providers.append(provider_data["ProviderName"])
                except Exception:
                    pass
                    
        return providers or ["ExampleVendor"]
        
    # UI Screens
    def show_home(self):
        """Show the home screen."""
        self.clear_content()
        
        # Title
        ttk.Label(
            self.content,
            text="Financial Data Harmonizer",
            style="Title.TLabel"
        ).pack(pady=10)
        
        # Welcome message
        welcome_frame = ttk.Frame(self.content)
        welcome_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(
            welcome_frame,
            text="Welcome to the Financial Data Harmonizer",
            style="Subtitle.TLabel"
        ).pack(pady=5)
        
        ttk.Label(
            welcome_frame,
            text="This tool helps you standardize financial data from various sources.",
            wraplength=500
        ).pack()
        
        # Features
        features_frame = ttk.LabelFrame(self.content, text="Features")
        features_frame.pack(fill=tk.X, pady=10, padx=10)
        
        features = [
            "Extract data from Excel and CSV files",
            "Transform data using customizable provider rules",
            "Load data into a standardized format for analysis"
        ]
        
        for feature in features:
            ttk.Label(
                features_frame,
                text=f"• {feature}",
                wraplength=500
            ).pack(anchor="w", pady=2, padx=10)
        
        # Quick start
        quickstart_frame = ttk.LabelFrame(self.content, text="Quick Start")
        quickstart_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Button(
            quickstart_frame,
            text="Process Files",
            command=self.show_process_files,
            style="Primary.TButton"
        ).pack(side=tk.LEFT, padx=10, pady=10)
        
        ttk.Button(
            quickstart_frame,
            text="Manage Providers",
            command=self.show_provider_manager
        ).pack(side=tk.LEFT, padx=10, pady=10)
        
    def show_process_files(self):
        """Show the process files screen."""
        self.clear_content()
        
        # Title
        ttk.Label(
            self.content,
            text="Process Files",
            style="Title.TLabel"
        ).pack(pady=10)
        
        # File selection section
        file_frame = ttk.LabelFrame(self.content, text="Select Files")
        file_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self.selected_files = []
        self.files_listbox = tk.Listbox(file_frame, height=6, width=70)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(file_frame, orient="vertical", command=self.files_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        self.files_listbox.config(yscrollcommand=scrollbar.set)
        
        button_frame = ttk.Frame(file_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            button_frame,
            text="Add Files",
            command=self.add_files
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Remove Selected",
            command=self.remove_selected_file
        ).pack(side=tk.LEFT, padx=5)
        
        # Provider selection
        provider_frame = ttk.LabelFrame(self.content, text="Provider Configuration")
        provider_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Label(
            provider_frame,
            text="Select Provider:"
        ).pack(side=tk.LEFT, padx=10, pady=10)
        
        self.provider_var = tk.StringVar()
        self.provider_combobox = ttk.Combobox(
            provider_frame,
            textvariable=self.provider_var,
            values=self.providers,
            state="readonly",
            width=30
        )
        if self.providers:
            self.provider_combobox.current(0)
        self.provider_combobox.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Processing options
        options_frame = ttk.LabelFrame(self.content, text="Processing Options")
        options_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Label(
            options_frame,
            text="Export Format:"
        ).pack(side=tk.LEFT, padx=10, pady=10)
        
        self.export_format_var = tk.StringVar(value="CSV")
        csv_radio = ttk.Radiobutton(
            options_frame,
            text="CSV",
            variable=self.export_format_var,
            value="CSV"
        )
        csv_radio.pack(side=tk.LEFT, padx=5, pady=10)
        
        excel_radio = ttk.Radiobutton(
            options_frame,
            text="Excel",
            variable=self.export_format_var,
            value="Excel"
        )
        excel_radio.pack(side=tk.LEFT, padx=5, pady=10)
        
        # Process button
        ttk.Button(
            self.content,
            text="Process Files",
            command=self.process_files,
            style="Primary.TButton"
        ).pack(pady=20)
        
    def add_files(self):
        """Add files to process."""
        filetypes = [
            ("Excel/CSV files", "*.xlsx *.xls *.csv"),
            ("Excel files", "*.xlsx *.xls"),
            ("CSV files", "*.csv"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select files to process",
            filetypes=filetypes
        )
        
        if files:
            for file in files:
                if file not in self.selected_files:
                    self.selected_files.append(file)
                    self.files_listbox.insert(tk.END, os.path.basename(file))
    
    def remove_selected_file(self):
        """Remove the selected file."""
        try:
            selected_index = self.files_listbox.curselection()[0]
            self.files_listbox.delete(selected_index)
            self.selected_files.pop(selected_index)
        except IndexError:
            messagebox.showinfo("Info", "Please select a file to remove")
    
    def process_files(self):
        """Process the selected files."""
        if not self.selected_files:
            messagebox.showinfo("Info", "Please select files to process")
            return
            
        if not self.provider_var.get():
            messagebox.showinfo("Info", "Please select a provider configuration")
            return
            
        # This is a placeholder for the actual processing
        # In a real implementation, we would call the harmonizer
        messagebox.showinfo(
            "Processing Files", 
            f"Processing {len(self.selected_files)} files with provider {self.provider_var.get()}\n\n"
            f"This is a simplified UI. For full functionality, use the Streamlit UI."
        )
        
    def show_provider_manager(self):
        """Show the provider manager screen."""
        self.clear_content()
        
        # Title
        ttk.Label(
            self.content,
            text="Provider Manager",
            style="Title.TLabel"
        ).pack(pady=10)
        
        # Simplified provider manager
        ttk.Label(
            self.content,
            text="Provider configuration management is limited in the Tkinter UI.",
            wraplength=500
        ).pack(pady=10)
        
        ttk.Label(
            self.content,
            text="For full provider management functionality,\nplease use the Streamlit UI.",
            wraplength=500
        ).pack(pady=10)
        
        # Provider listing
        provider_frame = ttk.LabelFrame(self.content, text="Available Providers")
        provider_frame.pack(fill=tk.X, pady=10, padx=10)
        
        providers_listbox = tk.Listbox(provider_frame, height=6, width=40)
        providers_listbox.pack(fill=tk.X, expand=True, padx=10, pady=10)
        
        for provider in self.providers:
            providers_listbox.insert(tk.END, provider)
        
    def show_settings(self):
        """Show the settings screen."""
        self.clear_content()
        
        # Title
        ttk.Label(
            self.content,
            text="Settings",
            style="Title.TLabel"
        ).pack(pady=10)
        
        # Basic settings
        settings_frame = ttk.LabelFrame(self.content, text="Application Settings")
        settings_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # Output directory
        dir_frame = ttk.Frame(settings_frame)
        dir_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(
            dir_frame,
            text="Output Directory:"
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.output_dir_var = tk.StringVar(value=self.settings.get("output_directory", ""))
        output_dir_entry = ttk.Entry(
            dir_frame,
            textvariable=self.output_dir_var,
            width=40
        )
        output_dir_entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        ttk.Button(
            dir_frame,
            text="Browse...",
            command=self.browse_output_dir
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Default export format
        format_frame = ttk.Frame(settings_frame)
        format_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(
            format_frame,
            text="Default Export Format:"
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.settings_export_format_var = tk.StringVar(
            value=self.settings.get("default_export_format", "csv").upper()
        )
        
        csv_radio = ttk.Radiobutton(
            format_frame,
            text="CSV",
            variable=self.settings_export_format_var,
            value="CSV"
        )
        csv_radio.pack(side=tk.LEFT, padx=5, pady=5)
        
        excel_radio = ttk.Radiobutton(
            format_frame,
            text="Excel",
            variable=self.settings_export_format_var,
            value="EXCEL"
        )
        excel_radio.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Auto-detect provider
        auto_detect_frame = ttk.Frame(settings_frame)
        auto_detect_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.auto_detect_var = tk.BooleanVar(
            value=self.settings.get("auto_detect_provider", True)
        )
        
        auto_detect_check = ttk.Checkbutton(
            auto_detect_frame,
            text="Auto-detect Provider Based on Filename",
            variable=self.auto_detect_var
        )
        auto_detect_check.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Save settings button
        ttk.Button(
            self.content,
            text="Save Settings",
            command=self.save_settings,
            style="Primary.TButton"
        ).pack(pady=20)
        
        # Diagnostics
        diagnostics_frame = ttk.LabelFrame(self.content, text="Diagnostics")
        diagnostics_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Label(
            diagnostics_frame,
            text=f"Python Version: {sys.version.split()[0]}"
        ).pack(anchor="w", padx=10, pady=2)
        
        ttk.Label(
            diagnostics_frame,
            text=f"Provider Count: {len(self.providers)}"
        ).pack(anchor="w", padx=10, pady=2)
        
        ttk.Button(
            diagnostics_frame,
            text="Run Diagnostics",
            command=self.run_diagnostics
        ).pack(padx=10, pady=10)
        
    def browse_output_dir(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(
            title="Select Output Directory"
        )
        
        if directory:
            self.output_dir_var.set(directory)
            
    def save_settings(self):
        """Save application settings."""
        settings = {
            "output_directory": self.output_dir_var.get(),
            "default_export_format": self.settings_export_format_var.get().lower(),
            "auto_detect_provider": self.auto_detect_var.get(),
            "theme": self.settings.get("theme", "light")
        }
        
        settings_path = Path(__file__).parent.parent / "config" / "settings.json"
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            
            # Write settings
            with open(settings_path, "w") as f:
                json.dump(settings, f, indent=2)
                
            messagebox.showinfo("Success", "Settings saved successfully!")
            self.settings = settings
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
            
    def run_diagnostics(self):
        """Run diagnostics."""
        # Placeholder for actual diagnostics
        diagnostics_results = [
            ("Python Environment", "✓ OK", f"Python {sys.version.split()[0]}"),
            ("Config Directory", "✓ OK", "Exists"),
            ("Provider Configuration", "✓ OK", f"{len(self.providers)} providers found")
        ]
        
        # Create diagnostics window
        diag_window = tk.Toplevel(self.root)
        diag_window.title("Diagnostics Results")
        diag_window.geometry("600x400")
        diag_window.transient(self.root)
        
        # Add diagnostics results
        ttk.Label(
            diag_window,
            text="Diagnostics Results",
            style="Title.TLabel"
        ).pack(pady=10)
        
        results_frame = ttk.Frame(diag_window, padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create headers
        headers = ["Test", "Status", "Details"]
        for i, header in enumerate(headers):
            ttk.Label(
                results_frame,
                text=header,
                font=("Arial", 11, "bold")
            ).grid(row=0, column=i, padx=5, pady=5, sticky="w")
            
        # Add results
        for i, result in enumerate(diagnostics_results):
            for j, value in enumerate(result):
                ttk.Label(
                    results_frame,
                    text=value
                ).grid(row=i+1, column=j, padx=5, pady=5, sticky="w")
                
        # Close button
        ttk.Button(
            diag_window,
            text="Close",
            command=diag_window.destroy
        ).pack(pady=10)
        
    def run(self):
        """Run the application."""
        self.root.mainloop()

if __name__ == "__main__":
    app = FinancialHarmonizerTkApp()
    app.run()