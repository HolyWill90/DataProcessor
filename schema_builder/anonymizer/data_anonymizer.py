"""
Data anonymizer for provider schema generation.

This module provides tools to anonymize financial data while preserving structure,
allowing users to generate provider schemas without exposing sensitive information.
"""
import pandas as pd
import numpy as np
import random
import string
import re
import os
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple


class DataAnonymizer:
    """
    Anonymizes financial data while preserving structure and patterns.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the DataAnonymizer.
        
        Args:
            seed: Optional random seed for reproducible anonymization
        """
        self.random = random.Random(seed)
        self.companies = [
            "Acme Corp", "Globex", "Initech", "Umbrella", "Stark Industries",
            "Wayne Enterprises", "Cyberdyne", "LexCorp", "Oceanic Airlines",
            "Soylent Corp", "Virtucon", "Massive Dynamic", "Tyrell Corp"
        ]
        
    def anonymize_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Anonymize a file directly, using the proper FileProcessor for header detection.
        
        Args:
            file_path: Path to the file to anonymize
            
        Returns:
            Dictionary with anonymized data and metadata
        """
        # Import FileProcessor here to avoid circular imports
        from core.file_processor import FileProcessor
        
        # Use the FileProcessor to get the properly structured data
        file_processor = FileProcessor()
        result = file_processor.process_file(file_path)
        
        # Extract the data and header text
        df = result.get('Data', pd.DataFrame())
        header_text = result.get('PreHeaderText', '')
        
        # Anonymize both components
        anonymized_df = self.anonymize_dataframe(df)
        anonymized_header = self.anonymize_header_text(header_text)
        
        return {
            "Data": anonymized_df,
            "HeaderText": anonymized_header,
            "OriginalData": df,
            "OriginalHeaderText": header_text
        }
        
    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Anonymize a DataFrame while preserving column structure and data patterns.
        
        Args:
            df: Source DataFrame to anonymize
            
        Returns:
            Anonymized DataFrame with same structure
        """
        if df.empty:
            return df.copy()
            
        # Create a copy to avoid modifying the original
        anon_df = df.copy()
        
        # Process each column based on detected data type
        for col in anon_df.columns:
            col_data = anon_df[col].dropna()
            
            # Skip columns with no data
            if len(col_data) == 0:
                continue
                
            # Detect data type
            if self._is_date_column(col_data):
                anon_df[col] = self._anonymize_dates(col_data)
            elif self._is_numeric_column(col_data):
                anon_df[col] = self._anonymize_numbers(col_data)
            elif self._is_invoice_number(col, col_data):
                anon_df[col] = self._anonymize_invoice_numbers(col_data)
            elif self._is_email_column(col_data):
                anon_df[col] = self._anonymize_emails(col_data)
            elif self._is_name_column(col):
                anon_df[col] = self._anonymize_names(col_data)
            else:
                anon_df[col] = self._anonymize_text(col_data)
                
        return anon_df
        
    def anonymize_header_text(self, text: str) -> str:
        """
        Anonymize header text while preserving format and patterns.
        
        Args:
            text: Source header text
            
        Returns:
            Anonymized header text
        """
        if not text:
            return ""
            
        # Replace dates with random dates in same format
        date_pattern = r"\b\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}\b"
        text = re.sub(date_pattern, lambda m: self._random_date_string(), text)
        
        # Replace amounts with random amounts
        amount_pattern = r"\$?\s?\d+[,\.]?\d*"
        text = re.sub(amount_pattern, lambda m: f"${self.random.randint(100, 9999)}.{self.random.randint(0, 99):02d}", text)
        
        # Replace account numbers
        account_pattern = r"\b(Acc|Account|ID)[ :]+\d+\b"
        text = re.sub(account_pattern, lambda m: f"{m.group(1)}: {self._random_account_number()}", text)
        
        # Replace company names with random company names
        for company in self.companies:
            if company.lower() in text.lower():
                text = re.sub(re.escape(company), self.random.choice(self.companies), text, flags=re.IGNORECASE)
        
        return text
        
    def _is_date_column(self, col_data: pd.Series) -> bool:
        """Detect if a column contains date values."""
        # Check if pandas already detected it as datetime
        if pd.api.types.is_datetime64_dtype(col_data):
            return True
            
        # Check if the column name suggests a date
        col_name = col_data.name.lower()
        date_indicators = ['date', 'day', 'month', 'year', 'time', 'period']
        if any(ind in col_name for ind in date_indicators):
            # Try to convert to datetime
            try:
                pd.to_datetime(col_data, errors='raise', dayfirst=True)
                return True
            except:
                pass
        
        # Check for common date patterns in strings
        if col_data.dtype == 'object':
            date_pattern = r"\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}"
            sample = col_data.astype(str).sample(min(10, len(col_data))).str
            return sample.match(date_pattern).any()
            
        return False
        
    def _is_numeric_column(self, col_data: pd.Series) -> bool:
        """Detect if a column contains numeric values."""
        # Check if pandas already detected it as numeric
        if pd.api.types.is_numeric_dtype(col_data):
            return True
            
        # Check if string values can be converted to numbers
        if col_data.dtype == 'object':
            # Try to convert the first few non-empty values
            sample = col_data.dropna().astype(str).head(5)
            for val in sample:
                val = val.strip().replace(',', '')
                try:
                    float(val)
                except ValueError:
                    return False
            return True
            
        return False
        
    def _is_invoice_number(self, colname: str, col_data: pd.Series) -> bool:
        """Detect if a column contains invoice numbers."""
        # Check column name
        col_lower = colname.lower()
        invoice_indicators = ['invoice', 'inv', 'ref', 'reference', 'document', 'doc']
        
        if any(ind in col_lower for ind in invoice_indicators):
            # Check for common invoice patterns (mixture of letters and numbers)
            if col_data.dtype == 'object':
                pattern = r"^[A-Za-z0-9\-]+$"
                sample = col_data.astype(str).sample(min(5, len(col_data)))
                matches = sample.str.match(pattern)
                return matches.mean() > 0.8  # 80% of sample matches pattern
                
        return False
        
    def _is_email_column(self, col_data: pd.Series) -> bool:
        """Detect if a column contains email addresses."""
        if col_data.dtype != 'object':
            return False
            
        email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        sample = col_data.astype(str).sample(min(5, len(col_data)))
        matches = sample.str.match(email_pattern)
        return matches.mean() > 0.5  # 50% of sample matches email pattern
        
    def _is_name_column(self, colname: str) -> bool:
        """Detect if a column likely contains personal names."""
        col_lower = colname.lower()
        name_indicators = ['name', 'customer', 'client', 'vendor', 'supplier', 'contact', 'person']
        return any(ind in col_lower for ind in name_indicators)
        
    def _anonymize_dates(self, col_data: pd.Series) -> pd.Series:
        """Anonymize date values while preserving distribution."""
        try:
            # Convert to datetime if not already
            dates = pd.to_datetime(col_data, errors='coerce', dayfirst=True)
            
            # Get min and max dates from the series
            min_date = dates.min()
            max_date = dates.max()
            
            if pd.isna(min_date) or pd.isna(max_date):
                # Fallback if conversion fails
                return pd.Series([self._random_date_string() for _ in range(len(col_data))], index=col_data.index)
            
            # Generate random dates in the same range
            time_range = (max_date - min_date).days
            
            # If the range is too small, expand it
            if time_range < 30:
                time_range = 30
                
            random_days = [self.random.randint(0, time_range) for _ in range(len(col_data))]
            random_dates = [min_date + datetime.timedelta(days=days) for days in random_days]
            
            return pd.Series(random_dates, index=col_data.index)
        except:
            # Fallback for any errors
            return pd.Series([self._random_date_string() for _ in range(len(col_data))], index=col_data.index)
            
    def _anonymize_numbers(self, col_data: pd.Series) -> pd.Series:
        """Anonymize numeric values while preserving distribution."""
        try:
            # Convert to numeric if not already
            numbers = pd.to_numeric(col_data, errors='coerce')
            
            # Get stats for the distribution
            min_val = numbers.min()
            max_val = numbers.max()
            mean_val = numbers.mean()
            
            if pd.isna(min_val) or pd.isna(max_val) or pd.isna(mean_val):
                # Fallback if conversion fails
                return pd.Series([float(self.random.randint(100, 10000)) for _ in range(len(col_data))], 
                                index=col_data.index)
            
            # Generate random numbers with similar distribution
            range_val = max_val - min_val
            random_numbers = []
            
            for _ in range(len(col_data)):
                # Random values close to the mean with occasional outliers
                if self.random.random() < 0.8:
                    # 80% close to mean
                    rand_val = self.random.uniform(mean_val * 0.8, mean_val * 1.2)
                else:
                    # 20% anywhere in the range
                    rand_val = self.random.uniform(min_val, max_val)
                
                # Preserve integer vs float
                if pd.api.types.is_integer_dtype(col_data):
                    rand_val = int(rand_val)
                    
                random_numbers.append(rand_val)
                
            return pd.Series(random_numbers, index=col_data.index)
        except:
            # Fallback for any errors
            return pd.Series([float(self.random.randint(100, 10000)) for _ in range(len(col_data))], 
                          index=col_data.index)
            
    def _anonymize_invoice_numbers(self, col_data: pd.Series) -> pd.Series:
        """Anonymize invoice numbers while preserving format."""
        anonymized = []
        
        for value in col_data:
            if pd.isna(value):
                anonymized.append(value)
                continue
                
            str_val = str(value)
            
            # Analyze the pattern (letters, numbers, format)
            letter_positions = [i for i, c in enumerate(str_val) if c.isalpha()]
            number_positions = [i for i, c in enumerate(str_val) if c.isdigit()]
            other_chars = [c for c in str_val if not c.isalnum()]
            
            # Create a new random value with the same pattern
            new_value = list(' ' * len(str_val))
            
            # Fill in letters
            for pos in letter_positions:
                new_value[pos] = self.random.choice(string.ascii_uppercase)
                
            # Fill in numbers
            for pos in number_positions:
                new_value[pos] = str(self.random.randint(0, 9))
                
            # Add other characters back
            for c in other_chars:
                positions = [i for i, char in enumerate(str_val) if char == c]
                for pos in positions:
                    new_value[pos] = c
                    
            anonymized.append(''.join(new_value))
            
        return pd.Series(anonymized, index=col_data.index)
        
    def _anonymize_emails(self, col_data: pd.Series) -> pd.Series:
        """Anonymize email addresses while preserving domain structure."""
        domains = ["example.com", "sample.org", "anon.net", "test.io", "mock.co"]
        anonymized = []
        
        for value in col_data:
            if pd.isna(value):
                anonymized.append(value)
                continue
                
            str_val = str(value)
            
            # Check if it's an email
            if '@' in str_val:
                username_length = self.random.randint(5, 10)
                username = ''.join(self.random.choices(string.ascii_lowercase, k=username_length))
                domain = self.random.choice(domains)
                anonymized.append(f"{username}@{domain}")
            else:
                # Not an email, randomize text
                anonymized.append(self._random_text(len(str_val)))
                
        return pd.Series(anonymized, index=col_data.index)
        
    def _anonymize_names(self, col_data: pd.Series) -> pd.Series:
        """Anonymize names with realistic substitutes."""
        first_names = ["John", "Jane", "Alex", "Sam", "Chris", "Pat", "Morgan", "Taylor", "Casey"]
        last_names = ["Smith", "Johnson", "Brown", "Davis", "Wilson", "Moore", "Taylor", "Anderson"]
        companies = self.companies
        
        anonymized = []
        
        for value in col_data:
            if pd.isna(value):
                anonymized.append(value)
                continue
                
            str_val = str(value)
            
            # Determine if it looks like a person name or company name
            words = str_val.split()
            
            if len(words) <= 2:
                # Likely a person name
                if len(words) == 1:
                    anonymized.append(self.random.choice(first_names))
                else:
                    anonymized.append(f"{self.random.choice(first_names)} {self.random.choice(last_names)}")
            else:
                # Likely a company name
                anonymized.append(self.random.choice(companies))
                
        return pd.Series(anonymized, index=col_data.index)
        
    def _anonymize_text(self, col_data: pd.Series) -> pd.Series:
        """Anonymize general text data."""
        anonymized = []
        
        for value in col_data:
            if pd.isna(value):
                anonymized.append(value)
                continue
                
            str_val = str(value)
            anonymized.append(self._random_text(len(str_val)))
            
        return pd.Series(anonymized, index=col_data.index)
        
    def _random_date_string(self) -> str:
        """Generate a random date string."""
        year = self.random.randint(2020, 2023)
        month = self.random.randint(1, 12)
        day = self.random.randint(1, 28)
        return f"{month:02d}/{day:02d}/{year}"
        
    def _random_account_number(self) -> str:
        """Generate a random account number."""
        return ''.join(self.random.choices(string.digits, k=self.random.randint(6, 10)))
        
    def _random_text(self, length: int) -> str:
        """Generate random text of a given length."""
        if length <= 0:
            return ""
            
        # For very short strings, use simple random characters
        if length < 5:
            return ''.join(self.random.choices(string.ascii_letters, k=length))
            
        # Choose words to maintain readability
        words = ["item", "service", "product", "unit", "asset", "expense", 
                 "payment", "invoice", "receipt", "account", "order"]
                 
        result = ""
        while len(result) < length:
            result += self.random.choice(words) + " "
            
        return result[:length]