"""
Offline processing orchestrator that combines image processing and metadata storage.
"""
import logging
from pathlib import Path
from typing import Union, List, Optional

from ..models.config import AppConfig
from .image_processor import ImageProcessor
from ..storage.metadata_store import MetadataStore


class OfflineProcessor:
    """
    Orchestrates offline processing of architectural images.
    
    This class combines ImageProcessor and MetadataStore to provide
    a complete offline processing pipeline for architectural images.
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize OfflineProcessor with configuration.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.image_processor = ImageProcessor(config)
        self.metadata_store = MetadataStore(config)
        self.logger = logging.getLogger(__name__)
    
    def process_new_images(self, image_directory: Optional[Union[str, Path]] = None) -> int:
        """
        Process all new or modified images in the configured directory.
        
        Args:
            image_directory: Optional override for image directory
            
        Returns:
            int: Number of images processed
        """
        if image_directory is None:
            image_directory = self.config.image_directory
        
        image_directory = Path(image_directory)
        
        if not image_directory.exists():
            self.logger.error(f"Image directory not found: {image_directory}")
            return 0
        
        # Find images that need processing
        images_to_process = self.metadata_store.get_images_needing_processing(image_directory)
        
        if not images_to_process:
            self.logger.info("No new images to process")
            return 0
        
        self.logger.info(f"Processing {len(images_to_process)} images")
        
        # Process images in batches
        processed_count = 0
        batch_size = self.config.batch_size
        
        for i in range(0, len(images_to_process), batch_size):
            batch_paths = images_to_process[i:i + batch_size]
            
            try:
                # Process batch
                metadata_list = self.image_processor.process_batch_images(batch_paths)
                
                # Save metadata
                if metadata_list:
                    self.metadata_store.save_batch_metadata(metadata_list)
                    processed_count += len(metadata_list)
                
                self.logger.info(f"Processed batch {i//batch_size + 1}: {len(metadata_list)} images")
                
            except Exception as e:
                self.logger.error(f"Failed to process batch {i//batch_size + 1}: {e}")
                continue
        
        self.logger.info(f"Offline processing complete: {processed_count} images processed")
        return processed_count
    
    def reprocess_all_images(self, image_directory: Optional[Union[str, Path]] = None) -> int:
        """
        Reprocess all images in the directory, regardless of existing metadata.
        
        Args:
            image_directory: Optional override for image directory
            
        Returns:
            int: Number of images processed
        """
        if image_directory is None:
            image_directory = self.config.image_directory
        
        image_directory = Path(image_directory)
        
        if not image_directory.exists():
            self.logger.error(f"Image directory not found: {image_directory}")
            return 0
        
        # Process entire directory
        metadata_list = self.image_processor.process_directory(image_directory)
        
        if metadata_list:
            self.metadata_store.save_batch_metadata(metadata_list)
            self.logger.info(f"Reprocessed {len(metadata_list)} images")
            return len(metadata_list)
        
        return 0
    
    def get_processing_status(self) -> dict:
        """
        Get status information about the processing system.
        
        Returns:
            dict: Status information
        """
        storage_stats = self.metadata_store.get_storage_stats()
        processor_stats = self.image_processor.get_processing_stats()
        
        return {
            "storage": storage_stats,
            "processor": processor_stats,
            "config": {
                "image_directory": self.config.image_directory,
                "metadata_file": self.config.metadata_file,
                "batch_size": self.config.batch_size
            }
        }
    
    def cleanup_orphaned_metadata(self) -> int:
        """
        Remove metadata for images that no longer exist.
        
        Returns:
            int: Number of orphaned entries removed
        """
        return self.metadata_store.cleanup_orphaned_metadata(self.config.image_directory)
    
    def cleanup(self):
        """Clean up processor resources."""
        if self.image_processor:
            self.image_processor.cleanup()
        self.logger.info("Offline processor cleaned up")


def main():
    """Example usage of the offline processor."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load configuration
    from ..models.config import AppConfig
    config = AppConfig.load_config()
    
    # Ensure directories exist
    config.ensure_directories_exist()
    
    # Create processor
    processor = OfflineProcessor(config)
    
    try:
        # Process new images
        processed_count = processor.process_new_images()
        print(f"Processed {processed_count} new images")
        
        # Show status
        status = processor.get_processing_status()
        print(f"Total images in storage: {status['storage']['total_images']}")
        
    finally:
        processor.cleanup()


if __name__ == "__main__":
    main()