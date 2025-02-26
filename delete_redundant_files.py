"""
UI Cleanup Utility for Financial Harmonizer

This script identifies and optionally removes redundant UI files
while preserving the essential UI components.
"""
import os
import sys
import shutil
from pathlib import Path
import logging
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ui_cleanup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent

def identify_redundant_files():
    """Identify redundant UI files that can be removed."""
    project_root = get_project_root()
    
    # Define core and redundant UI files
    core_ui_files = {
        # Main application entry points
        project_root / "launcher.py": "Main unified entry point",
        project_root / "streamlit_app.py": "Streamlit UI entry point",
        project_root / "tkinter_app.py": "Tkinter UI entry point",
        
        # UI component directories
        project_root / "ui" / "__init__.py": "Streamlit UI components initializer",
        project_root / "ui" / "home.py": "Home page UI",
        project_root / "ui" / "file_processor.py": "File processing UI",
        project_root / "ui" / "provider_manager.py": "Provider management UI",
        project_root / "ui" / "settings.py": "Settings UI",
        project_root / "ui_tkinter" / "__init__.py": "Tkinter UI components initializer",
        project_root / "ui_tkinter" / "app.py": "Tkinter application implementation"
    }
    
    redundant_ui_files = {
        # Redundant entry points and specialized files
        project_root / "simple_ui.py": "Outdated simple UI",
        project_root / "simple_ui_fixed.py": "Generated fallback UI",
        project_root / "ui_streamlit.py": "Old Streamlit entry point"
    }
    
    # Files that need review before deletion
    specialized_files = {
        project_root / "fix_ui.py": "UI repair tool with fallback functionality",
        project_root / "provider_ui.py": "Standalone provider management UI",
        project_root / "run_ui.py": "Streamlit installer and launcher"
    }
    
    # Verify existence of core files
    missing_core_files = []
    for file_path in core_ui_files:
        if not file_path.exists():
            missing_core_files.append(file_path)
    
    # Check for redundant files
    existing_redundant_files = []
    for file_path in redundant_ui_files:
        if file_path.exists():
            existing_redundant_files.append(file_path)
    
    # Check specialized files
    existing_specialized_files = []
    for file_path in specialized_files:
        if file_path.exists():
            existing_specialized_files.append(file_path)
    
    return {
        "core_files": {str(k): v for k, v in core_ui_files.items()},
        "missing_core_files": [str(f) for f in missing_core_files],
        "redundant_files": {str(k): v for k, v in redundant_ui_files.items() if k in existing_redundant_files},
        "specialized_files": {str(k): v for k, v in specialized_files.items() if k in existing_specialized_files}
    }

def delete_files(files_to_delete, backup=True):
    """Delete the specified files with optional backup."""
    results = {"success": [], "failed": []}
    backup_dir = Path("./ui_backup")
    
    if backup and files_to_delete:
        os.makedirs(backup_dir, exist_ok=True)
        logger.info(f"Creating backup directory: {backup_dir}")
    
    for file_path in files_to_delete:
        path = Path(file_path)
        try:
            if backup:
                # Create backup
                backup_path = backup_dir / path.name
                shutil.copy2(path, backup_path)
                logger.info(f"Backed up {path} to {backup_path}")
            
            # Delete the file
            os.remove(path)
            logger.info(f"Deleted {path}")
            results["success"].append(str(path))
        except Exception as e:
            logger.error(f"Failed to delete {path}: {e}")
            results["failed"].append(str(path))
    
    return results

