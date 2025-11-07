"""
Configuration settings for the AI Architectural Search System
"""
import os
import logging
from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class AppConfig:
    """Application configuration with default settings"""
    
    # Directory paths
    image_directory: str = "images/"
    metadata_file: str = "image_metadata.json"
    
    # Search settings
    max_results: int = 5
    similarity_threshold: float = 0.1
    
    # Model settings
    clip_model_name: str = "ViT-B/32"
    
    # Performance settings
    batch_size: int = 32
    max_image_size: Tuple[int, int] = (512, 512)
    
    # Web interface settings
    page_title: str = "AI Architectural Search"
    page_icon: str = "🏗️"
    
    # Cloud deployment settings
    environment: str = "development"  # development, staging, production
    debug_mode: bool = False
    log_level: str = "INFO"
    
    # Resource optimization for cloud
    enable_model_caching: bool = True
    memory_optimization: bool = False
    cpu_only_mode: bool = False
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Load configuration from environment variables with defaults"""
        # Parse max_image_size from environment
        max_size_str = os.getenv('MAX_IMAGE_SIZE', '512,512')
        try:
            width, height = map(int, max_size_str.split(','))
            max_image_size = (width, height)
        except (ValueError, AttributeError):
            max_image_size = (512, 512)
        
        # Parse boolean environment variables
        def parse_bool(value: Optional[str], default: bool) -> bool:
            if value is None:
                return default
            return value.lower() in ('true', '1', 'yes', 'on')
        
        return cls(
            # File paths
            image_directory=os.getenv('IMAGE_DIRECTORY', 'images/'),
            metadata_file=os.getenv('METADATA_FILE', 'image_metadata.json'),
            
            # Search settings
            max_results=int(os.getenv('MAX_RESULTS', '5')),
            similarity_threshold=float(os.getenv('SIMILARITY_THRESHOLD', '0.1')),
            
            # Model settings
            clip_model_name=os.getenv('CLIP_MODEL_NAME', 'ViT-B/32'),
            
            # Performance settings
            batch_size=int(os.getenv('BATCH_SIZE', '32')),
            max_image_size=max_image_size,
            
            # Web interface
            page_title=os.getenv('PAGE_TITLE', 'AI Architectural Search'),
            page_icon=os.getenv('PAGE_ICON', '🏗️'),
            
            # Cloud deployment
            environment=os.getenv('ENVIRONMENT', 'development'),
            debug_mode=parse_bool(os.getenv('DEBUG_MODE'), False),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            
            # Resource optimization
            enable_model_caching=parse_bool(os.getenv('ENABLE_MODEL_CACHING'), True),
            memory_optimization=parse_bool(os.getenv('MEMORY_OPTIMIZATION'), False),
            cpu_only_mode=parse_bool(os.getenv('CPU_ONLY_MODE'), False)
        )
    
    def validate(self) -> None:
        """Validate configuration values"""
        if self.max_results <= 0:
            raise ValueError("max_results must be positive")
        if not 0 <= self.similarity_threshold <= 1:
            raise ValueError("similarity_threshold must be between 0 and 1")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.environment not in ['development', 'staging', 'production']:
            raise ValueError("environment must be development, staging, or production")
        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            raise ValueError("log_level must be DEBUG, INFO, WARNING, or ERROR")
        
        # Create directories if they don't exist
        if not os.path.exists(self.image_directory):
            os.makedirs(self.image_directory, exist_ok=True)
    
    def configure_logging(self) -> None:
        """Configure logging based on environment settings"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        if self.environment == 'production':
            # Production logging - structured format
            logging.basicConfig(
                level=getattr(logging, self.log_level),
                format=log_format,
                handlers=[
                    logging.StreamHandler(),
                    logging.FileHandler('app.log') if os.access('.', os.W_OK) else logging.StreamHandler()
                ]
            )
        else:
            # Development/staging logging - console only
            logging.basicConfig(
                level=getattr(logging, self.log_level),
                format=log_format,
                handlers=[logging.StreamHandler()]
            )
    
    def get_optimization_settings(self) -> dict:
        """Get optimization settings for cloud deployment"""
        return {
            'memory_optimization': self.memory_optimization,
            'cpu_only_mode': self.cpu_only_mode,
            'enable_caching': self.enable_model_caching,
            'batch_size': self.batch_size if not self.memory_optimization else min(self.batch_size, 16),
            'max_image_size': self.max_image_size if not self.memory_optimization else (256, 256)
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == 'development'


# Factory function for configuration
def get_config() -> AppConfig:
    """Get configuration instance based on environment"""
    config = AppConfig.from_env()
    config.validate()
    config.configure_logging()
    return config


# Default configuration instance
config = get_config()