import pandas as pd
import numpy as np
import re
from typing import Dict, List, Any, Optional, Union, Callable
import datetime

class TransformPipeline:
    """Main pipeline for applying transformations to financial data."""
    
    def __init__(self):
        self.log_entries = []
    
    def create_log_entry(self, step: str, source: str, detail: str, message: str) -> Dict[str, Any]:
        """Create a standardized log entry."""
        log_entry = {
            "Step": step,
            "Timestamp": datetime.datetime.utcnow().isoformat(),
            "Source": source,
            "ActionDetail": detail,
            "Message": message
        }
        self.log_entries.append(log_entry)
        return log_entry
    
    def apply_synonyms(self, df: pd.DataFrame, synonyms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply column renaming based on synonyms.
        
        Args:
            df: Source DataFrame
            synonyms: List of synonym configurations
            
        Returns:
            Dict with ResultTable (DataFrame) and Log
        """
        if df.empty or not synonyms:
            self.create_log_entry("Apply Synonyms", "TransformPipeline", "No data or synonyms", "No changes made")
            return {"ResultTable": df, "Log": self.log_entries[-1]}
            
        # Build renaming map
        rename_mappings = {}
        source_columns = df.columns.tolist()
        source_columns_upper = [col.upper() for col in source_columns]
        
        for syn in synonyms:
            logical_field = syn.get("LogicalField", "")
            alt_names = syn.get("AlternateNames", [])
            
            for alt_name in alt_names:
                alt_name = alt_name.strip()
                alt_name_upper = alt_name.upper()
                
                # Check if this alternate name exists in the DataFrame
                for idx, col in enumerate(source_columns_upper):
                    if alt_name_upper == col:
                        rename_mappings[source_columns[idx]] = logical_field
                        break
        
        # Apply renaming
        if rename_mappings:
            try:
                df = df.rename(columns=rename_mappings)
                renamed_cols = list(rename_mappings.values())
                self.create_log_entry(
                    "Apply Synonyms", 
                    "TransformPipeline", 
                    f"Renamed columns: {', '.join(rename_mappings.keys())} to {', '.join(renamed_cols)}", 
                    "Success"
                )
            except Exception as e:
                self.create_log_entry("Apply Synonyms", "TransformPipeline", "Error renaming columns", str(e))
        else:
            self.create_log_entry("Apply Synonyms", "TransformPipeline", "No matching columns found", "No changes made")
            
        return {"ResultTable": df, "Log": self.log_entries[-1:]}
    
    def apply_filters(self, df: pd.DataFrame, filter_settings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply row filtering based on filter conditions.
        
        Args:
            df: Source DataFrame
            filter_settings: List of filter conditions
            
        Returns:
            Dict with ResultTable (DataFrame) and Log
        """
        if df.empty or not filter_settings:
            self.create_log_entry("Apply Filters", "TransformPipeline", "No data or filters", "No changes made")
            return {"ResultTable": df, "Log": self.log_entries[-1:]}
        
        # Normalize column names to lowercase
        df.columns = df.columns.str.lower()
        
        original_row_count = len(df)
        filter_logs = []
        
        for filter_condition in filter_settings:
            # Extract column name from [column] format
            condition = filter_condition.strip()
            col_match = re.search(r'\[(.*?)\]', condition)
            
            if not col_match:
                filter_logs.append({
                    "Filter": condition,
                    "Status": "Invalid filter format - missing [column]",
                    "RowsRemoved": 0
                })
                continue
                
            col_name = col_match.group(1).lower()
            
            if col_name not in df.columns:
                filter_logs.append({
                    "Filter": condition,
                    "Status": f"Column '{col_name}' not found",
                    "RowsRemoved": 0
                })
                continue
                
            # Extract operator and value
            ops = ['<>', '>=', '<=', '=', '>', '<']
            op = None
            value = None
            
            for possible_op in ops:
                if possible_op in condition:
                    parts = condition.split(possible_op, 1)
                    if len(parts) == 2:
                        op = possible_op
                        value = parts[1].strip()
                        break
            
            if op is None or value is None:
                filter_logs.append({
                    "Filter": condition,
                    "Status": "Invalid filter format - missing operator or value",
                    "RowsRemoved": 0
                })
                continue
                
            # Apply filter
            before_count = len(df)
            
            try:
                # Handle null checks
                if value.lower() in ('null', 'blank()', '""', "''"):
                    if op == '=':
                        df = df[df[col_name].isna() | (df[col_name] == '')]
                    elif op == '<>':
                        df = df[df[col_name].notna() & (df[col_name] != '')]
                # Handle numeric comparisons
                elif value.replace('.', '').replace('-', '').isdigit():
                    num_val = float(value)
                    if op == '=':
                        df = df[pd.to_numeric(df[col_name], errors='coerce') == num_val]
                    elif op == '<>':
                        df = df[pd.to_numeric(df[col_name], errors='coerce') != num_val]
                    elif op == '<':
                        df = df[pd.to_numeric(df[col_name], errors='coerce') < num_val]
                    elif op == '>':
                        df = df[pd.to_numeric(df[col_name], errors='coerce') > num_val]
                    elif op == '<=':
                        df = df[pd.to_numeric(df[col_name], errors='coerce') <= num_val]
                    elif op == '>=':
                        df = df[pd.to_numeric(df[col_name], errors='coerce') >= num_val]
                # Handle text comparisons
                else:
                    text_val = value.strip('"\'')
                    if op == '=':
                        df = df[df[col_name].astype(str).str.lower() == text_val.lower()]
                    elif op == '<>':
                        df = df[df[col_name].astype(str).str.lower() != text_val.lower()]
                
                after_count = len(df)
                rows_removed = before_count - after_count
                
                filter_logs.append({
                    "Filter": condition,
                    "Status": "Applied",
                    "RowsRemoved": rows_removed
                })
                
            except Exception as e:
                filter_logs.append({
                    "Filter": condition,
                    "Status": f"Error: {str(e)}",
                    "RowsRemoved": 0
                })
        
        # Add filter logs to main log
        for filter_log in filter_logs:
            self.create_log_entry(
                "Apply Filters", 
                "TransformPipeline", 
                f"Filter: {filter_log['Filter']}; Rows removed: {filter_log['RowsRemoved']}", 
                filter_log['Status']
            )
            
        final_row_count = len(df)
        total_rows_removed = original_row_count - final_row_count
        
        self.create_log_entry(
            "Apply Filters Summary", 
            "TransformPipeline", 
            f"Original rows: {original_row_count}; Final rows: {final_row_count}; Total removed: {total_rows_removed}", 
            "Completed"
        )
            
        return {"ResultTable": df, "Log": self.log_entries[-len(filter_logs)-1:]}
    
    def apply_calculations(self, df: pd.DataFrame, calculations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply calculations to create new columns.
        
        Args:
            df: Source DataFrame
            calculations: List of calculation definitions
            
        Returns:
            Dict with ResultTable (DataFrame) and Log
        """
        if df.empty or not calculations:
            self.create_log_entry("Apply Calculations", "TransformPipeline", "No data or calculations", "No changes made")
            return {"ResultTable": df, "Log": self.log_entries[-1:]}
            
        # Convert column names to lowercase for consistency
        df.columns = df.columns.str.lower()
        
        for calc in calculations:
            new_field = calc.get("NewField", "").lower()
            expression = calc.get("Expression", "")
            
            if not new_field or not expression:
                self.create_log_entry(
                    "Apply Calculations", 
                    "TransformPipeline", 
                    f"Invalid calculation: {new_field} = {expression}", 
                    "Missing field name or expression"
                )
                continue
                
            try:
                # Replace column references with actual values
                def calculate_for_row(row):
                    processed_expr = expression
                    
                    # Replace column references with values
                    for col in df.columns:
                        placeholder = f"[{col}]"
                        if placeholder in processed_expr:
                            value = row[col]
                            
                            # Handle nulls and empty strings
                            if pd.isna(value) or value == '':
                                if '&' in processed_expr:  # String concatenation
                                    processed_expr = processed_expr.replace(placeholder, '""')
                                else:  # Numeric operation
                                    processed_expr = processed_expr.replace(placeholder, '0')
                            elif isinstance(value, str):
                                if '&' in processed_expr:  # String concatenation
                                    processed_expr = processed_expr.replace(placeholder, f'"{value}"')
                                else:  # Try to convert to number if possible
                                    try:
                                        num_val = float(value)
                                        processed_expr = processed_expr.replace(placeholder, str(num_val))
                                    except:
                                        processed_expr = processed_expr.replace(placeholder, '0')
                            else:  # Numeric value
                                processed_expr = processed_expr.replace(placeholder, str(value))
                
                    # Evaluate the expression
                    try:
                        # Handle string concatenation with &
                        if '&' in processed_expr:
                            processed_expr = processed_expr.replace('&', '+')
                            # Make sure string literals are properly quoted
                            processed_expr = re.sub(r'([^"\'+-/*\s()]+)', r'"\1"', processed_expr)
                        
                        result = eval(processed_expr)
                        return result
                    except:
                        return None
                
                # Add the calculated column
                df[new_field] = df.apply(calculate_for_row, axis=1)
                
                # Convert to proper type
                is_text_operation = '&' in expression
                if is_text_operation:
                    df[new_field] = df[new_field].astype(str)
                else:
                    # Replace deprecated errors='ignore' with try-except approach
                    try:
                        df[new_field] = pd.to_numeric(df[new_field])
                    except Exception:
                        # If conversion fails, keep as is
                        pass
                    
                self.create_log_entry(
                    "Apply Calculations", 
                    "TransformPipeline", 
                    f"Added column: {new_field} = {expression}", 
                    "Success"
                )
                
            except Exception as e:
                self.create_log_entry(
                    "Apply Calculations", 
                    "TransformPipeline", 
                    f"Error adding column {new_field} = {expression}", 
                    str(e)
                )
                
        return {"ResultTable": df, "Log": self.log_entries[-len(calculations):]}
    
    def apply_hardcoded_fields(self, df: pd.DataFrame, hardcoded_fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add hardcoded field values to the DataFrame.
        
        Args:
            df: Source DataFrame
            hardcoded_fields: List of field definitions
            
        Returns:
            Dict with ResultTable (DataFrame) and Log
        """
        if df.empty or not hardcoded_fields:
            self.create_log_entry("Apply Hardcoded Fields", "TransformPipeline", "No data or fields", "No changes made")
            return {"ResultTable": df, "Log": self.log_entries[-1:]}
            
        for field in hardcoded_fields:
            field_name = field.get("FieldName", "")
            field_value = field.get("Value", "")
            
            if not field_name:
                self.create_log_entry(
                    "Apply Hardcoded Fields", 
                    "TransformPipeline", 
                    f"Invalid field definition", 
                    "Missing field name"
                )
                continue
                
            try:
                df[field_name] = field_value
                self.create_log_entry(
                    "Apply Hardcoded Fields", 
                    "TransformPipeline", 
                    f"Added field: {field_name} = {field_value}", 
                    "Success"
                )
            except Exception as e:
                self.create_log_entry(
                    "Apply Hardcoded Fields", 
                    "TransformPipeline", 
                    f"Error adding field {field_name}", 
                    str(e)
                )
                
        return {"ResultTable": df, "Log": self.log_entries[-len(hardcoded_fields):]}
        
    def extract_values_from_text(self, source_text: str, field_definitions: List[Dict[str, Any]], df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract structured data from text using field definitions.
        
        Args:
            source_text: Text to extract from
            field_definitions: List of extraction rules
            df: DataFrame to add extracted values to
            
        Returns:
            Dict with ResultTable (DataFrame) and Log
        """
        if not source_text or not field_definitions:
            self.create_log_entry("Extract Values", "TransformPipeline", "No source text or field definitions", "No changes made")
            return {"ResultTable": df, "Log": self.log_entries[-1:]}
            
        extracted_values = {}
        
        for field_def in field_definitions:
            field_name = field_def.get("FieldName", "")
            start_delim = field_def.get("StartDelim", "")
            end_delim = field_def.get("EndDelim", "")
            sub_start_delim = field_def.get("SubStartDelim", "")
            is_date_range = field_def.get("IsDateRange", False)
            return_part = field_def.get("ReturnPart", "")
            cleanup_steps = field_def.get("CleanupSteps", [])
            
            if not field_name:
                self.create_log_entry(
                    "Extract Values", 
                    "TransformPipeline", 
                    f"Missing field name in definition", 
                    "Skipping"
                )
                continue
            
            try:
                # Extract value between delimiters
                if start_delim:
                    if start_delim in source_text:
                        after_start = source_text.split(start_delim, 1)[1]
                    else:
                        after_start = source_text
                else:
                    after_start = source_text
                
                # Apply sub-delimiter if specified
                if sub_start_delim and sub_start_delim in after_start:
                    after_sub = after_start.split(sub_start_delim, 1)[1]
                else:
                    after_sub = after_start
                
                # Handle date ranges
                if is_date_range:
                    if " to " in after_sub:
                        full_range = after_sub.split(" to ", 1)
                        start_date = full_range[0].strip()
                        end_date = full_range[1].strip()
                        
                        if end_delim and end_date:
                            end_date = end_date.split(end_delim, 1)[0].strip()
                            
                        raw_value = start_date if return_part.lower() == "start" else end_date
                    else:
                        # If no range found, just extract until end delimiter
                        if end_delim and end_delim in after_sub:
                            raw_value = after_sub.split(end_delim, 1)[0].strip()
                        else:
                            raw_value = after_sub.strip()
                else:
                    # Standard extraction
                    if end_delim and end_delim in after_sub:
                        raw_value = after_sub.split(end_delim, 1)[0].strip()
                    else:
                        raw_value = after_sub.strip()
                
                # Apply cleanup steps
                cleaned_value = raw_value
                if cleanup_steps:
                    for step in cleanup_steps:
                        step_type = step.get("type", "")
                        delimiter = step.get("delimiter", " ")
                        part = step.get("part", 0)
                        mode = step.get("mode", "all")
                        
                        if step_type == "split":
                            # Split the value
                            if mode == "first":
                                # Split only at first occurrence
                                parts = cleaned_value.split(delimiter, 1)
                                if len(parts) > 1:
                                    left_part = parts[0].strip()
                                    right_part = parts[1].strip()
                                    cleaned_value = [left_part, right_part]
                            else:
                                # Split at all occurrences
                                cleaned_value = [p.strip() for p in cleaned_value.split(delimiter)]
                                
                        elif step_type == "pick":
                            # Pick specific part from list
                            if isinstance(cleaned_value, list):
                                part_idx = int(part) - 1  # Convert to 0-based index
                                if 0 <= part_idx < len(cleaned_value):
                                    cleaned_value = cleaned_value[part_idx]
                                else:
                                    cleaned_value = ""
                                
                        elif step_type == "trim":
                            # Trim whitespace
                            if isinstance(cleaned_value, list):
                                cleaned_value = [v.strip() for v in cleaned_value]
                            else:
                                cleaned_value = cleaned_value.strip()
                
                # Convert list to string if needed
                if isinstance(cleaned_value, list):
                    cleaned_value = cleaned_value[0] if cleaned_value else ""
                
                # Store the extracted value
                extracted_values[field_name] = cleaned_value
                
                self.create_log_entry(
                    "Extract Values", 
                    "TransformPipeline", 
                    f"Field: {field_name}; Value: {cleaned_value}", 
                    "Extracted"
                )
                
            except Exception as e:
                self.create_log_entry(
                    "Extract Values", 
                    "TransformPipeline", 
                    f"Error extracting field {field_name}", 
                    str(e)
                )
        
        # Add extracted values as columns to DataFrame
        for field_name, value in extracted_values.items():
            df[field_name] = value
            
        self.create_log_entry(
            "Extract Values Summary", 
            "TransformPipeline", 
            f"Added {len(extracted_values)} extracted fields to data", 
            "Completed"
        )
            
        return {"ResultTable": df, "Log": self.log_entries[-len(field_definitions)-1:]}