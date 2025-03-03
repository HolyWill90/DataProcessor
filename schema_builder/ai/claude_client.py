"""
Claude API client for schema generation.

This module provides a client for the Claude API to generate provider schemas
from anonymized data samples.
"""
import os
import json
import requests
import time
from typing import Dict, List, Any, Optional, Union
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClaudeClient:
    """
    Client for the Claude API for schema generation.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        """
        Initialize the Claude API client.
        
        Args:
            api_key: API key for Claude API
            model: Claude model to use
        """
        self.api_key = api_key or os.environ.get("CLAUDE_API_KEY")
        if not self.api_key:
            logger.warning("No Claude API key provided. Running in offline mode.")
            
        self.model = model
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
    def generate_schema(self, prompt: str) -> str:
        """
        Generate a schema using the Claude API.
        
        Args:
            prompt: Prompt for schema generation
            
        Returns:
            Generated schema as JSON string
        """
        if not self.api_key:
            # Return a mock response in offline mode
            logger.info("Running in offline mode. Returning mock schema.")
            return self._get_mock_response()
            
        # Make API request
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Limit the prompt size to avoid context length issues
        if len(prompt) > 80000:  # Reduce from Claude's max limit to leave room for response
            logger.warning(f"Prompt length ({len(prompt)} chars) exceeds recommended limit. Truncating.")
            # Preserve the beginning instructions and schema format examples
            instruction_part = prompt[:5000]  # Keep the first instructions
            # Find the data sample start/end
            data_start = prompt.find("```json")
            data_end = prompt.find("```", data_start + 6)
            if data_start > 0 and data_end > data_start:
                # Truncate the data part to fit within limits
                max_data_size = 40000  # Adjust as needed
                data_part = prompt[data_start:data_start + max_data_size]
                if data_part.count('{') != data_part.count('}'):
                    # Ensure valid JSON by finding the last complete object
                    last_complete = data_part.rfind('},')
                    if last_complete > 0:
                        data_part = data_part[:last_complete+2] + "\n  ...]}"
                end_part = prompt[data_end:]
                prompt = instruction_part + data_part + end_part
                logger.info(f"Prompt truncated to {len(prompt)} chars")
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4000
        }
        
        # Try the request with retries
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Making API request (attempt {attempt + 1})")
                response = requests.post(
                    self.api_url, 
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    # Successfully got a response
                    response_data = response.json()
                    text_response = response_data.get("content", [{"text": ""}])[0].get("text", "")
                    return text_response
                elif response.status_code == 429:
                    # Rate limit error - wait and retry
                    logger.warning("Rate limited. Waiting before retry.")
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    # Other error
                    logger.error(f"API error: {response.status_code} - {response.text}")
                    # Try again if not the last attempt
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                    else:
                        # Last attempt failed, return mock
                        logger.warning("API calls failed. Falling back to mock response.")
                        return self._get_mock_response()
                        
            except Exception as e:
                logger.error(f"Error calling Claude API: {e}")
                # Try again if not the last attempt
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    # Last attempt failed, return mock
                    logger.warning("API calls failed. Falling back to mock response.")
                    return self._get_mock_response()
        
        # If we get here, all retries failed
        return self._get_mock_response()
        
    def _get_mock_response(self) -> str:
        """
        Get a mock response for offline mode.
        
        Returns:
            Mock schema as JSON string
        """
        mock_schema = {
            "ProviderName": "MockProvider",
            "Synonyms": [
                {
                    "LogicalField": "date",
                    "AlternateNames": ["Date", "Transaction Date", "Invoice Date", "Due Date"]
                },
                {
                    "LogicalField": "amount",
                    "AlternateNames": ["Amount", "Total", "Invoice Amount", "Payment Amount"]
                },
                {
                    "LogicalField": "description",
                    "AlternateNames": ["Description", "Details", "Narrative", "Item Description"]
                },
                {
                    "LogicalField": "reference",
                    "AlternateNames": ["Reference", "Invoice Number", "Transaction ID", "Document Number"]
                }
            ],
            "FilterTable": [
                "[amount] <> 0",
                "[description] <> null"
            ],
            "Calculations": [
                {
                    "NewField": "gst_amount",
                    "Expression": "([amount] * 0.15)"
                },
                {
                    "NewField": "excl_gst_amount",
                    "Expression": "([amount] - [gst_amount])"
                }
            ],
            "HardcodedFields": [
                {
                    "FieldName": "provider",
                    "Value": "MockProvider"
                },
                {
                    "FieldName": "currency",
                    "Value": "USD"
                }
            ]
        }
        
        return json.dumps(mock_schema, indent=2)