#!/usr/bin/env python3
"""
Financial Harmonizer - Main Entry Point

This script provides a single entry point for running the Financial Harmonizer application,
using the UI wrapper to determine the best available UI framework.
"""
import os
import sys
import argparse
import traceback
from pathlib import Path
import logging

def setup_logging(debug=False):
    """Configure logging based on debug flag."""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("financial_harmonizer.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def add_to_path():
    """Add the project root to the Python path."""
    project_root = Path(__file__).parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    return project_root

def main():
    """Main entry point for the application."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run the Financial Harmonizer application")
    parser.add_argument('--ui', choices=['streamlit', 'tkinter'], 
                        help='Specify UI framework to use (streamlit or tkinter)')
    parser.add_argument('--debug', action='store_true', 
                        help='Run in debug mode with additional logging')
    parser.add_argument('--fix', action='store_true',
                        help='Run the UI fixer tool to repair installation issues')
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging(args.debug)
    
    # Set up environment based on arguments
    if args.ui:
        os.environ['FH_UI_PREFERENCE'] = args.ui
    
    if args.debug:
        os.environ['FH_DEBUG'] = 'true'
    
    print("="*50)
    print(" Financial Harmonizer".center(50))
    print("="*50)
    
    # Add project root to path
    project_root = add_to_path()
    
    # If fix flag is set, run the fix_ui script directly
    if args.fix:
        fix_ui_path = project_root / "fix_ui.py"
        if fix_ui_path.exists():
            print("\nRunning UI fixer tool...")
            try:
                sys.path.insert(0, str(project_root))
                import fix_ui
                fix_ui.main()
                return 0
            except Exception as e:
                print(f"\nError running fix_ui: {e}")
                logger.error(f"Error running fix_ui: {e}")
                logger.debug(traceback.format_exc())
                return 1
        else:
            print("\nError: UI fixer tool not found")
            return 1
    
    # Import and use the UI wrapper
    try:
        from ui_wrapper import get_ui
        ui = get_ui(framework=args.ui, debug=args.debug)
        
        print(f"\nUsing {ui.framework.capitalize()} UI framework")
        print("\nStarting application...\n")
        
        # Run the application
        result = ui.run()
        
        if not result:
            print("\nError: Failed to start the application")
            logger.error("Failed to start the application")
            
            # Try running the fix_ui script as a fallback
            fix_ui_path = project_root / "fix_ui.py"
            if fix_ui_path.exists():
                print("\nWould you like to try the UI fixer tool? (y/n)")
                choice = input("> ").lower().strip()
                
                if choice.startswith('y'):
                    print("\nRunning UI fixer tool...")
                    try:
                        sys.path.insert(0, str(project_root))
                        import fix_ui
                        fix_ui.main()
                    except Exception as e:
                        print(f"\nError running fix_ui: {e}")
                        logger.error(f"Error running fix_ui: {e}")
                        logger.debug(traceback.format_exc())
                        return 1
            
            return 1
            
    except ImportError as e:
        print(f"\nError: {e}")
        print("\nFailed to initialize UI. Please ensure all dependencies are installed:")
        print("  For Streamlit UI: pip install -r ui_requirements.txt")
        print("  For Tkinter UI: No additional requirements (uses standard library)")
        
        # Try running the fix_ui script as a fallback
        fix_ui_path = project_root / "fix_ui.py"
        if fix_ui_path.exists():
            print("\nWould you like to run the UI fixer tool? (y/n)")
            choice = input("> ").lower().strip()
            
            if choice.startswith('y'):
                print("\nRunning UI fixer tool...")
                try:
                    import fix_ui
                    fix_ui.main()
                except Exception as e:
                    print(f"\nError running fix_ui: {e}")
                    return 1
        
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        logger.debug(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())