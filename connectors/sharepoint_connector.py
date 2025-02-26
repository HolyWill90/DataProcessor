import os
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import pandas as pd
import json
import datetime
import warnings

# Handle missing shareplum gracefully
SHAREPLUM_AVAILABLE = False
try:
    from shareplum import Site, Office365
    from shareplum.site import Version
    SHAREPLUM_AVAILABLE = True
except ImportError:
    warnings.warn("SharePoint integration unavailable: shareplum package not installed")

class SharePointConnector:
    """Connector for retrieving files and metadata from SharePoint."""
    
    def __init__(self, site_url: str, username: Optional[str] = None, password: Optional[str] = None, config_path: Optional[str] = None):
        """
        Initialize SharePoint connector.
        
        Args:
            site_url: SharePoint site URL
            username: SharePoint username (if not using config file)
            password: SharePoint password (if not using config file)
            config_path: Path to config file with credentials (alternative to username/password)
        """
        self.site_url = site_url
        self.username = username
        self.password = password
        self.config_path = config_path
        self.connection = None
        self.site = None
        self.log_entries = []
        
        if not SHAREPLUM_AVAILABLE:
            self.create_log_entry(
                "Initialize", 
                "SharePointConnector", 
                "SharePoint integration unavailable", 
                "Please install shareplum package: pip install shareplum"
            )
        
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
    
    def connect(self) -> bool:
        """
        Connect to SharePoint site.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not SHAREPLUM_AVAILABLE:
            self.create_log_entry(
                "Connect", 
                "SharePointConnector", 
                "SharePoint integration unavailable", 
                "Please install shareplum package: pip install shareplum"
            )
            return False
            
        try:
            # Try to load credentials from config if provided
            if self.config_path and os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.username = config.get('username', self.username)
                    self.password = config.get('password', self.password)
            
            # Validate credentials
            if not self.username or not self.password:
                self.create_log_entry(
                    "Connect", 
                    "SharePointConnector", 
                    "Missing credentials", 
                    "Username and password must be provided either directly or via config file"
                )
                return False
            
            # Connect using Office365 auth
            auth_site = self.site_url
            authcookie = Office365(auth_site, username=self.username, password=self.password).GetCookie()
            self.site = Site(self.site_url, version=Version.v365, authcookie=authcookie)
            
            self.create_log_entry(
                "Connect", 
                "SharePointConnector", 
                f"Connected to {self.site_url}", 
                "Success"
            )
            return True
            
        except Exception as e:
            self.create_log_entry(
                "Connect", 
                "SharePointConnector", 
                f"Failed to connect to {self.site_url}", 
                str(e)
            )
            return False
    
    def get_files(self, folder_path: str, file_extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get files from a SharePoint folder.
        
        Args:
            folder_path: Path to folder within SharePoint site
            file_extensions: Optional list of file extensions to filter by
            
        Returns:
            Dictionary with:
                - Files: List of file info dictionaries
                - Log: Operation logs
        """
        if not SHAREPLUM_AVAILABLE:
            self.create_log_entry(
                "Get Files", 
                "SharePointConnector", 
                "SharePoint integration unavailable", 
                "Please install shareplum package: pip install shareplum"
            )
            return {"Files": [], "Log": self.log_entries}
        
        if not self.site:
            success = self.connect()
            if not success:
                return {"Files": [], "Log": self.log_entries}
        
        try:
            # Get folder
            folder = self.site.Folder(folder_path)
            
            # Get files
            files = folder.files
            
            # Filter by extension if specified
            if file_extensions:
                file_extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in file_extensions]
                filtered_files = []
                for file_info in files:
                    name = file_info.get('Name', '')
                    _, ext = os.path.splitext(name)
                    if ext.lower() in file_extensions:
                        filtered_files.append(file_info)
                files = filtered_files
            
            # Add file content
            for file_info in files:
                name = file_info.get('Name', '')
                try:
                    file_content = folder.get_file(name)
                    file_info['Content'] = file_content
                    file_info['Extension'] = os.path.splitext(name)[1].lower()
                    file_info['FolderPath'] = folder_path
                except Exception as e:
                    file_info['Content'] = None
                    file_info['Error'] = str(e)
            
            self.create_log_entry(
                "Get Files", 
                "SharePointConnector", 
                f"Retrieved {len(files)} files from {folder_path}", 
                "Success"
            )
            
            return {"Files": files, "Log": self.log_entries}
            
        except Exception as e:
            self.create_log_entry(
                "Get Files", 
                "SharePointConnector", 
                f"Failed to retrieve files from {folder_path}", 
                str(e)
            )
            return {"Files": [], "Log": self.log_entries}
    
    def get_list_items(self, list_name: str, query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get items from a SharePoint list.
        
        Args:
            list_name: Name of SharePoint list
            query: Optional CAML query parameters
            
        Returns:
            Dictionary with:
                - Items: List of items
                - Log: Operation logs
        """
        if not SHAREPLUM_AVAILABLE:
            self.create_log_entry(
                "Get List Items", 
                "SharePointConnector", 
                "SharePoint integration unavailable", 
                "Please install shareplum package: pip install shareplum"
            )
            return {"Items": [], "Log": self.log_entries}
        
        if not self.site:
            success = self.connect()
            if not success:
                return {"Items": [], "Log": self.log_entries}
        
        try:
            # Get list
            sp_list = self.site.List(list_name)
            
            # Get items with query if specified
            if query:
                items = sp_list.GetListItems(query)
            else:
                items = sp_list.GetListItems()
            
            self.create_log_entry(
                "Get List Items", 
                "SharePointConnector", 
                f"Retrieved {len(items)} items from list {list_name}", 
                "Success"
            )
            
            return {"Items": items, "Log": self.log_entries}
            
        except Exception as e:
            self.create_log_entry(
                "Get List Items", 
                "SharePointConnector", 
                f"Failed to retrieve items from list {list_name}", 
                str(e)
            )
            return {"Items": [], "Log": self.log_entries}
