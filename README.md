# Financial Data Harmonizer

A flexible, modular system for processing, transforming, and harmonizing financial data from multiple providers.

## Overview

The Financial Data Harmonizer automates the process of extracting, transforming, and loading financial data from various formats and sources into a standardized structure. It's designed to replace complex, manual PowerQuery processes with a more maintainable Python-based solution.

## Key Features

- **Provider Configuration System**: Define data providers with synonyms, filters, calculations, and hardcoded fields
- **Intelligent File Processing**: Handle Excel and CSV files with automatic header detection
- **Smart Column Mapping**: Map columns via synonym matching
- **Transformation Pipeline**: Apply filters, calculations, and field extraction
- **SharePoint Integration**: Process files directly from SharePoint
- **Multiple UI Options**: Choose between Streamlit (web-based) or Tkinter (desktop) interfaces

## Installation

1. Ensure you have Python 3.7+ installed
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## Getting Started

### Using the Unified UI

The Financial Harmonizer now provides a single, unified entry point that automatically selects the best available UI framework:

```bash
python -m financial_harmonizer.run
```

#### UI Framework Options

- **Streamlit UI (Default)**: A modern web-based interface with rich interactive components
  ```bash
  python -m financial_harmonizer.run --ui streamlit
  ```

- **Tkinter UI (Fallback)**: A traditional desktop UI available when Streamlit cannot run
  ```bash
  python -m financial_harmonizer.run --ui tkinter
  ```

#### Additional Options

- **Debug Mode**: Run with additional logging
  ```bash
  python -m financial_harmonizer.run --debug
  ```

- **UI Fixer**: Launch the UI fixer tool to repair installation issues
  ```bash
  python -m financial_harmonizer.run --fix
  ```

### Using the Command Line

You can also use the Financial Harmonizer from the command line for batch processing:

```bash
python -m financial_harmonizer.cli process --file "path/to/file.xlsx" --provider "ProviderName"
```

## UI Architecture

For detailed information about the UI system, see:
- [UI Architecture Documentation](./UI_ARCHITECTURE.md)
- [UI Optimization Recommendations](./UI_OPTIMIZATION_RECOMMENDATIONS.md)
- [UI Fixes Applied](./UI_FIXES_APPLIED.md)

## Provider Configuration

The Financial Harmonizer uses JSON-based provider configurations to handle different data formats. See the `config/providers/` directory for examples.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
