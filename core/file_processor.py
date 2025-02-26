import pandas as pd
import numpy as np
import os
import csv
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import re

class FileProcessor:
    """Processes Excel and CSV files with intelligent header detection."""
    
    def __init__(self):
        self.log_entries = []
    
    def create_log_entry(self, step: str, source: str, detail: str, message: str) -> Dict[str, Any]:
        """Create a standardized log entry."""
        import datetime
        log_entry = {
            "Step": step,
            "Timestamp": datetime.datetime.utcnow().isoformat(),
            "Source": source,
            "ActionDetail": detail,
            "Message": message
        }
        self.log_entries.append(log_entry)
        return log_entry
    
    def safe_call(self, fn, step_name: str, source: str) -> Dict[str, Any]:
        """Safely execute a function and log the result."""
        try:
            result = fn()
            self.create_log_entry(step_name, source, "", "Success")
            return {"Result": result, "Log": self.log_entries[-1]}
        except Exception as e:
            self.create_log_entry(step_name, source, "", str(e))
            return {"Result": None, "Log": self.log_entries[-1]}
    
    def process_file(self, file_path: Union[str, Path], synonyms: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a file (Excel or CSV) and extract structured data.
        
        Args:
            file_path: Path to the file
            synonyms: List of synonym configurations for header matching
            
        Returns:
            Dictionary with:
                - PreHeaderText: Text extracted above headers
                - Data: Pandas DataFrame with the processed data
                - Log: Processing logs
        """
        if synonyms is None:
            synonyms = []
            
        # Extract file extension
        file_extension = os.path.splitext(str(file_path))[1].lower()
        
        # Get all alternate names for header matching
        alt_names_raw = []
        for syn in synonyms:
            if 'AlternateNames' in syn:
                alt_names_raw.extend(syn['AlternateNames'])
                
        # Filter out special synonym types
        filtered_alt_names = [
            x for x in alt_names_raw
            if not any(special in x.lower() for special in ["calculated", "regex", "concat", "hardcoded"]) 
            and x.strip()
        ]
        
        # Process based on file type
        if file_extension in ['.xlsx', '.xls']:
            result = self._process_excel(file_path, filtered_alt_names)
        elif file_extension == '.csv':
            result = self._process_csv(file_path, filtered_alt_names)
        else:
            self.create_log_entry("Process File", "FileProcessor", file_extension, "Unsupported file type")
            return {
                "PreHeaderText": "",
                "Data": pd.DataFrame(),
                "Log": self.log_entries
            }
            
        return result
        
    def _process_excel(self, file_path: Union[str, Path], alt_names: List[str]) -> Dict[str, Any]:
        """Process Excel files."""
        try:
            # Try to read all sheets
            excel_data = pd.read_excel(file_path, sheet_name=None, header=None)
            
            # Find sheets with data
            valid_sheets = {name: sheet for name, sheet in excel_data.items() if not sheet.empty}
            
            if not valid_sheets:
                self.create_log_entry("Process Excel", "FileProcessor", str(file_path), "No valid sheets found")
                return {"PreHeaderText": "", "Data": pd.DataFrame(), "Log": self.log_entries}
            
            # Try to find a sheet with matching headers
            chosen_sheet = None
            chosen_sheet_name = None
            
            if alt_names:
                for sheet_name, sheet in valid_sheets.items():
                    # Convert all cells to string for easier matching
                    str_sheet = sheet.astype(str)
                    
                    # Check if this sheet contains our expected headers
                    for alt_name in alt_names:
                        mask = str_sheet.apply(
                            lambda x: x.str.contains(alt_name, case=False, na=False)
                        ).any(axis=1)
                        
                        if mask.sum() >= 3:  # If we find at least 3 matches
                            chosen_sheet = sheet
                            chosen_sheet_name = sheet_name
                            break
                    
                    if chosen_sheet is not None:
                        break
            
            # If no sheet with headers found, use the first valid sheet
            if chosen_sheet is None:
                chosen_sheet_name = next(iter(valid_sheets))
                chosen_sheet = valid_sheets[chosen_sheet_name]
                
            # Find header row based on alternate names
            header_index = 0
            if alt_names:
                for idx, row in chosen_sheet.iterrows():
                    matches = sum(1 for val in row if isinstance(val, str) and any(
                        alt.lower() in val.lower() for alt in alt_names
                    ))
                    if matches >= 3:
                        header_index = idx
                        break
                        
            # Extract text above headers
            pre_header_text = ""
            if header_index > 0:
                rows_above_header = chosen_sheet.iloc[:header_index]
                pre_header_cells = rows_above_header.values.flatten()
                pre_header_text = " ".join(str(x) for x in pre_header_cells if pd.notna(x) and str(x).strip())
                
            # Extract data with proper headers
            data = chosen_sheet.iloc[header_index:].reset_index(drop=True)
            headers = data.iloc[0]
            data = data.iloc[1:].reset_index(drop=True)
            
            # Make header names unique
            unique_headers = []
            seen = set()
            for h in headers:
                h_str = str(h).strip()
                if h_str in seen:
                    count = 1
                    while f"{h_str}_{count}" in seen:
                        count += 1
                    h_str = f"{h_str}_{count}"
                seen.add(h_str)
                unique_headers.append(h_str)
                
            data.columns = unique_headers
            
            # Drop empty columns
            data = data.dropna(axis=1, how='all')
            
            self.create_log_entry("Process Excel", "FileProcessor", str(file_path), f"Successfully processed sheet '{chosen_sheet_name}'")
            return {"PreHeaderText": pre_header_text, "Data": data, "Log": self.log_entries}
            
        except Exception as e:
            self.create_log_entry("Process Excel", "FileProcessor", str(file_path), f"Error: {str(e)}")
            return {"PreHeaderText": "", "Data": pd.DataFrame(), "Log": self.log_entries}
    
    def _process_csv(self, file_path: Union[str, Path], alt_names: List[str]) -> Dict[str, Any]:
        """Process CSV files."""
        try:
            # First read without headers to analyze
            data = pd.read_csv(file_path, header=None)
            
            # Find header row based on alternate names
            header_index = 0
            if alt_names:
                for idx, row in data.iterrows():
                    matches = sum(1 for val in row if isinstance(val, str) and any(
                        alt.lower() in val.lower() for alt in alt_names
                    ))
                    if matches >= 3:
                        header_index = idx
                        break
            
            # Extract text above headers
            pre_header_text = ""
            if header_index > 0:
                rows_above_header = data.iloc[:header_index]
                pre_header_cells = rows_above_header.values.flatten()
                pre_header_text = " ".join(str(x) for x in pre_header_cells if pd.notna(x) and str(x).strip())
                
            # Re-read with proper header
            data = pd.read_csv(file_path, header=header_index)
            
            # Make header names unique
            columns = data.columns.tolist()
            unique_columns = []
            seen = set()
            for c in columns:
                c_str = str(c).strip()
                if c_str in seen:
                    count = 1
                    while f"{c_str}_{count}" in seen:
                        count += 1
                    c_str = f"{c_str}_{count}"
                seen.add(c_str)
                unique_columns.append(c_str)
                
            data.columns = unique_columns
            
            # Drop empty columns
            data = data.dropna(axis=1, how='all')
            
            self.create_log_entry("Process CSV", "FileProcessor", str(file_path), "Successfully processed CSV")
            return {"PreHeaderText": pre_header_text, "Data": data, "Log": self.log_entries}
            
        except Exception as e:
            self.create_log_entry("Process CSV", "FileProcessor", str(file_path), f"Error: {str(e)}")
            return {"PreHeaderText": "", "Data": pd.DataFrame(), "Log": self.log_entries}