def create_ui_guide():
    """Create a guide explaining the UI architecture."""
    project_root = get_project_root()
    guide_path = project_root / "UI_ARCHITECTURE.md"
    
    content = """# Financial Harmonizer UI Architecture

## Overview

The Financial Harmonizer application provides two user interface options:

1. **Streamlit UI (Primary)**: A modern web-based interface with rich interactive components
2. **Tkinter UI (Fallback)**: A traditional desktop UI available when Streamlit cannot run

## Entry Points

- **launcher.py**: The main entry point that intelligently selects and runs the appropriate UI
- **streamlit_app.py**: Direct entry point for the Streamlit UI
- **tkinter_app.py**: Direct entry point for the Tkinter UI

## Component Structure

### Streamlit UI Components

Located in the `ui/` directory:

- **home.py**: Home page with application overview
- **file_processor.py**: Interface for processing financial files
- **provider_manager.py**: Tools for managing data provider configurations
- **settings.py**: Application settings management

### Tkinter UI Components

Located in the `ui_tkinter/` directory:

- **app.py**: Complete Tkinter application implementation

## UI Preference

The application selects a UI based on the following criteria:

1. Environment variable `FH_UI_PREFERENCE` if set to 'streamlit' or 'tkinter'
2. If not specified, attempts to use Streamlit first
3. Falls back to Tkinter if Streamlit is unavailable

## Best Practices

- Use the unified launcher (`launcher.py`) for the most reliable experience
- Develop new features for the Streamlit UI first, then port to Tkinter if needed
- Test both UIs when making significant changes
"""
    
    with open(guide_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Created UI architecture guide: {guide_path}")
    return str(guide_path)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Clean up redundant UI files")
    parser.add_argument('--delete', action='store_true', help='Delete redundant files')
    parser.add_argument('--no-backup', dest='backup', action='store_false', 
                        help='Disable backup when deleting files')
    parser.add_argument('--create-guide', action='store_true', 
                        help='Create UI architecture guide')
    parser.set_defaults(backup=True)
    
    args = parser.parse_args()
    
    print("============================================================")
    print(" FINANCIAL HARMONIZER UI CLEANUP UTILITY")
    print("============================================================")
    print("")
    print("This utility helps identify redundant UI files that can be safely removed.")
    
    # Identify redundant files
    ui_files = identify_redundant_files()
    
    print("")
    print("============================================================")
    print(" REDUNDANT FILES (SAFE TO DELETE)")
    print("============================================================")
    
    if ui_files["redundant_files"]:
        for file_path, description in ui_files["redundant_files"].items():
            print(f"✗ {file_path} - {description}")
    else:
        print("No redundant files found!")
    
    print("")
    print("============================================================")
    print(" SPECIALIZED FILES (REVIEW BEFORE DELETION)")
    print("============================================================")
    
    if ui_files["specialized_files"]:
        for file_path, description in ui_files["specialized_files"].items():
            print(f"⚠️ {file_path} - May be specialized, review before deletion")
    else:
        print("No specialized files found!")
    
    print("")
    print("============================================================")
    print(" NEW UI STRUCTURE VERIFICATION")
    print("============================================================")
    
    if ui_files["missing_core_files"]:
        for file_path in ui_files["missing_core_files"]:
            print(f"✗ {file_path} - MISSING")
    
    for file_path in ui_files["core_files"]:
        if Path(file_path).exists():
            print(f"✓ {file_path} - Present")
        else:
            print(f"✗ {file_path} - MISSING")
    
    # Delete redundant files if requested
    if args.delete and ui_files["redundant_files"]:
        print("")
        print("Deleting redundant files...")
        results = delete_files(ui_files["redundant_files"], backup=args.backup)
        
        print(f"Successfully deleted {len(results['success'])} files.")
        if results["failed"]:
            print(f"Failed to delete {len(results['failed'])} files.")
            for file_path in results["failed"]:
                print(f"  - {file_path}")
    
    # Create architecture guide if requested
    if args.create_guide:
        guide_path = create_ui_guide()
        print(f"\nCreated UI architecture guide: {guide_path}")
    
    print("")
    print("============================================================")
    print(" SUMMARY")
    print("============================================================")
    
    print(f"Redundant files: {len(ui_files['redundant_files'])}")
    print(f"Specialized files: {len(ui_files['specialized_files'])}")
    print(f"Missing core files: {len(ui_files['missing_core_files'])}")
    
    if not args.delete and ui_files["redundant_files"]:
        print("\nTo delete redundant files, run:")
        print("python -m financial_harmonizer.delete_redundant_files --delete")
    
    if not args.create_guide:
        print("\nTo create a UI architecture guide, run:")
        print("python -m financial_harmonizer.delete_redundant_files --create-guide")

if __name__ == "__main__":
    main()