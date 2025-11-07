"""
Configuration management for the AI architectural search system.
"""
import os
import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from pathlib import Path


@dataclass
class AppConfig:
    """
    Application configuration with default settings and validation.
    
    Attributes:
        image_directory: Directory containing architectural images
        metadata_file: Path to JSON file storing image metadata
        max_results: Maximum number of search results to return
        similarity_threshold: Minimum similarity score for results
        clip_model_name: Name of the CLIP model to use
        batch_size: Number of images to process in each batch
        cache_embeddings: Whether to cache embeddings for performance
        web_port: Port for Streamlit web interface
        web_host: Host address for web interface
    """
    image_directory: str = "images/"
    metadata_file: str = "image_metadata.json"
    max_results: int = 5
    similarity_threshold: float = 0.1
    clip_model_name: str = "ViT-B/32"
    batch_size: int = 10
    cache_embeddings: bool = True
    web_port: int = 8501
    web_host: str = "localhost"
    
    def __post_init__(self):
        """Validate configuration values after initialization."""
        self._validate_config()
    
    def _validate_config(self):
        """Validate all configuration values."""
        # Validate image directory
        if not isinstance(self.image_directory, str) or not self.image_directory.strip():
            raise ValueError("Image directory must be a non-empty string")
        
        # Validate metadata file
        if not isinstance(self.metadata_file, str) or not self.metadata_file.strip():
            raise ValueError("Metadata file must be a non-empty string")
        
        # Validate max results
        if not isinstance(self.max_results, int) or self.max_results <= 0:
            raise ValueError("Max results must be a positive integer")
        
        # Validate similarity threshold
        if not isinstance(self.similarity_threshold, (int, float)):
            raise TypeError("Similarity threshold must be a number")
        if not (0 <= self.similarity_threshold <= 1):
            raise ValueError("Similarity threshold must be between 0 and 1")
        
        # Validate CLIP model name
        if not isinstance(self.clip_model_name, str) or not self.clip_model_name.strip():
            raise ValueError("CLIP model name must be a non-empty string")
        
        # Validate batch size
        if not isinstance(self.batch_size, int) or self.batch_size <= 0:
            raise ValueError("Batch size must be a positive integer")
        
        # Validate cache embeddings
        if not isinstance(self.cache_embeddings, bool):
            raise TypeError("Cache embeddings must be a boolean")
        
        # Validate web port
        if not isinstance(self.web_port, int) or not (1 <= self.web_port <= 65535):
            raise ValueError("Web port must be an integer between 1 and 65535")
        
        # Validate web host
        if not isinstance(self.web_host, str) or not self.web_host.strip():
            raise ValueError("Web host must be a non-empty string")
    
    def get_image_directory_path(self) -> Path:
        """Get Path object for image directory."""
        return Path(self.image_directory)
    
    def get_metadata_file_path(self) -> Path:
        """Get Path object for metadata file."""
        return Path(self.metadata_file)
    
    def ensure_directories_exist(self):
        """Create necessary directories if they don't exist."""
        img_dir = self.get_image_directory_path()
        if not img_dir.exists():
            img_dir.mkdir(parents=True, exist_ok=True)
        
        # Create metadata file directory if needed
        metadata_dir = self.get_metadata_file_path().parent
        if not metadata_dir.exists():
            metadata_dir.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """
        Create AppConfig from dictionary.
        
        Args:
            data: Dictionary containing configuration values
            
        Returns:
            AppConfig instance with validated values
        """
        # Filter out unknown keys
        valid_keys = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        
        return cls(**filtered_data)
    
    def save_to_file(self, config_path: str):
        """
        Save configuration to JSON file.
        
        Args:
            config_path: Path to save configuration file
        """
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, config_path: str) -> 'AppConfig':
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            AppConfig instance loaded from file
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file contains invalid JSON
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def load_from_env(cls) -> 'AppConfig':
        """
        Load configuration from environment variables.
        
        Environment variables should be prefixed with 'AI_SEARCH_'
        For example: AI_SEARCH_IMAGE_DIRECTORY, AI_SEARCH_MAX_RESULTS
        
        Returns:
            AppConfig instance with values from environment
        """
        env_mapping = {
            'AI_SEARCH_IMAGE_DIRECTORY': 'image_directory',
            'AI_SEARCH_METADATA_FILE': 'metadata_file',
            'AI_SEARCH_MAX_RESULTS': 'max_results',
            'AI_SEARCH_SIMILARITY_THRESHOLD': 'similarity_threshold',
            'AI_SEARCH_CLIP_MODEL_NAME': 'clip_model_name',
            'AI_SEARCH_BATCH_SIZE': 'batch_size',
            'AI_SEARCH_CACHE_EMBEDDINGS': 'cache_embeddings',
            'AI_SEARCH_WEB_PORT': 'web_port',
            'AI_SEARCH_WEB_HOST': 'web_host',
        }
        
        config_data = {}
        
        for env_var, config_key in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if config_key in ['max_results', 'batch_size', 'web_port']:
                    try:
                        config_data[config_key] = int(value)
                    except ValueError:
                        raise ValueError(f"Invalid integer value for {env_var}: {value}")
                elif config_key == 'similarity_threshold':
                    try:
                        config_data[config_key] = float(value)
                    except ValueError:
                        raise ValueError(f"Invalid float value for {env_var}: {value}")
                elif config_key == 'cache_embeddings':
                    config_data[config_key] = value.lower() in ('true', '1', 'yes', 'on')
                else:
                    config_data[config_key] = value
        
        return cls.from_dict(config_data)
    
    @classmethod
    def load_config(cls, config_path: Optional[str] = None, 
                   use_env: bool = True) -> 'AppConfig':
        """
        Load configuration with fallback priority: file -> environment -> defaults.
        
        Args:
            config_path: Optional path to configuration file
            use_env: Whether to load from environment variables
            
        Returns:
            AppConfig instance with merged configuration
        """
        # Start with defaults
        config = cls()
        
        # Override with environment variables if requested
        if use_env:
            try:
                env_config = cls.load_from_env()
                # Merge non-default values from environment
                for key, value in env_config.to_dict().items():
                    setattr(config, key, value)
            except Exception:
                # Continue with defaults if environment loading fails
                pass
        
        # Override with file configuration if provided
        if config_path:
            try:
                file_config = cls.load_from_file(config_path)
                # Merge values from file
                for key, value in file_config.to_dict().items():
                    setattr(config, key, value)
            except FileNotFoundError:
                # Continue with current config if file doesn't exist
                pass
        
        # Validate final configuration
        config._validate_config()
        return config


def get_default_config() -> AppConfig:
    """Get default application configuration."""
    return AppConfig()


def load_config_with_fallbacks(config_file: str = "config.json") -> AppConfig:
    """
    Load configuration with standard fallback behavior.
    
    Args:
        config_file: Name of configuration file to look for
        
    Returns:
        AppConfig instance with loaded configuration
    """
    return AppConfig.load_config(config_path=config_file, use_env=True)