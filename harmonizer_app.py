import os
import json
import pandas as pd
import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging
import warnings

# Import our modules
from config.providers import ProviderConfig
from core.file_processor import FileProcessor
from transformers.transform_pipeline import TransformPipeline

# Try to import SharePointConnector, but handle the case where shareplum is not available
SHAREPOINT_AVAILABLE = False
try:
    from connectors.sharepoint_connector import SharePointConnector
    SHAREPOINT_AVAILABLE = True
except ImportError:
    warnings.warn("SharePoint integration unavailable: shareplum package not installed")

class FinancialHarmonizer:
    """
    Main application class that orchestrates the entire data harmonization process.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Financial Harmonizer with optional config path.
        
        Args:
            config_path: Path to configuration file
        """
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('FinancialHarmonizer')
        
        # Load config 
        self.config = {}
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        
        # Initialize components
        self.provider_config = ProviderConfig()
        self.file_processor = FileProcessor()
        self.transform_pipeline = TransformPipeline()
        
        # Initialize SharePoint connector if needed and available
        self.sharepoint = None
        sp_config = self.config.get('sharepoint', {})
        if sp_config and SHAREPOINT_AVAILABLE:
            self.sharepoint = SharePointConnector(
                site_url=sp_config.get('site_url', ''),
                username=sp_config.get('username', ''),
                password=sp_config.get('password', ''),
                config_path=sp_config.get('config_path', '')
            )
        elif sp_config and not SHAREPOINT_AVAILABLE:
            self.logger.warning(
                "SharePoint configuration found, but shareplum package is not installed. "
                "SharePoint integration will be disabled."
            )
            
        # Initialize tracking variables
        self.processed_files = []
        self.errors = []
        self.master_data = None
        self.master_log = []
    
    def process_file(self, file_path: Union[str, Path], provider_name: str) -> Dict[str, Any]:
        """
        Process a file with the specified provider configuration.
        
        Args:
            file_path: Path to the file
            provider_name: Name of the provider configuration to use
            
        Returns:
            Dictionary with processing results and logs
        """
        self.logger.info(f"Processing file {file_path} with provider {provider_name}")
        
        try:
            # Get provider settings
            provider_settings = self.provider_config.get_provider_settings(provider_name)
            
            # Process file
            file_result = self.file_processor.process_file(
                file_path=file_path,
                synonyms=provider_settings.get('Synonyms', [])
            )
            
            # Extract data and metadata
            pre_header_text = file_result.get('PreHeaderText', '')
            df = file_result.get('Data', pd.DataFrame())
            logs = file_result.get('Log', [])
            
            # Add file metadata
            file_name = os.path.basename(file_path)
            
            # Apply transformation pipeline
            # 1. Apply synonyms
            synonym_result = self.transform_pipeline.apply_synonyms(
                df=df,
                synonyms=provider_settings.get('Synonyms', [])
            )
            df = synonym_result.get('ResultTable', df)
            logs.extend(synonym_result.get('Log', []))
            
            # 2. Apply filters
            filter_result = self.transform_pipeline.apply_filters(
                df=df,
                filter_settings=provider_settings.get('FilterTable', [])
            )
            df = filter_result.get('ResultTable', df)
            logs.extend(filter_result.get('Log', []))
            
            # 3. Apply calculations
            calc_result = self.transform_pipeline.apply_calculations(
                df=df,
                calculations=provider_settings.get('Calculations', [])
            )
            df = calc_result.get('ResultTable', df)
            logs.extend(calc_result.get('Log', []))
            
            # 4. Apply hardcoded fields
            hardcoded_result = self.transform_pipeline.apply_hardcoded_fields(
                df=df,
                hardcoded_fields=provider_settings.get('HardcodedFields', [])
            )
            df = hardcoded_result.get('ResultTable', df)
            logs.extend(hardcoded_result.get('Log', []))
            
            # 5. Extract values from header text
            extract_result = self.transform_pipeline.extract_values_from_text(
                source_text=pre_header_text,
                field_definitions=provider_settings.get('HeaderExtraction', []),
                df=df
            )
            df = extract_result.get('ResultTable', df)
            logs.extend(extract_result.get('Log', []))
            
            # Add file metadata columns
            df['provider_name'] = provider_name
            df['file_name'] = file_name
            df['processed_date'] = datetime.datetime.now().isoformat()
            
            # Track this file as processed
            self.processed_files.append({
                'file_path': str(file_path),
                'provider_name': provider_name,
                'row_count': len(df),
                'success': True
            })
            
            # Update master data
            if self.master_data is None:
                self.master_data = df
            else:
                self.master_data = pd.concat([self.master_data, df], ignore_index=True)
                
            # Update master log
            self.master_log.extend(logs)
            
            return {
                'success': True,
                'data': df,
                'log': logs,
                'file_name': file_name,
                'provider_name': provider_name,
                'row_count': len(df)
            }
            
        except Exception as e:
            error_msg = f"Error processing file {file_path}: {str(e)}"
            self.logger.error(error_msg)
            
            # Track this file as failed
            self.errors.append({
                'file_path': str(file_path),
                'provider_name': provider_name,
                'error': error_msg
            })
            
            return {
                'success': False,
                'error': error_msg,
                'file_name': os.path.basename(file_path),
                'provider_name': provider_name
            }
    
    def process_directory(self, directory_path: Union[str, Path], provider_mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Process all compatible files in a directory.
        
        Args:
            directory_path: Path to the directory
            provider_mapping: Optional mapping of file patterns to provider names
            
        Returns:
            Summary of processing results
        """
        self.logger.info(f"Processing directory {directory_path}")
        
        directory_path = Path(directory_path)
        if not directory_path.exists() or not directory_path.is_dir():
            error_msg = f"Directory {directory_path} does not exist or is not a directory"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        
        # Default mapping uses filename patterns
        if provider_mapping is None:
            provider_mapping = {}
        
        # Find all Excel and CSV files
        files = list(directory_path.glob("**/*.xlsx"))
        files.extend(directory_path.glob("**/*.xls"))
        files.extend(directory_path.glob("**/*.csv"))
        
        if not files:
            self.logger.warning(f"No compatible files found in {directory_path}")
            return {'success': True, 'processed': 0, 'errors': 0, 'files': []}
        
        processed_count = 0
        error_count = 0
        results = []
        
        for file_path in files:
            file_name = file_path.name
            
            # Determine provider for this file
            provider_name = None
            for pattern, provider in provider_mapping.items():
                if pattern in file_name:
                    provider_name = provider
                    break
            
            # Skip if no provider mapping
            if not provider_name:
                self.logger.warning(f"Skipping file {file_name} - no provider mapping found")
                continue
            
            # Process the file
            result = self.process_file(file_path, provider_name)
            results.append(result)
            
            if result.get('success', False):
                processed_count += 1
            else:
                error_count += 1
        
        return {
            'success': True,
            'processed': processed_count,
            'errors': error_count,
            'total_files': len(files),
            'skipped': len(files) - processed_count - error_count,
            'results': results
        }
    
    def process_sharepoint_folder(self, folder_path: str, provider_mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Process files from a SharePoint folder.
        
        Args:
            folder_path: Path to SharePoint folder
            provider_mapping: Optional mapping of file patterns to provider names
            
        Returns:
            Summary of processing results
        """
        if not SHAREPOINT_AVAILABLE:
            error_msg = "SharePoint integration unavailable: shareplum package not installed"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
            
        if not self.sharepoint:
            error_msg = "SharePoint connector not configured"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
            
        self.logger.info(f"Processing SharePoint folder {folder_path}")
        
        # Get files from SharePoint
        result = self.sharepoint.get_files(
            folder_path=folder_path,
            file_extensions=['.xlsx', '.xls', '.csv']
        )
        
        files = result.get('Files', [])
        logs = result.get('Log', [])
        self.master_log.extend(logs)
        
        if not files:
            self.logger.warning(f"No compatible files found in SharePoint folder {folder_path}")
            return {'success': True, 'processed': 0, 'errors': 0, 'files': []}
        
        # Default mapping uses filename patterns
        if provider_mapping is None:
            provider_mapping = {}
        
        # Create a temp directory for files
        import tempfile
        temp_dir = tempfile.mkdtemp()
        
        processed_count = 0
        error_count = 0
        results = []
        
        for file_info in files:
            file_name = file_info.get('Name', '')
            content = file_info.get('Content')
            
            if not content:
                self.logger.warning(f"Skipping file {file_name} - no content")
                continue
            
            # Determine provider for this file
            provider_name = None
            for pattern, provider in provider_mapping.items():
                if pattern in file_name:
                    provider_name = provider
                    break
            
            # Skip if no provider mapping
            if not provider_name:
                self.logger.warning(f"Skipping file {file_name} - no provider mapping found")
                continue
            
            # Save file temporarily
            temp_file_path = os.path.join(temp_dir, file_name)
            with open(temp_file_path, 'wb') as f:
                f.write(content)
            
            # Process the file
            result = self.process_file(temp_file_path, provider_name)
            results.append(result)
            
            # Clean up temp file
            try:
                os.remove(temp_file_path)
            except:
                pass
            
            if result.get('success', False):
                processed_count += 1
            else:
                error_count += 1
        
        # Clean up temp dir
        try:
            os.rmdir(temp_dir)
        except:
            pass
        
        return {
            'success': True,
            'processed': processed_count,
            'errors': error_count,
            'total_files': len(files),
            'skipped': len(files) - processed_count - error_count,
            'results': results
        }
    
    def export_results(self, output_path: str, format: str = 'csv') -> Dict[str, Any]:
        """
        Export harmonized data to a file.
        
        Args:
            output_path: Path to save the output file
            format: Output format ('csv' or 'excel')
            
        Returns:
            Export status
        """
        if self.master_data is None or self.master_data.empty:
            return {'success': False, 'error': 'No data to export'}
        
        try:
            if format.lower() == 'csv':
                self.master_data.to_csv(output_path, index=False)
            elif format.lower() == 'excel':
                self.master_data.to_excel(output_path, index=False)
            else:
                return {'success': False, 'error': f'Unsupported format: {format}'}
            
            # Export logs to a separate file
            log_path = output_path + '.log.json'
            with open(log_path, 'w') as f:
                json.dump(self.master_log, f, indent=2)
                
            return {
                'success': True,
                'path': output_path,
                'log_path': log_path,
                'rows': len(self.master_data),
                'columns': len(self.master_data.columns)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all processing operations.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            'files_processed': len(self.processed_files),
            'errors': len(self.errors),
            'total_rows': len(self.master_data) if self.master_data is not None else 0,
            'processed_files': self.processed_files,
            'error_files': self.errors,
            'log_entries': len(self.master_log)
        }
