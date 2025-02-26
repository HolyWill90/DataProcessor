"""
Fix script for UI issues in the Financial Data Harmonizer
This script attempts to fix Streamlit circular import issues and provides a fallback UI if needed
"""
import os
import sys
import subprocess
from pathlib import Path
import importlib
import traceback
import shutil

def check_streamlit():
    """Check if Streamlit is importable and working correctly."""
    print("Checking Streamlit installation...")
    
    try:
        # Try to import streamlit - but do it in a separate process to avoid affecting our current environment
        result = subprocess.run(
            [sys.executable, "-c", "import streamlit; print('Streamlit works!')"],
            capture_output=True,
            text=True
        )
        
        if "Streamlit works!" in result.stdout:
            print("✓ Basic Streamlit import successful")
            return True
        else:
            print(f"✗ Streamlit import failed with output: {result.stdout}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Streamlit check failed: {str(e)}")
        return False

def fix_streamlit():
    """Attempt to fix Streamlit installation."""
    print("\nAttempting to fix Streamlit installation...")
    
    try:
        # Uninstall current streamlit
        print("1. Uninstalling current Streamlit...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "uninstall", "-y", "streamlit"
        ])
        
        # Remove any cached files
        print("2. Clearing Python cache directories...")
        for directory in sys.path:
            if os.path.isdir(directory):
                for root, dirs, files in os.walk(directory):
                    for d in dirs:
                        if d == "__pycache__" and "streamlit" in root:
                            pycache_dir = os.path.join(root, d)
                            print(f"   Removing {pycache_dir}")
                            try:
                                shutil.rmtree(pycache_dir)
                            except Exception as e:
                                print(f"   Failed to remove {pycache_dir}: {e}")
        
        # Install a specific version known to work well
        print("3. Installing Streamlit 1.22.0 (known stable version)...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "streamlit==1.22.0"
        ])
        
        print("✓ Streamlit reinstallation complete")
        
        # Check if fixed
        if check_streamlit():
            return True
        else:
            print("✗ Streamlit still has issues after reinstallation")
            return False
        
    except Exception as e:
        print(f"✗ Failed to fix Streamlit: {str(e)}")
        traceback.print_exc()
        return False

def run_streamlit_in_isolation():
    """Launch Streamlit in isolation to avoid circular imports."""
    print("\nLaunching Streamlit UI in isolation...")
    
    current_dir = Path(__file__).parent
    ui_script = current_dir / "ui_streamlit.py"
    
    if not ui_script.exists():
        print(f"✗ UI script not found at {ui_script}")
        return False
    
    try:
        # Create a minimal launcher script
        launcher_path = current_dir / "streamlit_launcher.py"
        with open(launcher_path, "w") as f:
            f.write("""
# Simple launcher to avoid circular imports
import subprocess
import sys
import os

streamlit_file = os.path.abspath(sys.argv[1])
print(f"Launching Streamlit for {streamlit_file}")

subprocess.run([
    "streamlit", "run", streamlit_file, "--server.headless", "true"
])
""")
        
        print(f"Created temporary launcher script at {launcher_path}")
        
        # Execute the launcher in a new process
        print("Running Streamlit via launcher...")
        process = subprocess.Popen([
            sys.executable, 
            str(launcher_path), 
            str(ui_script)
        ])
        
        print("\nIf a browser window doesn't open automatically,")
        print("go to http://localhost:8501 in your web browser")
        
        # Wait for process to finish or user to interrupt
        process.wait()
        
        # Clean up launcher
        try:
            os.unlink(launcher_path)
        except:
            pass
            
        return True
        
    except Exception as e:
        print(f"✗ Failed to launch Streamlit UI: {str(e)}")
        traceback.print_exc()
        return False

