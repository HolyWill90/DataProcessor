"""
Financial Data Harmonizer - Command-line launcher

This script provides an easy way to launch the Financial Data Harmonizer
using either the preferred Streamlit interface or the fallback Tkinter interface.
"""
import os
import sys
import subprocess
from pathlib import Path
import platform
import time

def check_running_instance():
    """Check if another instance is already running."""
    # Different commands based on OS
    if platform.system() == "Windows":
        try:
            # Check if any streamlit processes are running
            result = subprocess.run("tasklist /FI \"IMAGENAME eq streamlit.exe\"", 
                                   shell=True, capture_output=True, text=True)
            return "streamlit.exe" in result.stdout
        except:
            return False
    else:
        try:
            # For MacOS/Linux
            result = subprocess.run("pgrep -f streamlit", 
                                   shell=True, capture_output=True, text=True)
            return bool(result.stdout.strip())
        except:
            return False

def main():
    """Main launcher function."""
    script_dir = Path(__file__).parent
    main_script = script_dir / "main_ui.py"
    
    # Only set the environment flag if it's not already set
    if not os.environ.get('FH_LAUNCHER_STARTED'):
        os.environ['FH_LAUNCHER_STARTED'] = 'true'
    
    print("===============================================")
    print("   Financial Data Harmonizer - Launcher")
    print("===============================================")
    
    # Check if another instance might be running
    if check_running_instance():
        print("\nWARNING: Another instance of Financial Harmonizer appears to be running.")
        choice = input("Proceed anyway? (y/n) ").lower().strip()
        
        if not choice.startswith('y'):
            print("\nLaunch cancelled. Please close any running instances first.")
            return
    
    print("\nAttempting to launch the application...")
    
    try:
        # Run the main UI script
        subprocess.run([sys.executable, str(main_script)])
    except Exception as e:
        print(f"\nError launching application: {e}")
        print("\nWould you like to try the fallback UI? (y/n)")
        choice = input("> ").lower().strip()
        
        if choice.startswith('y'):
            try:
                # Try to find the fallback UI script
                fallback_script = script_dir / "simple_ui_fixed.py"
                if fallback_script.exists():
                    print("\nLaunching fallback UI...")
                    subprocess.run([sys.executable, str(fallback_script)])
                else:
                    print("\nFallback UI script not found.")
            except Exception as fallback_error:
                print(f"\nError launching fallback UI: {fallback_error}")
                print("\nPlease check that Python is installed correctly and that all requirements are met.")
    
    print("\nApplication session ended.")

if __name__ == "__main__":
    main()
