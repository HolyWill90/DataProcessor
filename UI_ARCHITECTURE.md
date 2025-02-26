# Financial Harmonizer UI Architecture

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
