#!/usr/bin/env python3
"""
Configuration Management for Daily Financial Summary Agent
Handles environment variables, API key validation, and logging setup.
"""

import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration class for the finance agent."""
    
    def __init__(self):
        """Initialize configuration by loading environment variables."""
        self.project_root = Path(__file__).parent.parent
        self.load_environment()
        self.setup_logging()
        self.validate_config()
    
    def load_environment(self):
        """Load environment variables from .env file."""
        env_path = self.project_root / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            logging.info(f"Loaded environment from {env_path}")
        else:
            logging.warning("No .env file found. Using system environment variables.")
    
    def setup_logging(self):
        """Configure logging for the application."""
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
            ]
        )
        
        # Suppress verbose logs from external libraries
        logging.getLogger('anthropic').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    def validate_config(self):
        """Validate required configuration values."""
        if not self.anthropic_api_key:
            self._show_api_key_setup_help()
            sys.exit(1)
        
        if len(self.anthropic_api_key) < 20:
            logging.error("ANTHROPIC_API_KEY appears to be invalid (too short)")
            sys.exit(1)
        
        logging.info("Configuration validation successful")
    
    @property
    def anthropic_api_key(self) -> str:
        """Get the Anthropic API key from environment."""
        return os.getenv('ANTHROPIC_API_KEY', '')
    
    @property
    def data_dir(self) -> Path:
        """Get the data directory path."""
        return self.project_root / 'data'
    
    @property
    def reports_dir(self) -> Path:
        """Get the reports directory path."""
        return self.project_root / 'reports'
    
    @property
    def transactions_file(self) -> Path:
        """Get the transactions CSV file path."""
        return self.data_dir / 'transactions.csv'
    
    @property
    def sample_transactions_file(self) -> Path:
        """Get the sample transactions CSV file path."""
        return self.data_dir / 'sample_transactions.csv'
    
    def _show_api_key_setup_help(self):
        """Display helpful instructions for API key setup."""
        print("\n❌ Missing ANTHROPIC_API_KEY")
        print("\n🔧 Setup Instructions:")
        print("1. Get your API key from: https://console.anthropic.com/")
        print("2. Copy .env.example to .env:")
        print("   cp .env.example .env")
        print("3. Add your API key to .env:")
        print("   ANTHROPIC_API_KEY=your_api_key_here")
        print("4. Rebuild the Docker container:")
        print("   docker-compose build")
        print("\n💡 Make sure your .env file is in the project root directory.")


# Global configuration instance
config = Config()