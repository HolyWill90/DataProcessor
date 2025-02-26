"""
Utility functions for Financial Harmonizer
"""
import os
import sys
import pandas as pd
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_file_with_encoding_fallback(file_path, file_obj=None):
    """
    Load a file with multiple encoding fallbacks.
    
    Args:
        file_path (str): Path to the file or file name
        file_obj (file-like, optional): Open file object (for streamlit uploads)
        
    Returns:
        pandas.DataFrame: The loaded data
    """
    # Determine file type
    path = Path(file_path)
    file_type = path.suffix.lower()
    
    # For Excel files, encoding doesn't matter
    if file_type in ['.xlsx', '.xls']:
        try:
            if file_obj is not None:
                return pd.read_excel(file_obj)
            else:
                return pd.read_excel(file_path)
        except Exception as e:
            logger.error(f"Error reading Excel file {file_path}: {e}")
            raise
    
    # For CSV, try different encodings
    encodings = ['utf-8', 'latin-1', 'cp1252', 'ISO-8859-1']
    
    for encoding in encodings:
        try:
            if file_obj is not None:
                if hasattr(file_obj, 'seek'):
                    file_obj.seek(0)  # Reset file pointer
                return pd.read_csv(file_obj, encoding=encoding)
            else:
                return pd.read_csv(file_path, encoding=encoding)
        except UnicodeDecodeError:
            continue
        except Exception as e:
            if 'unicode' not in str(e).lower():
                # If it's not an encoding error, no need to try other encodings
                logger.error(f"Error reading CSV file {file_path}: {e}")
                raise
    
    # If all encodings fail
    error_msg = f"Could not decode file {file_path} with any of the encodings: {encodings}"
    logger.error(error_msg)
    raise ValueError(error_msg)

def ensure_directory(directory_path):
    """
    Ensure a directory exists.
    
    Args:
        directory_path (str): Path to the directory
        
    Returns:
        Path: The directory path
    """
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent

def add_to_python_path():
    """Add the project root to the Python path."""
    project_root = str(get_project_root())
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        logger.info(f"Added {project_root} to Python path")
    return True

def make_dataframe_arrow_compatible(df):
    """
    Make a DataFrame compatible with Arrow for Streamlit display.
    
    Args:
        df (pandas.DataFrame): The DataFrame to convert
        
    Returns:
        pandas.DataFrame: An Arrow-compatible DataFrame
    """
    if df is None or df.empty:
        return df
        
    # Create a copy to avoid modifying the original
    result = df.copy()
    
    # Function to safely convert a column
    def safe_convert(col):
        try:
            # Try to infer better types for string columns that might be numeric
            if pd.api.types.is_object_dtype(col):
                try:
                    # Try to convert to numeric, but keep as original if it fails
                    return pd.to_numeric(col, errors='raise')
                except:
                    # Convert column to string to ensure Arrow compatibility
                    return col.astype(str)
            return col
        except Exception:
            # If all else fails, convert to string
            return col.astype(str)
    
    # Apply conversion to each column
    for col_name in result.columns:
        result[col_name] = safe_convert(result[col_name])
    
    return result