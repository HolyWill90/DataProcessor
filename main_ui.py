"""
Financial Data Harmonizer - Main UI
This is the primary entry point for the application's user interface
"""
import os
import sys
import subprocess
from pathlib import Path
import importlib
import traceback
import uuid

# Initialize path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Check if we're running in streamlit
IN_STREAMLIT = os.environ.get('STREAMLIT_RUNTIME_LOOP') == 'true'

# Create a lock file to prevent multiple instances
LOCK_FILE = Path(current_dir) / ".harmonizer.lock"
INSTANCE_ID = str(uuid.uuid4())

def is_already_running():
    """Check if another instance is running by checking the lock file."""
    if LOCK_FILE.exists():
        try:
            # Check if the process in the lock file is still running
            with open(LOCK_FILE, "r") as f:
                pid = f.read().strip()
            
            # Try to check if the process is running
            if pid:
                # On Windows
                if sys.platform.startswith("win"):
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    PROCESS_QUERY_INFORMATION = 0x0400
                    handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, int(pid))
                    if handle:
                        kernel32.CloseHandle(handle)
                        return True
                # On Unix-like systems
                else:
                    try:
                        os.kill(int(pid), 0)
                        return True
                    except OSError:
                        pass
        except:
            pass
            
        # Lock file exists but process not running - clean up the stale lock
        try:
            LOCK_FILE.unlink()
        except:
            pass
            
    return False

def create_lock_file():
    """Create a lock file with the current process ID."""
    try:
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
    except:
        print("Warning: Could not create lock file")

def remove_lock_file():
    """Remove the lock file."""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except:
        print("Warning: Could not remove lock file")

def check_streamlit_importable():
    """Check if streamlit can be imported without issues."""
    try:
        # Try in subprocess to avoid affecting current process
        result = subprocess.run(
            [sys.executable, "-c", "import streamlit; print('Streamlit OK')"],
            capture_output=True,
            text=True
        )
        return "Streamlit OK" in result.stdout
    except Exception as e:
        print(f"Error checking Streamlit: {e}")
        return False

def fix_streamlit_installation():
    """Attempt to fix Streamlit installation."""
    print("\nAttempting to fix Streamlit installation...")
    
    try:
        # Uninstall current streamlit
        subprocess.check_call([
            sys.executable, "-m", "pip", "uninstall", "-y", "streamlit"
        ])
        
        # Remove any cached files
        for directory in sys.path:
            if os.path.isdir(directory):
                for root, dirs, files in os.walk(directory):
                    for d in dirs:
                        if d == "__pycache__" and "streamlit" in root:
                            pycache_dir = os.path.join(root, d)
                            print(f"   Removing {pycache_dir}")
                            try:
                                import shutil
                                shutil.rmtree(pycache_dir)
                            except Exception as e:
                                print(f"   Failed to remove {pycache_dir}: {e}")
        
        # Install a specific version known to work well
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "streamlit==1.22.0"
        ])
        
        return check_streamlit_importable()
    except Exception as e:
        print(f"Failed to fix Streamlit: {e}")
        traceback.print_exc()
        return False

def run_streamlit_ui():
    """Run the Streamlit UI."""
    # Get path to this script
    script_path = Path(__file__).resolve()
    
    # Try to run streamlit
    cmd = [sys.executable, "-m", "streamlit", "run", str(script_path), "--server.headless", "true"]
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        # Create a clean environment without the launcher flag
        env = os.environ.copy()
        if 'FH_LAUNCHER_STARTED' in env:
            del env['FH_LAUNCHER_STARTED']
            
        # Use run instead of Popen to wait for completion
        subprocess.run(cmd, env=env)
        return True
    except Exception as e:
        print(f"Failed to launch Streamlit UI: {e}")
        traceback.print_exc()
        return False

def run_tkinter_ui():
    """Run the fallback Tkinter UI."""
    print("\nFalling back to Tkinter UI...")
    
    try:
        # Import the Tkinter UI module
        from ui.tkinter_ui import TkinterApp
        
        # Run the Tkinter UI
        TkinterApp().run()
        return True
    except Exception as e:
        print(f"Failed to launch Tkinter UI: {e}")
        traceback.print_exc()
        
        # Try to create a basic UI if the proper one fails
        try:
            import tkinter as tk
            from tkinter import ttk, messagebox
            
            root = tk.Tk()
            root.title("Financial Data Harmonizer - Error")
            root.geometry("600x400")
            
            ttk.Label(
                root, 
                text="Error Launching UI", 
                font=("Arial", 16, "bold")
            ).pack(pady=20)
            
            ttk.Label(
                root, 
                text=f"Failed to launch UI: {str(e)}", 
                wraplength=500
            ).pack(pady=10)
            
            ttk.Label(
                root, 
                text="Please check the console for more details.", 
                wraplength=500
            ).pack(pady=10)
            
            ttk.Button(
                root, 
                text="Exit", 
                command=root.destroy
            ).pack(pady=20)
            
            root.mainloop()
        except:
            print("Failed to create error UI. Please check the console output.")
        
        return False

def main_cli():
    """Main function for CLI startup."""
    print("==== Financial Data Harmonizer UI ====")
    
    # Check if another instance is already running
    if is_already_running():
        print("Another instance is already running.")
        choice = input("Would you like to force start anyway? (y/n) ")
        
        if not choice.lower().startswith('y'):
            print("Launch cancelled. Please close the existing instance first.")
            return
    
    # Create lock file
    create_lock_file()
    
    try:
        print("\nChecking Streamlit availability...")
        streamlit_ok = check_streamlit_importable()
        
        if not streamlit_ok:
            print("Streamlit is not working correctly.")
            choice = input("Would you like to attempt to fix Streamlit? (y/n) ")
            
            if choice.lower().startswith('y'):
                streamlit_ok = fix_streamlit_installation()
                if streamlit_ok:
                    print("Streamlit fixed successfully!")
                else:
                    print("Failed to fix Streamlit. Falling back to Tkinter UI.")
            else:
                print("Skipping Streamlit fix.")
        
        if streamlit_ok:
            run_streamlit_ui()
        else:
            run_tkinter_ui()
    finally:
        # Always remove the lock file when exiting
        remove_lock_file()

# Streamlit UI Code 
def run_streamlit_app():
    """Main entry point for Streamlit app."""
    import streamlit as st
    
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
    page = st.sidebar.radio(
        "Navigation", 
        ["Home", "Process Files", "Provider Manager", "Settings"],
        index=["home", "process", "provider", "settings"].index(st.session_state.page) 
            if st.session_state.page in ["home", "process", "provider", "settings"] else 0
    )
    
    # Set the current page in session state
    st.session_state.page = page.lower().replace(" ", "")
    
    # Version info
    st.sidebar.divider()
    st.sidebar.caption("Version 0.1.0")
    
    # Display the selected page
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

# Main entry point
if __name__ == "__main__":
    if IN_STREAMLIT:
        # Running in Streamlit
        run_streamlit_app()
    else:
        # Running from command line - only start once
        main_cli()