def run_tkinter_ui():
    """Launch the Tkinter UI as fallback."""
    print("\nLaunching fallback Tkinter UI for Financial Data Harmonizer...")
    
    # We'll create a very simple UI if needed
    simple_ui_code = """
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import json

# Add the current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Try to import the harmonizer
try:
    from harmonizer_app import FinancialHarmonizer
    from config.providers import ProviderConfig
    harmonizer_available = True
except ImportError as e:
    print(f"Error importing harmonizer: {e}")
    harmonizer_available = False

class SimpleHarmonizerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Financial Data Harmonizer")
        self.root.geometry("800x600")
        
        # Initialize harmonizer if available
        if harmonizer_available:
            self.harmonizer = FinancialHarmonizer()
            try:
                self.provider_config = ProviderConfig()
                self.providers = list(self.provider_config.providers_cache.keys())
            except:
                self.providers = ["ExampleVendor"]
        else:
            self.harmonizer = None
            self.provider_config = None
            self.providers = ["ExampleVendor"]
        
        self.create_ui()
        
    def create_ui(self):
        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(
            main_frame, 
            text="Financial Data Harmonizer", 
            font=("Arial", 16, "bold")
        ).pack(pady=10)
        
        if not harmonizer_available:
            ttk.Label(
                main_frame,
                text="WARNING: Harmonizer module not available. Limited functionality.",
                foreground="red"
            ).pack(pady=5)
        
        # File selection frame
        files_frame = ttk.LabelFrame(main_frame, text="Select Files", padding=10)
        files_frame.pack(fill=tk.X, pady=10)
        
        self.files_listbox = tk.Listbox(files_frame, height=5)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        files_scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.files_listbox.yview)
        files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_listbox.config(yscrollcommand=files_scrollbar.set)
        
        files_buttons_frame = ttk.Frame(files_frame)
        files_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            files_buttons_frame, 
            text="Add Files", 
            command=self.add_files
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            files_buttons_frame, 
            text="Clear", 
            command=self.clear_files
        ).pack(side=tk.LEFT, padx=5)
        
        # Provider selection frame
        provider_frame = ttk.LabelFrame(main_frame, text="Provider Configuration", padding=10)
        provider_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(provider_frame, text="Select Provider:").pack(anchor=tk.W)
        
        self.provider_var = tk.StringVar()
        if self.providers:
            self.provider_var.set(self.providers[0])
        
        self.provider_dropdown = ttk.Combobox(
            provider_frame, 
            textvariable=self.provider_var,
            values=self.providers,
            state="readonly"
        )
        self.provider_dropdown.pack(fill=tk.X, pady=5)
        
        # Process button
        ttk.Button(
            main_frame, 
            text="Process Files", 
            command=self.process_files,
            style="Accent.TButton"
        ).pack(fill=tk.X, pady=10)
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.results_text = tk.Text(results_frame, height=10)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=results_scrollbar.set)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN).pack(side=tk.BOTTOM, fill=tk.X)
        
    def add_files(self):
        filetypes = [
            ("Excel & CSV Files", "*.xlsx *.xls *.csv"),
            ("Excel Files", "*.xlsx *.xls"),
            ("CSV Files", "*.csv"),
            ("All Files", "*.*")
        ]
        
        filenames = filedialog.askopenfilenames(
            title="Select files to process",
            filetypes=filetypes
        )
        
        if not filenames:
            return
            
        for filename in filenames:
            self.files_listbox.insert(tk.END, filename)
            
        self.status_var.set(f"Added {len(filenames)} files")
        
    def clear_files(self):
        self.files_listbox.delete(0, tk.END)
        self.status_var.set("File list cleared")
        
    def process_files(self):
        if not harmonizer_available:
            messagebox.showerror(
                "Error", 
                "Harmonizer module not available. Cannot process files."
            )
            return
            
        files = self.files_listbox.get(0, tk.END)
        if not files:
            messagebox.showinfo("Error", "Please select files to process")
            return
            
        provider = self.provider_var.get()
        if not provider:
            messagebox.showinfo("Error", "Please select a provider configuration")
            return
            
        self.status_var.set("Processing files...")
        self.root.update()
        
        try:
            results = []
            for file_path in files:
                result = self.harmonizer.process_file(file_path=file_path, provider_name=provider)
                results.append(result)
            
            self.results_text.delete("1.0", tk.END)
            
            success_count = sum(1 for r in results if r.get("success", False))
            error_count = len(results) - success_count
            
            self.results_text.insert(tk.END, f"Processed {len(results)} files\\n")
            self.results_text.insert(tk.END, f"Success: {success_count}\\n")
            self.results_text.insert(tk.END, f"Errors: {error_count}\\n\\n")
            
            if self.harmonizer.master_data is not None:
                row_count = len(self.harmonizer.master_data)
                col_count = len(self.harmonizer.master_data.columns)
                
                self.results_text.insert(tk.END, f"Total rows: {row_count}\\n")
                self.results_text.insert(tk.END, f"Total columns: {col_count}\\n\\n")
                
                # Ask for save location
                save_path = filedialog.asksaveasfilename(
                    title="Save Results",
                    defaultextension=".csv",
                    filetypes=[
                        ("CSV Files", "*.csv"),
                        ("Excel Files", "*.xlsx")
                    ]
                )
                
                if save_path:
                    _, ext = os.path.splitext(save_path)
                    format_type = "csv" if ext.lower() == ".csv" else "excel"
                    
                    export_result = self.harmonizer.export_results(
                        output_path=save_path,
                        format=format_type
                    )
                    
                    if export_result.get("success", False):
                        self.results_text.insert(tk.END, f"Results saved to: {save_path}\\n")
                    else:
                        self.results_text.insert(tk.END, f"Error saving results: {export_result.get('error', 'Unknown error')}\\n")
            
            self.status_var.set("Processing complete")
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            self.results_text.delete("1.0", tk.END)
            self.results_text.insert(tk.END, f"Error processing files:\\n{str(e)}")
            traceback.print_exc()

def main():
    root = tk.Tk()
    app = SimpleHarmonizerUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
"""
    
    # Create the fallback UI file
    simple_ui_path = Path(__file__).parent / "simple_ui_fixed.py"
    
    try:
        with open(simple_ui_path, 'w') as f:
            f.write(simple_ui_code)
            
        print(f"Created fallback UI at {simple_ui_path}")
        
        # Run the fallback UI
        subprocess.call([sys.executable, str(simple_ui_path)])
        return True
        
    except Exception as e:
        print(f"✗ Failed to create or run fallback UI: {str(e)}")
        traceback.print_exc()
        return False

