"""
Tkinter UI entry point for Financial Data Harmonizer
"""
import os
import sys
from pathlib import Path
from ui_tkinter.app import FinancialHarmonizerTkApp

def main():
    """Main entry point for Tkinter UI."""
    print("Starting Financial Data Harmonizer (Tkinter UI)...")
    
    # Add the project root to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    try:
        # Create and run the Tkinter application
        app = FinancialHarmonizerTkApp()
        app.run()
    except Exception as e:
        print(f"Error launching Tkinter UI: {e}")
        import traceback
        traceback.print_exc()
        print("\nPress Enter to exit...")
        input()
        sys.exit(1)

if __name__ == "__main__":
    main()