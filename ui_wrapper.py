"""
UI Wrapper for Financial Harmonizer

This module provides a unified interface to both Streamlit and Tkinter UIs,
allowing for easier switching between UI frameworks and consistent access patterns.
"""
import os
import sys
import importlib
from pathlib import Path
import logging
import traceback

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UIWrapper:
    """Base UI wrapper class that defines the common interface."""
    
    def __init__(self, framework=None, debug=False):
        """Initialize the UI wrapper.
        
        Args:
            framework (str, optional): UI framework to use ('streamlit' or 'tkinter').
                If None, will try to detect based on environment variables and available modules.
            debug (bool, optional): Whether to enable debug logging.
        """
        # Configure logging based on debug flag
        if debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled")
            
        self.debug = debug
        self.framework = framework or self._detect_framework()
        self.root_dir = Path(__file__).parent
        
        # Make sure project root is in Python path
        self._add_to_path()
        
        # Try to import utils
        try:
            from utils import add_to_python_path, get_project_root
            self.project_root = get_project_root()
            add_to_python_path()
        except ImportError:
            logger.warning("Could not import utility functions")
            self.project_root = self.root_dir
        
        # Initialize the appropriate UI framework
        self._initialize_framework()
    
    def _add_to_path(self):
        """Add the project root to the Python path."""
        project_root = str(self.root_dir)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            logger.info(f"Added {project_root} to Python path")
        return True
    
    def _detect_framework(self):
        """Detect which UI framework to use based on environment and available modules."""
        # Check environment variables first
        env_preference = os.environ.get('FH_UI_PREFERENCE', '').lower()
        if env_preference in ['streamlit', 'tkinter']:
            logger.info(f"Using environment-specified UI framework: {env_preference}")
            return env_preference
        
        # Check if streamlit is available
        try:
            importlib.import_module('streamlit')
            logger.info("Detected Streamlit as available framework")
            return 'streamlit'
        except ImportError:
            logger.info("Streamlit not available, using Tkinter")
            return 'tkinter'
    
    def _initialize_framework(self):
        """Initialize the selected UI framework."""
        if self.framework == 'streamlit':
            try:
                self.module = importlib.import_module('financial_harmonizer.streamlit_app')
                logger.info("Initialized Streamlit UI framework")
            except ImportError as e:
                logger.error(f"Failed to initialize Streamlit UI: {e}")
                logger.debug(traceback.format_exc())
                # Fall back to Tkinter
                self.framework = 'tkinter'
                self._initialize_framework()
        else:  # tkinter
            try:
                self.module = importlib.import_module('financial_harmonizer.ui_tkinter.app')
                logger.info("Initialized Tkinter UI framework")
            except ImportError as e:
                logger.error(f"Failed to initialize Tkinter UI: {e}")
                logger.debug(traceback.format_exc())
                raise ImportError("No UI framework available") from e
    
    def _check_resources(self):
        """Check if necessary resources exist and are valid."""
        required_resources = {
            'streamlit': ['streamlit_app.py', 'ui/__init__.py'],
            'tkinter': ['ui_tkinter/app.py', 'ui_tkinter/__init__.py']
        }
        
        missing = []
        for resource in required_resources[self.framework]:
            if not (self.root_dir / resource).exists():
                missing.append(resource)
        
        if missing:
            logger.warning(f"Missing resources for {self.framework}: {', '.join(missing)}")
            return False
        
        return True
    
    def run(self):
        """Run the UI application."""
        # Perform resource check before launching
        if not self._check_resources():
            logger.warning("Some resources are missing, UI may not function correctly")
        
        if self.framework == 'streamlit':
            # Streamlit has a different launch mechanism
            import subprocess
            streamlit_app = self.root_dir / "streamlit_app.py"
            logger.info(f"Launching Streamlit app: {streamlit_app}")
            
            try:
                cmd = [
                    sys.executable, 
                    "-m", 
                    "streamlit", 
                    "run", 
                    str(streamlit_app),
                ]
                
                # Add debug flag if needed
                if self.debug:
                    cmd.append("--logger.level=debug")
                
                subprocess.run(cmd)
            except Exception as e:
                logger.error(f"Failed to launch Streamlit: {e}")
                logger.debug(traceback.format_exc())
                
                # If we failed to launch streamlit, try the backup method with fix_ui
                fix_ui_path = self.root_dir / "fix_ui.py"
                if fix_ui_path.exists():
                    logger.info("Trying fix_ui.py as fallback")
                    try:
                        subprocess.run([sys.executable, str(fix_ui_path)])
                    except Exception as fallback_e:
                        logger.error(f"Failed to run fix_ui.py: {fallback_e}")
                        return False
                else:
                    return False
        else:
            # For Tkinter, create and run the app
            try:
                from financial_harmonizer.ui_tkinter.app import FinancialHarmonizerTkApp
                app = FinancialHarmonizerTkApp()
                app.run()
            except Exception as e:
                logger.error(f"Failed to launch Tkinter app: {e}")
                logger.debug(traceback.format_exc())
                
                # If we failed to launch the tkinter app, see if we have a fallback
                simple_ui_path = self.root_dir / "simple_ui_fixed.py"
                if simple_ui_path.exists():
                    logger.info("Trying simple_ui_fixed.py as fallback")
                    try:
                        subprocess.run([sys.executable, str(simple_ui_path)])
                    except Exception as fallback_e:
                        logger.error(f"Failed to run simple_ui_fixed.py: {fallback_e}")
                        return False
                else:
                    return False
        
        return True
    
    def get_component(self, component_name):
        """Get a UI component by name.
        
        Args:
            component_name (str): Component name like 'home', 'file_processor', etc.
            
        Returns:
            module: The component module
        """
        try:
            if self.framework == 'streamlit':
                return importlib.import_module(f'financial_harmonizer.ui.{component_name}')
            else:
                # For Tkinter, most components are in the main app
                return self.module
        except ImportError as e:
            logger.error(f"Failed to load component {component_name}: {e}")
            return None


def get_ui(framework=None, debug=False):
    """Factory function to get a UI wrapper instance.
    
    Args:
        framework (str, optional): UI framework to use ('streamlit' or 'tkinter').
            If None, will try to detect based on environment variables and available modules.
        debug (bool, optional): Whether to enable debug logging.
            
    Returns:
        UIWrapper: An initialized UI wrapper instance
    """
    if debug:
        os.environ['FH_DEBUG'] = 'true'
        
    return UIWrapper(framework=framework, debug=debug)


if __name__ == "__main__":
    # If run directly, simply launch the default UI
    debug_mode = '--debug' in sys.argv
    
    ui = get_ui(debug=debug_mode)
    print(f"Launching Financial Harmonizer with {ui.framework} UI...")
    ui.run()