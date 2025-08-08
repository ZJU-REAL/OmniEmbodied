#!/usr/bin/env python3
"""
Download Expert Trajectory Data for OmniEAR
Downloads expert trajectory data from HuggingFace Hub for supervised fine-tuning
"""

import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from huggingface_hub import snapshot_download, login
from datasets import load_dataset
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExpertDataDownloader:
    """Downloads expert trajectory data from HuggingFace Hub"""
    
    def __init__(self, config_path: str = "hf_config.yaml"):
        """Initialize downloader with configuration
        
        Args:
            config_path: Path to HuggingFace configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.repo_id = f"{self.config['repository']['organization']}/{self.config['repository']['dataset_name']}"
        self.local_path = Path(__file__).parent
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)
            
    def check_authentication(self) -> bool:
        """Check if user is authenticated with HuggingFace"""
        try:
            from huggingface_hub import whoami
            user_info = whoami()
            logger.info(f"Authenticated as: {user_info['name']}")
            return True
        except Exception:
            logger.warning("Not authenticated with HuggingFace Hub")
            return False
            
    def authenticate(self) -> None:
        """Authenticate with HuggingFace Hub"""
        if not self.check_authentication():
            logger.info("Please authenticate with HuggingFace Hub")
            try:
                login()
                logger.info("Authentication successful")
            except Exception as e:
                logger.error(f"Authentication failed: {e}")
                logger.info("You can also set HF_TOKEN environment variable")
                sys.exit(1)
                
    def download_dataset(self, force_download: bool = False) -> None:
        """Download the expert trajectory dataset
        
        Args:
            force_download: Whether to force re-download existing files
        """
        logger.info(f"Downloading dataset from {self.repo_id}")
        
        try:
            # Download using snapshot_download for better control
            download_path = snapshot_download(
                repo_id=self.repo_id,
                repo_type="dataset",
                local_dir=self.local_path,
                local_dir_use_symlinks=False,
                force_download=force_download
            )
            
            logger.info(f"Dataset downloaded successfully to: {download_path}")
            
        except Exception as e:
            logger.error(f"Failed to download dataset: {e}")
            logger.info("Trying alternative download method...")
            
            try:
                # Alternative: Use datasets library
                dataset = load_dataset(self.repo_id)
                logger.info("Dataset loaded successfully using datasets library")
                return dataset
                
            except Exception as e2:
                logger.error(f"Alternative download also failed: {e2}")
                sys.exit(1)
                
    def verify_download(self) -> bool:
        """Verify that the download was successful"""
        logger.info("Verifying download...")
        
        # Check for expected directories
        single_agent_dir = self.local_path / "single_agent"
        centralized_agent_dir = self.local_path / "centralized_agent"
        
        if not single_agent_dir.exists():
            logger.error("single_agent directory not found")
            return False
            
        if not centralized_agent_dir.exists():
            logger.error("centralized_agent directory not found") 
            return False
            
        # Count files
        single_agent_files = len(list(single_agent_dir.glob("*.json")))
        centralized_agent_files = len(list(centralized_agent_dir.glob("*.json")))
        total_files = single_agent_files + centralized_agent_files
        
        logger.info(f"Found {single_agent_files} single-agent files")
        logger.info(f"Found {centralized_agent_files} centralized-agent files") 
        logger.info(f"Total files: {total_files}")
        
        # Verify file count matches expected
        expected_total = 1982  # Based on dataset description
        if total_files != expected_total:
            logger.warning(f"File count mismatch: expected {expected_total}, found {total_files}")
            
        # Verify file format
        return self._verify_file_format()
        
    def _verify_file_format(self) -> bool:
        """Verify that downloaded files have correct JSON format"""
        logger.info("Verifying file formats...")
        
        sample_files = []
        single_agent_dir = self.local_path / "single_agent"
        centralized_agent_dir = self.local_path / "centralized_agent"
        
        # Get sample files from each directory
        if single_agent_dir.exists():
            sample_files.extend(list(single_agent_dir.glob("*.json"))[:3])
        if centralized_agent_dir.exists():
            sample_files.extend(list(centralized_agent_dir.glob("*.json"))[:3])
            
        required_fields = self.config.get('validation', {}).get('required_fields', [])
        
        for file_path in sample_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Check required fields
                for field in required_fields:
                    if field not in data:
                        logger.error(f"Missing required field '{field}' in {file_path}")
                        return False
                        
            except Exception as e:
                logger.error(f"Invalid JSON format in {file_path}: {e}")
                return False
                
        logger.info("File format verification passed")
        return True
        
    def print_usage_example(self) -> None:
        """Print usage examples after successful download"""
        logger.info("\n" + "="*50)
        logger.info("Download completed successfully!")
        logger.info("="*50)
        
        print(f"""
Usage Examples:

1. Load with HuggingFace datasets:
   from datasets import load_dataset
   dataset = load_dataset("{self.repo_id}")

2. Load locally:
   import json
   from pathlib import Path
   
   # Load single-agent data
   single_agent_files = Path("single_agent").glob("*.json")
   for file_path in single_agent_files:
       with open(file_path) as f:
           data = json.load(f)
           
3. Use for fine-tuning:
   # See README.md for complete fine-tuning examples
   
Data structure:
- single_agent/: 1,262 single-agent reasoning tasks
- centralized_agent/: 720 multi-agent collaboration tasks
- Total: 1,982 expert trajectory samples
""")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download OmniEAR expert trajectory data")
    parser.add_argument("--force", action="store_true", help="Force re-download existing files")
    parser.add_argument("--config", default="hf_config.yaml", help="Path to configuration file")
    parser.add_argument("--no-auth", action="store_true", help="Skip authentication (for public datasets)")
    
    args = parser.parse_args()
    
    # Initialize downloader
    downloader = ExpertDataDownloader(args.config)
    
    # Authenticate if needed
    if not args.no_auth:
        downloader.authenticate()
    
    # Download dataset
    downloader.download_dataset(force_download=args.force)
    
    # Verify download
    if downloader.verify_download():
        downloader.print_usage_example()
    else:
        logger.error("Download verification failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
