"""
Setup and run the Financial Data Harmonizer UI
This script installs required dependencies and launches the Streamlit UI
"""
import os
import sys
import subprocess
from pathlib import Path

def check_package_installed(package_name):
    """Check if a Python package is installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def install_streamlit_requirements():
    """Install Streamlit and other UI requirements."""
    print("Setting up Financial Data Harmonizer UI...")
    
    # Check if streamlit is installed
    if check_package_installed('streamlit'):
        print("✓ Streamlit is already installed")
    else:
        print("Installing Streamlit and dependencies...")
        # Get the path to this script
        current_dir = Path(__file__).parent
        requirements_path = current_dir / "ui_requirements.txt"
        
        if requirements_path.exists():
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_path)
            ])
            print("✓ Successfully installed Streamlit and dependencies")
        else:
            # If requirements file doesn't exist, install minimal requirements
            print("Requirements file not found, installing minimal requirements...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "streamlit", "pandas", "openpyxl"
            ])
            print("✓ Installed minimal requirements")

def run_streamlit():
    """Launch the Streamlit UI."""
    print("\nLaunching Financial Data Harmonizer UI...")
    
    # Get path to Streamlit script
    current_dir = Path(__file__).parent
    ui_script = current_dir / "ui_streamlit.py"
    
    if ui_script.exists():
        # Run Streamlit in a subprocess to avoid blocking
        streamlit_module = subprocess.check_output([sys.executable, "-m", "pip", "show", "streamlit"]).decode()
        streamlit_location = None
        for line in streamlit_module.split('\n'):
            if line.startswith('Location:'):
                streamlit_location = line.split('Location: ')[1].strip()
                break
        
        if streamlit_location:
            streamlit_exe = os.path.join(streamlit_location, "streamlit", "__main__.py")
            if os.path.exists(streamlit_exe):
                cmd = [sys.executable, streamlit_exe, "run", str(ui_script)]
            else:
                cmd = [sys.executable, "-m", "streamlit", "run", str(ui_script)]
        else:
            cmd = [sys.executable, "-m", "streamlit", "run", str(ui_script)]
            
        # Print the command being run
        print(f"Running command: {' '.join(cmd)}")
        
        # Execute the command
        try:
            process = subprocess.Popen(cmd)
            print("\nIf a browser window doesn't open automatically,")
            print("go to the URL displayed in the command output (typically http://localhost:8501)")
            # Wait for the process to finish or user to interrupt
            process.wait()
        except KeyboardInterrupt:
            print("\nShutting down UI...")
            process.terminate()
    else:
        print(f"Error: UI script not found at {ui_script}")
        return False
    
    return True

def main():
    """Main function."""
    print("==== Financial Data Harmonizer UI Launcher ====")
    
    try:
        # Install requirements
        install_streamlit_requirements()
        
        # Run Streamlit
        success = run_streamlit()
        
        if not success:
            print("\nFailed to launch UI. You can try running it manually with:")
            print("streamlit run financial_harmonizer/ui_streamlit.py")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure you have Python 3.7+ installed")
        print("2. Try installing Streamlit manually: pip install streamlit")
        print("3. Run the UI manually: streamlit run financial_harmonizer/ui_streamlit.py")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