def fix_python_path():
    """Fix Python path to avoid module conflicts."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Remove current directory from path if it exists
    if current_dir in sys.path:
        sys.path.remove(current_dir)
        
    # Add it at the beginning to ensure our modules are found first
    sys.path.insert(0, current_dir)
    
    print(f"✓ Python path fixed. Current path: {sys.path[0]}")
    return True

def main():
    """Main function."""
    print("==== Financial Data Harmonizer UI Fix Tool ====")
    
    print("\nChecking your setup...")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    # Fix Python path
    fix_python_path()
    
    # Try the streamlit approach first
    streamlit_working = check_streamlit()
    
    if not streamlit_working:
        print("\nStreamlit has issues. Would you like to attempt to fix it? (y/n)")
        choice = input("> ").lower().strip()
        
        if choice.startswith('y'):
            success = fix_streamlit()
            if success:
                streamlit_working = True
                print("\nStreamlit fixed successfully!")
        else:
            print("\nSkipping Streamlit fix attempt.")
    
    # Try to run the preferred UI 
    if streamlit_working:
        print("\nAttempting to run Streamlit UI in isolation...")
        success = run_streamlit_in_isolation()
        
        if not success:
            print("\nFalling back to Tkinter UI...")
            run_tkinter_ui()
    else:
        print("\nRunning Tkinter UI instead...")
        run_tkinter_ui()
    
    print("\n==== UI Session Complete ====")
    
if __name__ == "__main__":
    main()
