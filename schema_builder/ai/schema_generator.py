"""
AI-powered schema generator for provider configurations.

This module handles the generation of provider schemas from anonymized sample data,
leveraging AI to create optimized transformations without exposing sensitive information.
"""
import pandas as pd
import json
import os
import sys
import requests
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

# Import anonymizer
from schema_builder.anonymizer.data_anonymizer import DataAnonymizer


class AISchemaGenerator:
    """
    Uses AI to generate provider schemas from anonymized sample data.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the schema generator.
        
        Args:
            api_key: Optional API key for external AI services
        """
        self.api_key = api_key or os.environ.get('CLAUDE_API_KEY')
        self.anonymizer = DataAnonymizer()
        
    def generate_schema_from_file(self, file_path: str, provider_name: str, skip_anonymization: bool = False) -> Dict[str, Any]:
        """
        Generate a provider schema directly from a file using the core FileProcessor.
        
        Args:
            file_path: Path to the file to process
            provider_name: Name for the provider
            skip_anonymization: If True, use the provided data without anonymizing it
            
        Returns:
            Complete provider schema as a dictionary
        """
        # Import FileProcessor here to avoid circular imports
        from core.file_processor import FileProcessor
        
        # Process the file using the improved FileProcessor with header detection
        file_processor = FileProcessor()
        result = file_processor.process_file(file_path)
        
        # Extract DataFrame and header text
        df = result.get('Data', pd.DataFrame())
        header_text = result.get('PreHeaderText', '')
        
        # Log the detected header text
        print(f"File processing detected header text: {len(header_text)} characters")
        
        # Use the manual schema generation directly for consistent header extraction
        # This ensures we always get the proper HeaderExtraction rules
        if header_text:
            manual_schema = self._generate_manual_schema(df, header_text, provider_name)
            # Keep the header extraction rules for later
            header_extraction_rules = manual_schema.get("HeaderExtraction", [])
            
            # Call the main schema generation method
            schema = self.generate_schema(df, provider_name, header_text, skip_anonymization)
            
            # Ensure the HeaderExtraction field exists and contains our rules
            if "HeaderExtraction" not in schema:
                schema["HeaderExtraction"] = []
                
            # Add the header extraction rules from manual generation if they don't exist
            if not schema["HeaderExtraction"]:
                schema["HeaderExtraction"] = header_extraction_rules
                
            return schema
        else:
            # No header text, just use the standard generation
            return self.generate_schema(df, provider_name, header_text, skip_anonymization)
    
    def generate_schema(self, df: pd.DataFrame, provider_name: str, header_text: str = "", skip_anonymization: bool = False) -> Dict[str, Any]:
        """
        Generate a provider schema based on a sample DataFrame.
        
        Args:
            df: Sample DataFrame
            provider_name: Name for the provider
            header_text: Optional header text from the file
            skip_anonymization: If True, use the provided data without anonymizing it
            
        Returns:
            Complete provider schema as a dictionary
        """
        # Clean the DataFrame to avoid NaT serialization errors
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Replace NaT values with None in datetime columns
        for col in df.select_dtypes(include=['datetime64']).columns:
            df[col] = df[col].astype(object).where(~pd.isna(df[col]), None)
        # First, ensure we're working with a properly structured DataFrame
        df = self._ensure_proper_dataframe_structure(df)
        
        if skip_anonymization:
            # Use the data as-is without anonymization
            processed_df = df
            processed_header = header_text
        else:
            # Anonymize the data
            processed_df = self.anonymizer.anonymize_dataframe(df)
            processed_header = self.anonymizer.anonymize_header_text(header_text)
        
        # Prepare data sample for AI
        data_sample = self._prepare_data_sample(processed_df, processed_header)
        
        # Generate schema using AI
        schema = self._generate_schema_with_ai(data_sample, provider_name)
        
        # As a fallback, if the AI-generated schema is problematic (indicated by empty result after validation),
        # then generate a manual schema based on column analysis
        if not schema:
            print("Using fallback manual schema generation based on column analysis")
            schema = self._generate_manual_schema(processed_df, header_text, provider_name)
        
        return schema
        
    def _ensure_proper_dataframe_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure that the DataFrame has proper structure with correctly identified headers.
        
        Args:
            df: The DataFrame to check and fix
            
        Returns:
            A properly structured DataFrame
        """
        # Check if the DataFrame has many unnamed columns, which indicates header detection issues
        unnamed_cols = [col for col in df.columns if isinstance(col, str) and col.startswith('Unnamed:')]
        
        # If more than 30% of columns are unnamed, we likely have a header detection issue
        if len(unnamed_cols) > len(df.columns) * 0.3:
            print(f"WARNING: {len(unnamed_cols)} of {len(df.columns)} columns are unnamed.")
            print("This indicates a possible header detection issue. Attempting to fix.")
            
            # Return a fixed version of the dataframe using our manual header detection
            return self._fix_dataframe_headers(df)
        
        # If columns are directly from the header text (e.g. "From (Recipient):")
        header_text_cols = [col for col in df.columns if isinstance(col, str) and 
                           any(term in col.lower() for term in ['recipient', 'supplier', 'abn', 'period'])]
        
        if header_text_cols and len(header_text_cols) > len(df.columns) * 0.2:
            print(f"WARNING: {len(header_text_cols)} columns appear to be from header text.")
            print("This indicates that header rows were incorrectly used as column names.")
            
            # Return a fixed version of the dataframe
            return self._fix_dataframe_headers(df)
            
        # Check if we have standard financial columns
        financial_cols = [col for col in df.columns if isinstance(col, str) and 
                         any(term in col.lower() for term in 
                            ['amount', 'premium', 'gst', 'total', 'policy', 'rep', 'comm'])]
        
        # If we don't have any financial columns, this might not be the right structure
        if not financial_cols and len(df.columns) > 5:
            print("WARNING: No standard financial columns detected.")
            print("This might indicate that the wrong header row was identified.")
            
            # Try to fix the dataframe structure
            return self._fix_dataframe_headers(df)
            
        # If we get here, the DataFrame structure seems reasonable
        return df
        
    def _fix_dataframe_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Attempt to fix a DataFrame with header detection issues by identifying the correct header row.
        
        Args:
            df: The problematic DataFrame
            
        Returns:
            A fixed DataFrame with proper headers
        """
        # If we don't have access to the original file, try to create a safer reconstruction
        try:
            # Create a new DataFrame with all data, including column names at the top
            # First create all data as strings
            all_data = []
            
            # Add column names as first row
            all_data.append([str(col) for col in df.columns])
            
            # Add all data rows
            for idx, row in df.iterrows():
                all_data.append([str(val) if pd.notna(val) else "" for val in row])
                
            # Create a raw DataFrame
            raw_df = pd.DataFrame(all_data)
            
            # Now use header detection on this raw dataframe
            # Look for header candidates - rows with several string values
            header_candidates = []
            for i in range(min(20, len(raw_df))):
                row = raw_df.iloc[i]
                string_count = sum(1 for val in row if isinstance(val, str) and len(str(val).strip()) > 0)
                digit_count = sum(1 for val in row if isinstance(val, (int, float)) or (
                    isinstance(val, str) and val.replace('.', '', 1).replace('-', '', 1).isdigit()
                ))
                
                # A good header row has more string values than numeric values
                if string_count > 3 and string_count > digit_count * 2:
                    header_candidates.append((i, string_count))
            
            if header_candidates:
                # Sort by number of string values, with preference for rows that are lower down
                # (financial statements often have multiple header-like rows)
                header_candidates.sort(key=lambda x: (x[1], x[0]), reverse=True)
                
                # Use the best candidate, with a preference for rows further down if string counts are similar
                chosen_header = header_candidates[0][0]
                
                # Create a new dataframe using this as the header
                header_row = raw_df.iloc[chosen_header]
                data_rows = raw_df.iloc[chosen_header+1:]
                
                # Create column names, ensuring they are unique
                column_names = []
                for val in header_row:
                    col_name = str(val).strip() if pd.notna(val) and str(val).strip() else "Column"
                    # Ensure unique column names
                    suffix = 1
                    base_name = col_name
                    while col_name in column_names:
                        col_name = f"{base_name}_{suffix}"
                        suffix += 1
                    column_names.append(col_name)
                
                # Create the new dataframe
                fixed_df = pd.DataFrame(data_rows.values, columns=column_names)
                
                # Remove any completely empty rows
                fixed_df = fixed_df.dropna(how='all')
                
                print(f"Fixed DataFrame using row {chosen_header} as header.")
                print(f"New columns: {fixed_df.columns.tolist()[:5]}...")
                return fixed_df
                
            else:
                print("No suitable header row found in the data.")
                return df
                
        except Exception as e:
            print(f"Error trying to fix DataFrame headers: {e}")
            return df
    
    def _generate_manual_schema(self, df: pd.DataFrame, header_text: str, provider_name: str) -> Dict[str, Any]:
        """
        Generate a schema manually based on column analysis when AI fails.
        
        Args:
            df: The DataFrame to analyze
            header_text: The header text from the file
            provider_name: The provider name
            
        Returns:
            A manually generated schema
        """
        # Initialize the schema with all required sections
        schema = {
            "ProviderName": provider_name,
            "Synonyms": [],
            "FilterTable": [],
            "Calculations": [],
            "HardcodedFields": [
                {
                    "FieldName": "dealer_group",
                    "Value": provider_name
                }
            ],
            "HeaderExtraction": []
        }
        
        # Log the presence of header text for debugging
        if header_text:
            print(f"Manual schema generation with header text: {len(header_text)} characters")
        else:
            print("Manual schema generation without header text")
        
        # Analyze columns to create appropriate mappings
        for col in df.columns:
            col_str = str(col)
            logical_field = None
            
            # Skip unnamed columns
            if col_str.startswith('Unnamed:') or col_str.strip() == "":
                continue
                
            # Define standard financial field mappings with more comprehensive patterns
            field_mappings = [
                # Advisor/Planner ID
                {"patterns": ['rep no', 'rep id', 'adviser code', 'adviser id', 'advisor code', 
                             'advisor id', 'adviser no', 'advisor no', 'planner id', 'planner code'], 
                 "field": "planner_id"},
                 
                # Advisor/Planner Name
                {"patterns": ['rep name', 'adviser name', 'advisor name', 'adviser trade name', 
                             'planner name', 'rep', 'authorised rep'], 
                 "field": "planner_name"},
                 
                # Policy/Contract Number
                {"patterns": ['policy no', 'policy number', 'policy', 'contract no', 'contract',
                             'policy ref', 'ptran key'], 
                 "field": "policy_number"},
                 
                # Customer/Client Name
                {"patterns": ['life insured', 'client name', 'customer name', 'customer', 'client',
                             'insured', 'insured name', 'owner', 'owner name'], 
                 "field": "customer_name"},
                 
                # Policy Type
                {"patterns": ['policy type', 'product type', 'product', 'plan type', 'plan', 
                             'contract type'], 
                 "field": "policy_type"},
                 
                # Revenue Types (commissions) - should be BEFORE other commission-specific fields
                {"patterns": ['comm type', 'commission type', 'revenue type', 'type of commission',
                              'commission category', 'comm category', 'commission code', 'comm code'], 
                 "field": "revenue_type"},
                 
                # Amounts excluding GST
                {"patterns": ['comm amt', 'commission amount', 'amount excl', 'excl gst', 
                             'ex gst', 'excluding gst', 'business placed', 'business amount',
                             'ins premium', 'premium', 'fund invested', 'investment', 
                             'investment amount', 'establishment fee amt', 'establishment fee'], 
                 "field": "excl_gst"},
                 
                # Commission-specific amounts (AFTER revenue_type)
                {"patterns": ['commission ', ' commission', 'precommission', 'postcommission',
                             'asr', 'fua', 'fee percentage', 'fee %'], 
                 "field": "revenue_type"},
                
                # GST Amounts
                {"patterns": ['gst amt', 'gst amount', 'tax amt', 'tax amount', 'commissiongst',
                             ' gst', 'gst ', ' tax', 'tax ', 'asr$gst', 'ins commission gst', 
                             'establishment fee gst', 'fee gst', 'commission tax'], 
                 "field": "gst_amt"},
                 
                # Total amounts (including GST)
                {"patterns": ['total', 'incl', 'including', 'incl gst', 'inc gst', 
                             'establishment fee total', 'grand total', 'total amount', 
                             'total fee', 'fee total'], 
                 "field": "incl_gst"},
                 
                # Annual premium
                {"patterns": ['annual premium', 'annual', 'annual amount', 'premium amount',
                             'premium paid', 'annual rate', 'fund bal', 'fund balance'], 
                 "field": "annual_premium"},
                 
                # Dates
                {"patterns": ['date', 'transaction date', 'tran date', 'statement date', 
                             'effective date', 'entry date', 'period date'], 
                 "field": "date"}
            ]
            
            # Default to a snake_case conversion of the column name
            logical_field = col_str.lower().replace(' ', '_').replace('-', '_')
            logical_field = ''.join(c for c in logical_field if c.isalnum() or c == '_')
            if not logical_field[0].isalpha():
                logical_field = 'field_' + logical_field
                
            # Look for matches in our field mappings
            col_lower = col_str.lower()
            for mapping in field_mappings:
                if any(pattern in col_lower for pattern in mapping["patterns"]):
                    logical_field = mapping["field"]
                    break
                    
            # Standard field name mapping (ensure we use consistent fields)
            standard_field_substitutions = {
                'commission': 'revenue_type',
                'precommission': 'revenue_type',
                'postcommission': 'revenue_type',
                'advisor_code': 'planner_id',
                'adviser_code': 'planner_id',
                'advisor_id': 'planner_id',
                'adviser_id': 'planner_id',
                'advisor_name': 'planner_name',
                'adviser_name': 'planner_name',
                'client_name': 'customer_name',
                'policy_no': 'policy_number',
                'transaction_date': 'date',
                'tran_date': 'date'
            }
            
            # Check if this field should be standardized
            if logical_field in standard_field_substitutions:
                logical_field = standard_field_substitutions[logical_field]
            
            # Check if this logical field already exists in the schema
            existing_field = None
            for syn in schema["Synonyms"]:
                if syn["LogicalField"] == logical_field:
                    existing_field = syn
                    break
                    
            if existing_field:
                # Add this column as an additional alternate name
                existing_field["AlternateNames"].append(col_str)
            else:
                # Create a new entry
                schema["Synonyms"].append({
                    "LogicalField": logical_field,
                    "AlternateNames": [col_str]
                })
        
        # Add common filters
        if any(syn["LogicalField"] == "planner_id" for syn in schema["Synonyms"]):
            schema["FilterTable"].append("[planner_id] <> null")
            schema["FilterTable"].append("[planner_id] <> \"\"")
            
        if any(syn["LogicalField"] == "excl_gst" for syn in schema["Synonyms"]):
            schema["FilterTable"].append("[excl_gst] <> 0")
        
        # Add calculations if we have the right fields
        has_excl_gst = any(syn["LogicalField"] == "excl_gst" for syn in schema["Synonyms"])
        has_gst_amt = any(syn["LogicalField"] == "gst_amt" for syn in schema["Synonyms"])
        has_incl_gst = any(syn["LogicalField"] == "incl_gst" for syn in schema["Synonyms"])
        
        # Standardized financial calculations
        if has_excl_gst and not has_gst_amt:
            schema["Calculations"].append({
                "NewField": "gst_amt",
                "Expression": "([excl_gst] * 0.15)"
            })
            
        if has_excl_gst and has_gst_amt and not has_incl_gst:
            schema["Calculations"].append({
                "NewField": "incl_gst",
                "Expression": "([excl_gst] + [gst_amt])"
            })
            
        if has_gst_amt and has_incl_gst and not has_excl_gst:
            schema["Calculations"].append({
                "NewField": "excl_gst",
                "Expression": "([incl_gst] - [gst_amt])"
            })
        
        # Extract from header text if available
        if header_text:
            import re
            
            # Look for exact date patterns that match the format in this file
            date_patterns = [
                r'For the Period Ending:\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})',
                r'Date:\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})',
                r'As at:\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})',
                r'Statement Date:\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})',
                r'Period:\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})'
            ]
            
            date_found = False
            for pattern in date_patterns:
                date_match = re.search(pattern, header_text)
                if date_match:
                    # Get the full match to extract the exact text before the date
                    full_match = date_match.group(0)
                    # Find where the colon is to get the proper delimiter
                    if ':' in full_match:
                        start_delim = full_match.split(':', 1)[0] + ': '
                    else:
                        # If no colon, use the whole text up to the date
                        start_idx = full_match.rfind(date_match.group(1))
                        start_delim = full_match[:start_idx]
                        
                    # For ASTERON LIFE format, use exact delimiter text
                    if "For the Period Ending:" in header_text:
                        schema["HeaderExtraction"].append({
                            "FieldName": "date",
                            "StartDelim": "For the Period Ending: ",
                            "EndDelim": "\n"
                        })
                    else:
                        # For other formats, use the detected delimiter
                        schema["HeaderExtraction"].append({
                            "FieldName": "date",
                            "StartDelim": start_delim,
                            "EndDelim": "\n"
                        })
                    date_found = True
                    break
                    
            # If no date found but "Period" or similar is in the text, make a more aggressive attempt
            if not date_found and any(term in header_text for term in ['Period', 'Date', 'As at']):
                # Just look for any date pattern
                simple_date_match = re.search(r'([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})', header_text)
                if simple_date_match:
                    # Find some text before this date to use as delimiter
                    date_pos = header_text.find(simple_date_match.group(1))
                    if date_pos > 10:  # Ensure we have enough text before
                        # Look back up to 30 characters to find a good delimiter
                        prefix_text = header_text[max(0, date_pos-30):date_pos]
                        # Find the last occurrence of : or similar punctuation
                        colon_pos = max(prefix_text.rfind(':'), prefix_text.rfind('-'), prefix_text.rfind('—'))
                        if colon_pos >= 0:
                            # Use text from the punctuation to the date
                            start_delim = prefix_text[colon_pos-10:].strip()
                            schema["HeaderExtraction"].append({
                                "FieldName": "date",
                                "StartDelim": start_delim,
                                "EndDelim": "\n"
                            })
                
            # Look for practice/company name using various patterns
            company_patterns = [
                r'To \(Supplier\):\s*([^\n]+)',
                r'(?:To|Supplier|Practice|Licensee).*?[:-]\s*([^\n\r]+)',
                r'(?:Name|Company).*?[:-]\s*([^\n\r]+)'
            ]
            
            for pattern in company_patterns:
                practice_match = re.search(pattern, header_text)
                if practice_match:
                    # Get the full match to extract the exact text before the company name
                    full_match = practice_match.group(0)
                    # Extract the proper start delimiter
                    if ':' in full_match:
                        start_delim = full_match.split(':', 1)[0] + ': '
                    else:
                        # If no colon, find another delimiter
                        delim_idx = max(full_match.rfind('-'), full_match.rfind('—'), full_match.rfind('–'))
                        if delim_idx >= 0:
                            start_delim = full_match[:delim_idx+1] + ' '
                        else:
                            # Fallback - use the text before the company name
                            company_pos = full_match.find(practice_match.group(1))
                            start_delim = full_match[:company_pos]
                            
                    # For ASTERON LIFE format, use exact delimiter text
                    if "To (Supplier):" in header_text:
                        schema["HeaderExtraction"].append({
                            "FieldName": "practice_name",
                            "StartDelim": "To (Supplier): ",
                            "EndDelim": "\n"
                        })
                    else:
                        # For other formats, use the detected delimiter
                        schema["HeaderExtraction"].append({
                            "FieldName": "practice_name",
                            "StartDelim": start_delim,
                            "EndDelim": "\n"
                        })
                    break
        
        return schema
        
    def _prepare_data_sample(self, df: pd.DataFrame, header_text: str) -> Dict[str, Any]:
        """
        Prepare a data sample for AI processing.
        
        Args:
            df: Anonymized DataFrame
            header_text: Anonymized header text
            
        Returns:
            Dictionary with sample data in a format suitable for AI
        """
        # Always start by ensuring the DataFrame has proper structure
        df = self._ensure_proper_dataframe_structure(df)
        
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Replace NaT values with None in datetime columns to avoid JSON serialization issues
        for col in df.select_dtypes(include=['datetime64']).columns:
            df[col] = df[col].astype(object).where(~pd.isna(df[col]), None)
            
        # Include only first few rows to limit data sent
        sample_rows = min(5, len(df))
        sample_df = df.head(sample_rows)
        
        # Add metadata to help the AI understand this is a financial file
        financial_metadata = {
            "file_type": "financial_statement",
            "document_type": "commission_statement",
            "likely_financial_columns": []
        }
        
        # Identify likely financial columns
        for col in df.columns:
            col_str = str(col).lower()
            if any(term in col_str for term in ['rep no', 'adviser', 'advisor', 'planner']):
                financial_metadata["likely_financial_columns"].append({"column": str(col), "role": "advisor_identifier"})
            elif any(term in col_str for term in ['name', 'insured']):
                financial_metadata["likely_financial_columns"].append({"column": str(col), "role": "name"})
            elif any(term in col_str for term in ['policy', 'contract']):
                financial_metadata["likely_financial_columns"].append({"column": str(col), "role": "policy_identifier"})
            elif any(term in col_str for term in ['comm', 'type']):
                financial_metadata["likely_financial_columns"].append({"column": str(col), "role": "commission_type"})
            elif any(term in col_str for term in ['gst', 'tax']):
                financial_metadata["likely_financial_columns"].append({"column": str(col), "role": "tax_amount"})
            elif any(term in col_str for term in ['amt', 'amount', 'premium', 'excl']):
                financial_metadata["likely_financial_columns"].append({"column": str(col), "role": "amount_excluding_tax"})
            elif any(term in col_str for term in ['total', 'incl']):
                financial_metadata["likely_financial_columns"].append({"column": str(col), "role": "amount_including_tax"})
            
        # Add explicit table structure information
        table_structure = {
            "has_header_row": True,
            "primary_data_table": {
                "column_names": list(df.columns),
                "row_count": len(df),
                "sample_rows": sample_df.to_dict(orient='records')
            },
            "header_text": {
                "text": header_text,
                "contains_metadata": len(header_text) > 0
            }
        }
        
        # Analyze the structure and content of the data
        column_analysis = {}
        for col in sample_df.columns:
            column_data = sample_df[col].dropna()
            
            # Skip empty columns
            if len(column_data) == 0:
                continue
                
            # Determine likely data type and format
            sample_values = column_data.head(3).tolist()
            
            # Check if column might be numeric
            numeric_values = 0
            for val in column_data:
                if isinstance(val, (int, float)) or (isinstance(val, str) and val.replace('.', '', 1).isdigit()):
                    numeric_values += 1
            
            numeric_ratio = numeric_values / len(column_data) if len(column_data) > 0 else 0
            
            # Identify potential roles of columns
            role = "unknown"
            col_name = str(col).lower()
            
            # Common column name patterns
            if any(name in col_name for name in ['date', 'period', 'time']):
                role = "date"
            elif any(name in col_name for name in ['amount', 'total', 'sum', 'value', 'premium', 'gst', 'exc', 'inc']):
                role = "amount"
            elif any(name in col_name for name in ['id', 'no', 'number', 'ref', 'policy']):
                role = "identifier"
            elif any(name in col_name for name in ['name', 'client', 'customer', 'insured', 'rep', 'adviser']):
                role = "name"
            elif any(name in col_name for name in ['type', 'category', 'comm']):
                role = "category"
                
            column_analysis[str(col)] = {
                "likely_type": "numeric" if numeric_ratio > 0.8 else "text",
                "sample_values": [str(v) for v in sample_values],
                "likely_role": role
            }
        
        # Extract potential header extraction patterns if header text exists
        header_extraction_patterns = []
        if header_text:
            # Look for common patterns in header text
            import re
            
            # Date patterns
            date_matches = re.findall(r'(?:(?:for|as at|period|date).*?[:-]?\s*)([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})', 
                                   header_text.lower())
            if date_matches:
                for match in date_matches:
                    # Find the text before the date
                    pattern_start = header_text.lower().find(match)
                    if pattern_start > 10:  # Ensure there's text before
                        # Look for a reasonable delimiter
                        pre_text = header_text.lower()[max(0, pattern_start-50):pattern_start]
                        for delim in ['for the period ending:', 'as at:', 'statement date:', 'date:', 'period:']:
                            if delim in pre_text:
                                header_extraction_patterns.append({
                                    "field": "date",
                                    "start_delim": delim,
                                    "end_delim": match + " ",  # Add space to avoid partial matches
                                    "example": match
                                })
                                break
            
            # Provider/practice patterns
            provider_matches = re.findall(r'(?:to|supplier|practice).*?[:-]?\s*([a-z0-9\s]+(?:pty\.?)?(?:\s+ltd)?)', 
                                       header_text.lower())
            if provider_matches:
                for match in provider_matches:
                    pattern_start = header_text.lower().find(match)
                    if pattern_start > 10:
                        pre_text = header_text.lower()[max(0, pattern_start-30):pattern_start]
                        for delim in ['to (supplier):', 'supplier:', 'practice:', 'to:']:
                            if delim in pre_text:
                                header_extraction_patterns.append({
                                    "field": "practice_name",
                                    "start_delim": delim,
                                    "end_delim": " abn" if "abn" in match else match,
                                    "example": match.strip()
                                })
                                break
        
        # Convert to dict for serialization
        data_dict = {
            'columns': list(sample_df.columns),
            'data_types': {col: str(sample_df[col].dtype) for col in sample_df.columns},
            'sample_rows': sample_df.to_dict(orient='records'),
            'header_text': header_text if header_text else "No header text available",
            'column_analysis': column_analysis,
            'potential_header_extraction': header_extraction_patterns,
            'financial_metadata': financial_metadata,
            'table_structure': table_structure,
            'schema_guidance': {
                'provider_name': 'Use the provided provider name exactly as given',
                'logical_fields': {
                    'planner_id': 'For advisor/rep IDs',
                    'planner_name': 'For advisor/rep names',
                    'policy_number': 'For policy or contract numbers',
                    'customer_name': 'For client/insured names',
                    'policy_type': 'For types of policies',
                    'revenue_type': 'For commission types',
                    'excl_gst': 'For amounts excluding GST/tax',
                    'gst_amt': 'For GST/tax amounts',
                    'incl_gst': 'For total amounts including GST/tax',
                    'date': 'For statement/effective dates'
                },
                'naming_rules': 'Do not use column names directly as logical fields',
                'mapping_instructions': 'Map each column to the most appropriate standard logical field name'
            }
        }
        
        return data_dict
        
    def _generate_schema_with_ai(self, data_sample: Dict[str, Any], provider_name: str) -> Dict[str, Any]:
        """
        Generate schema using AI service.
        
        Args:
            data_sample: Prepared data sample
            provider_name: Name for the provider
            
        Returns:
            Generated provider schema
        """
        if not self.api_key:
            # If no API key, return a basic schema
            return self._generate_basic_schema(data_sample, provider_name)
            
        # Prepare the prompt for AI
        prompt = self._build_ai_prompt(data_sample, provider_name)
        
        try:
            # Call AI service (Claude API in this case)
            response = self._call_claude_api(prompt)
            schema = self._extract_schema_from_response(response)
            
            # Validate the schema
            if self._validate_schema(schema):
                return schema
            else:
                # Fallback to basic schema if validation fails
                print("Warning: AI-generated schema failed validation. Using basic schema instead.")
                return self._generate_basic_schema(data_sample, provider_name)
                
        except Exception as e:
            print(f"Error generating schema with AI: {e}")
            # Fallback to basic schema
            return self._generate_basic_schema(data_sample, provider_name)
    
    def _build_ai_prompt(self, data_sample: Dict[str, Any], provider_name: str) -> str:
        """
        Build the prompt for the AI service.
        
        Args:
            data_sample: Prepared data sample
            provider_name: Name for the provider
            
        Returns:
            Complete prompt for AI
        """
        # Convert data sample to formatted JSON
        data_json = json.dumps(data_sample, indent=2)
        
        # Build a prompt with detailed instructions about schema format
        prompt = """You are a financial data expert who creates schemas for the DataHarmonizer system.

I need you to analyze the structure of this financial data sample and create a provider schema that follows the exact format required by our system.

Here is the data sample:
```json
""" + data_json + """
```

# Schema Structure Requirements
Create a schema for provider named """ + provider_name + """ with the following structure:
1. "ProviderName": The name of the provider
2. "Synonyms": Array of mappings from logical field names to alternate names in the data
3. "FilterTable": Array of filter expressions to apply (e.g., "[amount] > 0")
4. "Calculations": Array of calculations to perform (e.g., {"NewField": "gst_amt", "Expression": "[amount] * 0.15"})
5. "HardcodedFields": Array of constant values to add (e.g., {"FieldName": "provider", "Value": "Example"})
6. "HeaderExtraction": Optional array of rules to extract values from header text
7. "UnpivotColumns": Optional settings for unpivoting data from wide to long format

# Synonym Format
Each synonym mapping should be an object with:
- "LogicalField": The standardized field name (e.g., "date", "amount")
- "AlternateNames": Array of possible column names that represent this field

# Specific Instructions
1. Focus on common financial fields like dates, amounts, descriptions, reference numbers
2. Include calculations for GST (15%) and GST-exclusive amounts where relevant
3. The schema MUST use proper JSON formatting with double quotes for keys and string values
4. Follow the exact structure used by the DataHarmonizer application
5. Ensure all field references in calculations use square brackets, e.g., "[field_name]"
6. Use lowercase for all logical field names

# Sample Response Format
```json
{
  "ProviderName": "ExampleProvider",
  "Synonyms": [
    {
      "LogicalField": "date",
      "AlternateNames": ["Date", "TransDate", "Invoice Date"]
    },
    {
      "LogicalField": "amount",
      "AlternateNames": ["Amount", "Total", "Value"]
    }
  ],
  "FilterTable": ["[amount] <> 0"],
  "Calculations": [
    {
      "NewField": "gst_amt",
      "Expression": "[amount] * 0.15"
    },
    {
      "NewField": "excl_gst",
      "Expression": "[amount] - [gst_amt]"
    }
  ],
  "HardcodedFields": [
    {
      "FieldName": "provider",
      "Value": "ExampleProvider"
    }
  ]
}
```

Analyze the provided data and generate a complete provider schema that matches this exact format.
Return only the schema as a valid JSON object.
"""
        
        return prompt
        
    def _call_claude_api(self, prompt: str) -> str:
        """
        Call the Claude API to generate a schema.
        
        Args:
            prompt: The prepared prompt
            
        Returns:
            AI response text
        """
        # Import the Claude client
        from schema_builder.ai.claude_client import ClaudeClient
        
        # Create a client with the API key from environment variable or initialization
        client = ClaudeClient(api_key=self.api_key)
        
        # Generate schema using the client
        response = client.generate_schema(prompt)
        
        return response
        
    def _extract_schema_from_response(self, response: str) -> Dict[str, Any]:
        """
        Extract the schema from the AI response.
        
        Args:
            response: AI response text
            
        Returns:
            Extracted schema as a dictionary
        """
        try:
            # Try to parse as JSON
            schema = json.loads(response)
            
            # Do a quick validation check before returning
            if not self._basic_schema_sanity_check(schema):
                print("Warning: AI returned a schema that fails basic validation - generating fallback schema")
                return {}
                
            return schema
        except json.JSONDecodeError:
            # If not valid JSON, try to extract JSON from markdown code block
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if json_match:
                try:
                    schema = json.loads(json_match.group(1))
                    
                    # Do a quick validation check
                    if not self._basic_schema_sanity_check(schema):
                        print("Warning: AI returned a schema in a code block that fails basic validation - generating fallback schema")
                        return {}
                        
                    return schema
                except json.JSONDecodeError:
                    pass
            
            # If all else fails, generate a basic schema
            print("Warning: Could not parse AI response as JSON")
            return {}
    
    def _basic_schema_sanity_check(self, schema: Dict[str, Any]) -> bool:
        """
        Perform a basic sanity check on the schema to catch obviously broken schemas.
        
        Args:
            schema: The schema to check
            
        Returns:
            True if schema passes basic checks, False otherwise
        """
        # Check that ProviderName exists
        if "ProviderName" not in schema:
            print("Schema sanity check failed: Missing ProviderName")
            return False
            
        # Check that Synonyms exists and is a list
        if "Synonyms" not in schema or not isinstance(schema["Synonyms"], list):
            print("Schema sanity check failed: Missing or invalid Synonyms")
            return False
            
        # Check that Synonyms is not empty
        if len(schema["Synonyms"]) == 0:
            print("Schema sanity check failed: Empty Synonyms list")
            return False
            
        # Check that Synonyms have proper structure
        for syn in schema["Synonyms"]:
            if not isinstance(syn, dict):
                print("Schema sanity check failed: Synonym is not a dictionary")
                return False
                
            if "LogicalField" not in syn or "AlternateNames" not in syn:
                print("Schema sanity check failed: Synonym missing required fields")
                return False
                
            # Check that no logical field starts with "unnamed:" as that indicates a header detection issue
            if isinstance(syn.get("LogicalField"), str) and syn["LogicalField"].lower().startswith("unnamed:"):
                print("Schema sanity check failed: Found logical field starting with 'unnamed:' which indicates a header detection issue")
                return False
                
            # Check that no more than 20% of logical fields start with "unnamed" which indicates header detection issues
            unnamed_count = sum(1 for s in schema["Synonyms"] 
                              if isinstance(s.get("LogicalField"), str) and 
                              s["LogicalField"].lower().startswith("unnamed"))
            if unnamed_count > len(schema["Synonyms"]) * 0.2:
                print(f"Schema sanity check failed: {unnamed_count} of {len(schema['Synonyms'])} logical fields start with 'unnamed'")
                return False
        
        # Schema passed basic checks
        return True
            
    def _validate_schema(self, schema: Dict[str, Any]) -> bool:
        """
        Validate that the schema has the required structure.
        
        Args:
            schema: Schema to validate
            
        Returns:
            True if schema is valid, False otherwise
        """
        # Check required keys
        required_keys = ["ProviderName", "Synonyms"]
        if not all(key in schema for key in required_keys):
            print(f"Schema validation failed: Missing required keys. Found: {list(schema.keys())}")
            return False
            
        # Check Synonyms structure
        synonyms = schema.get("Synonyms", [])
        if not isinstance(synonyms, list) or not synonyms:
            print("Schema validation failed: Synonyms must be a non-empty list")
            return False
            
        for i, syn in enumerate(synonyms):
            if not isinstance(syn, dict):
                print(f"Schema validation failed: Synonym {i} is not a dictionary")
                return False
                
            if "LogicalField" not in syn:
                print(f"Schema validation failed: Synonym {i} missing LogicalField")
                return False
                
            if "AlternateNames" not in syn:
                print(f"Schema validation failed: Synonym {i} missing AlternateNames")
                return False
                
            if not isinstance(syn["AlternateNames"], list):
                print(f"Schema validation failed: AlternateNames in synonym {i} must be a list")
                return False
        
        # Check valid top-level keys
        allowed_keys = ["ProviderName", "Synonyms", "FilterTable", "Calculations", "HardcodedFields", "HeaderExtraction"]
        for key in schema.keys():
            if key not in allowed_keys:
                print(f"Schema validation failed: Invalid top-level key '{key}'")
                return False
        
        # Check FilterTable if present
        if "FilterTable" in schema:
            filter_table = schema["FilterTable"]
            if not isinstance(filter_table, list):
                print("Schema validation failed: FilterTable must be a list")
                return False
                
            for i, filter_expr in enumerate(filter_table):
                if not isinstance(filter_expr, str):
                    print(f"Schema validation failed: Filter expression {i} must be a string")
                    return False
        
        # Check Calculations if present
        if "Calculations" in schema:
            calculations = schema["Calculations"]
            if not isinstance(calculations, list):
                print("Schema validation failed: Calculations must be a list")
                return False
                
            for i, calc in enumerate(calculations):
                if not isinstance(calc, dict):
                    print(f"Schema validation failed: Calculation {i} must be a dictionary")
                    return False
                    
                if "NewField" not in calc:
                    print(f"Schema validation failed: Calculation {i} missing NewField")
                    return False
                    
                if "Expression" not in calc:
                    print(f"Schema validation failed: Calculation {i} missing Expression")
                    return False
        
        # Check HardcodedFields if present
        if "HardcodedFields" in schema:
            hardcoded = schema["HardcodedFields"]
            if not isinstance(hardcoded, list):
                print("Schema validation failed: HardcodedFields must be a list")
                return False
                
            for i, field in enumerate(hardcoded):
                if not isinstance(field, dict):
                    print(f"Schema validation failed: Hardcoded field {i} must be a dictionary")
                    return False
                    
                if "FieldName" not in field:
                    print(f"Schema validation failed: Hardcoded field {i} missing FieldName")
                    return False
                    
                if "Value" not in field:
                    print(f"Schema validation failed: Hardcoded field {i} missing Value")
                    return False
        
        # Check HeaderExtraction if present
        if "HeaderExtraction" in schema:
            extraction = schema["HeaderExtraction"]
            if not isinstance(extraction, list):
                print("Schema validation failed: HeaderExtraction must be a list")
                return False
                
            for i, rule in enumerate(extraction):
                if not isinstance(rule, dict):
                    print(f"Schema validation failed: Header extraction rule {i} must be a dictionary")
                    return False
                    
                required_rule_keys = ["FieldName", "StartDelim", "EndDelim"]
                for key in required_rule_keys:
                    if key not in rule:
                        print(f"Schema validation failed: Header extraction rule {i} missing '{key}'")
                        return False
                
                # Check for invalid keys in HeaderExtraction
                for key in rule.keys():
                    if key not in required_rule_keys:
                        print(f"Schema validation failed: Invalid key '{key}' in header extraction rule {i}")
                        return False
                
                # Verify StartDelim and EndDelim don't contain obvious regex patterns
                for pattern_key in ['StartDelim', 'EndDelim']:
                    pattern_value = rule.get(pattern_key, '')
                    # Only check for obvious regex patterns like .* or \d - allow normal parentheses
                    if any(regex_char in pattern_value for regex_char in ['.*', '.+', '[', ']', '{', '}', '\\d', '\\w', '\\s']):
                        print(f"Schema validation failed: {pattern_key} in rule {i} contains regex patterns. Use plain text only.")
                        return False
        
        # Schema appears valid
        return True
        
    def _generate_basic_schema(self, data_sample: Dict[str, Any], provider_name: str) -> Dict[str, Any]:
        """
        Generate a basic schema without AI assistance.
        
        Args:
            data_sample: Prepared data sample
            provider_name: Name for the provider
            
        Returns:
            Basic provider schema
        """
        columns = data_sample.get("columns", [])
        header_text = data_sample.get("header_text", "")
        
        # Create a basic schema with one-to-one column mappings
        schema = {
            "ProviderName": provider_name,
            "Synonyms": [],
            "FilterTable": [],
            "Calculations": [],
            "HardcodedFields": [
                {
                    "FieldName": "provider",
                    "Value": provider_name
                }
            ],
            "HeaderExtraction": []
        }
        
        # Include header extraction if we have header text
        if header_text and "No header text available" not in header_text:
            # Include any pre-detected header extraction patterns
            potential_patterns = data_sample.get("potential_header_extraction", [])
            
            for pattern in potential_patterns:
                field = pattern.get("field", "")
                start_delim = pattern.get("start_delim", "")
                end_delim = pattern.get("end_delim", "")
                
                if field and start_delim:
                    schema["HeaderExtraction"].append({
                        "FieldName": field,
                        "StartDelim": start_delim,
                        "EndDelim": end_delim if end_delim else "\n"
                    })
        
        # Generate synonyms from columns
        for col in columns:
            # Convert column name to a reasonable logical field
            logical_field = col.lower().replace(" ", "_").replace("-", "_")
            
            schema["Synonyms"].append({
                "LogicalField": logical_field,
                "AlternateNames": [col]
            })
            
        # Add basic filters for common fields
        amount_columns = [col for col in columns if "amount" in col.lower() or "total" in col.lower()]
        for amount_col in amount_columns:
            schema["FilterTable"].append(f"[{amount_col}] <> 0")
            
        # Add tax calculation if we have an amount field
        if amount_columns:
            amount_col = amount_columns[0]
            schema["Calculations"].append({
                "NewField": "tax_amount",
                "Expression": f"([{amount_col}] * 0.15)"
            })
            
        return schema