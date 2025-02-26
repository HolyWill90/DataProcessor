import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

class ProviderConfig:
    """Manages provider configurations with caching for performance."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize with optional config directory path."""
        self.config_dir = config_dir or os.path.join(os.path.dirname(__file__), 'providers')
        self.providers_cache = {}
        self._load_providers()
    
    def _load_providers(self) -> None:
        """Load all provider configurations from the config directory."""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        # Load from JSON files in the config directory
        for file_path in Path(self.config_dir).glob('*.json'):
            try:
                with open(file_path, 'r') as f:
                    provider_data = json.load(f)
                    if 'ProviderName' in provider_data:
                        self.providers_cache[provider_data['ProviderName'].upper()] = provider_data
            except Exception as e:
                print(f"Error loading provider config {file_path}: {e}")
                
        # Also load from YAML files
        for file_path in Path(self.config_dir).glob('*.yaml'):
            try:
                with open(file_path, 'r') as f:
                    provider_data = yaml.safe_load(f)
                    if 'ProviderName' in provider_data:
                        self.providers_cache[provider_data['ProviderName'].upper()] = provider_data
            except Exception as e:
                print(f"Error loading provider config {file_path}: {e}")
    
    def get_provider_settings(self, provider_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific provider.
        
        Args:
            provider_name: Name of the provider to retrieve
            
        Returns:
            Provider configuration as a dictionary
            
        Raises:
            ValueError: If provider name is invalid or provider not found
        """
        if not provider_name or not provider_name.strip():
            raise ValueError("Provider name cannot be null or empty")
        
        provider_name = provider_name.strip().upper()
        
        # Check cache first
        if provider_name in self.providers_cache:
            return self.providers_cache[provider_name]
        
        # If not in cache, maybe config was added since initialization
        self._load_providers()
        
        if provider_name in self.providers_cache:
            return self.providers_cache[provider_name]
        
        raise ValueError(f"No matching provider found for: {provider_name}")
    
    def save_provider(self, provider_config: Dict[str, Any]) -> None:
        """Save or update a provider configuration."""
        if 'ProviderName' not in provider_config:
            raise ValueError("Provider config must include 'ProviderName'")
            
        provider_name = provider_config['ProviderName']
        file_path = os.path.join(self.config_dir, f"{provider_name}.json")
        
        with open(file_path, 'w') as f:
            json.dump(provider_config, f, indent=2)
            
        # Update cache
        self.providers_cache[provider_name.upper()] = provider_config
