"""
Metadata storage system for efficient persistence and retrieval of image embeddings and descriptions.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Union, Set
from datetime import datetime
import numpy as np
import hashlib
import os

from ..models.config import AppConfig
from ..models.image_metadata import ImageMetadata


class MetadataStore:
    """
    Manages JSON-based persistence of image metadata with efficient storage and retrieval.
    
    This class handles:
    - JSON-based metadata storage and loading
    - Efficient embedding storage and retrieval
    - Incremental processing to handle new images
    - Data integrity and validation
    - Backup and recovery functionality
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize MetadataStore with configuration.
        
        Args:
            config: Application configuration containing storage settings
        """
        self.config = config
        self.metadata_file = Path(config.metadata_file)
        self.logger = logging.getLogger(__name__)
        
        # In-memory cache for loaded metadata
        self._metadata_cache: Dict[str, ImageMetadata] = {}
        self._cache_loaded = False
        self._last_modified = None
        
        # Ensure storage directory exists
        self._ensure_storage_directory()
    
    def _ensure_storage_directory(self):
        """Create storage directory if it doesn't exist."""
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _get_file_hash(self, file_path: Union[str, Path]) -> str:
        """
        Generate hash for file to detect changes.
        
        Args:
            file_path: Path to file
            
        Returns:
            str: MD5 hash of file content and modification time
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return ""
        
        try:
            # Combine file size and modification time for quick change detection
            stat = file_path.stat()
            content = f"{stat.st_size}_{stat.st_mtime}_{file_path}"
            return hashlib.md5(content.encode()).hexdigest()
        except Exception as e:
            self.logger.warning(f"Failed to generate hash for {file_path}: {e}")
            return ""
    
    def _load_metadata_from_file(self) -> Dict[str, ImageMetadata]:
        """
        Load metadata from JSON file.
        
        Returns:
            Dict[str, ImageMetadata]: Dictionary mapping image paths to metadata
            
        Raises:
            ValueError: If file format is invalid
        """
        if not self.metadata_file.exists():
            self.logger.info(f"Metadata file not found: {self.metadata_file}")
            return {}
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate file format
            if not isinstance(data, dict) or 'images' not in data:
                raise ValueError("Invalid metadata file format")
            
            metadata_dict = {}
            
            for item in data['images']:
                try:
                    metadata = ImageMetadata.from_dict(item)
                    metadata_dict[metadata.path] = metadata
                except Exception as e:
                    self.logger.warning(f"Failed to load metadata item: {e}")
                    continue
            
            self.logger.info(f"Loaded {len(metadata_dict)} metadata entries from {self.metadata_file}")
            return metadata_dict
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in metadata file: {e}")
            raise ValueError(f"Corrupted metadata file: {e}")
        except Exception as e:
            self.logger.error(f"Failed to load metadata file: {e}")
            raise ValueError(f"Could not load metadata: {e}")
    
    def _save_metadata_to_file(self, metadata_dict: Dict[str, ImageMetadata]):
        """
        Save metadata dictionary to JSON file.
        
        Args:
            metadata_dict: Dictionary of metadata to save
            
        Raises:
            ValueError: If saving fails
        """
        try:
            # Create backup if file exists
            if self.metadata_file.exists():
                backup_path = self.metadata_file.with_suffix('.json.backup')
                self.metadata_file.replace(backup_path)
                self.logger.debug(f"Created backup: {backup_path}")
            
            # Prepare data for JSON serialization
            data = {
                'version': '1.0',
                'created': datetime.now().isoformat(),
                'total_images': len(metadata_dict),
                'images': [metadata.to_dict() for metadata in metadata_dict.values()]
            }
            
            # Write to temporary file first, then rename for atomic operation
            temp_file = self.metadata_file.with_suffix('.json.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_file.replace(self.metadata_file)
            
            self.logger.info(f"Saved {len(metadata_dict)} metadata entries to {self.metadata_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save metadata file: {e}")
            # Clean up temporary file if it exists
            temp_file = self.metadata_file.with_suffix('.json.tmp')
            if temp_file.exists():
                temp_file.unlink()
            raise ValueError(f"Could not save metadata: {e}")
    
    def _refresh_cache_if_needed(self):
        """Refresh cache if metadata file has been modified."""
        if not self.metadata_file.exists():
            if self._cache_loaded:
                self._metadata_cache.clear()
                self._cache_loaded = False
            return
        
        try:
            current_modified = self.metadata_file.stat().st_mtime
            
            if not self._cache_loaded or self._last_modified != current_modified:
                self._metadata_cache = self._load_metadata_from_file()
                self._cache_loaded = True
                self._last_modified = current_modified
                self.logger.debug("Metadata cache refreshed")
                
        except Exception as e:
            self.logger.warning(f"Failed to refresh cache: {e}")
    
    def load_all_metadata(self) -> Dict[str, ImageMetadata]:
        """
        Load all metadata from storage.
        
        Returns:
            Dict[str, ImageMetadata]: Dictionary mapping image paths to metadata
        """
        self._refresh_cache_if_needed()
        return self._metadata_cache.copy()
    
    def save_metadata(self, metadata: ImageMetadata):
        """
        Save single metadata entry to storage.
        
        Args:
            metadata: ImageMetadata to save
        """
        self._refresh_cache_if_needed()
        
        # Update cache
        self._metadata_cache[metadata.path] = metadata
        
        # Save to file
        self._save_metadata_to_file(self._metadata_cache)
        
        self.logger.debug(f"Saved metadata for {metadata.path}")
    
    def save_batch_metadata(self, metadata_list: List[ImageMetadata]):
        """
        Save multiple metadata entries efficiently.
        
        Args:
            metadata_list: List of ImageMetadata to save
        """
        if not metadata_list:
            return
        
        self._refresh_cache_if_needed()
        
        # Update cache with all new metadata
        for metadata in metadata_list:
            self._metadata_cache[metadata.path] = metadata
        
        # Save to file once
        self._save_metadata_to_file(self._metadata_cache)
        
        self.logger.info(f"Saved batch of {len(metadata_list)} metadata entries")
    
    def get_metadata(self, image_path: Union[str, Path]) -> Optional[ImageMetadata]:
        """
        Get metadata for a specific image.
        
        Args:
            image_path: Path to the image
            
        Returns:
            Optional[ImageMetadata]: Metadata if found, None otherwise
        """
        self._refresh_cache_if_needed()
        return self._metadata_cache.get(str(image_path))
    
    def has_metadata(self, image_path: Union[str, Path]) -> bool:
        """
        Check if metadata exists for an image.
        
        Args:
            image_path: Path to the image
            
        Returns:
            bool: True if metadata exists
        """
        self._refresh_cache_if_needed()
        return str(image_path) in self._metadata_cache
    
    def remove_metadata(self, image_path: Union[str, Path]):
        """
        Remove metadata for a specific image.
        
        Args:
            image_path: Path to the image
        """
        self._refresh_cache_if_needed()
        
        image_path_str = str(image_path)
        if image_path_str in self._metadata_cache:
            del self._metadata_cache[image_path_str]
            self._save_metadata_to_file(self._metadata_cache)
            self.logger.info(f"Removed metadata for {image_path}")
        else:
            self.logger.warning(f"No metadata found for {image_path}")
    
    def get_images_needing_processing(self, image_directory: Union[str, Path]) -> List[Path]:
        """
        Find images that need processing (new or modified since last processing).
        
        Args:
            image_directory: Directory containing images
            
        Returns:
            List[Path]: List of image paths that need processing
        """
        image_directory = Path(image_directory)
        
        if not image_directory.exists():
            self.logger.warning(f"Image directory not found: {image_directory}")
            return []
        
        self._refresh_cache_if_needed()
        
        # Supported image extensions
        supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        
        # Find all image files
        image_files = []
        for ext in supported_extensions:
            image_files.extend(image_directory.rglob(f"*{ext}"))
            image_files.extend(image_directory.rglob(f"*{ext.upper()}"))
        
        # Remove duplicates
        image_files = list(set(image_files))
        
        # Check which images need processing
        images_to_process = []
        
        for image_path in image_files:
            image_path_str = str(image_path)
            
            # Check if metadata exists
            if image_path_str not in self._metadata_cache:
                images_to_process.append(image_path)
                continue
            
            # Check if image has been modified since processing
            try:
                metadata = self._metadata_cache[image_path_str]
                image_stat = image_path.stat()
                
                # Compare modification times
                if metadata.processed_date:
                    image_modified = datetime.fromtimestamp(image_stat.st_mtime)
                    if image_modified > metadata.processed_date:
                        images_to_process.append(image_path)
                        continue
                
                # Check if file size changed
                if metadata.file_size and metadata.file_size != image_stat.st_size:
                    images_to_process.append(image_path)
                    continue
                    
            except Exception as e:
                self.logger.warning(f"Failed to check modification for {image_path}: {e}")
                # Include in processing if we can't determine status
                images_to_process.append(image_path)
        
        self.logger.info(f"Found {len(images_to_process)} images needing processing out of {len(image_files)} total")
        return images_to_process
    
    def get_all_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Get all embeddings for efficient similarity calculations.
        
        Returns:
            Dict[str, np.ndarray]: Dictionary mapping image paths to embeddings
        """
        self._refresh_cache_if_needed()
        
        embeddings = {}
        for path, metadata in self._metadata_cache.items():
            if metadata.embedding is not None:
                embeddings[path] = metadata.embedding
        
        return embeddings
    
    def get_storage_stats(self) -> Dict[str, any]:
        """
        Get statistics about the metadata storage.
        
        Returns:
            dict: Storage statistics
        """
        self._refresh_cache_if_needed()
        
        stats = {
            'total_images': len(self._metadata_cache),
            'metadata_file': str(self.metadata_file),
            'file_exists': self.metadata_file.exists(),
            'cache_loaded': self._cache_loaded
        }
        
        if self.metadata_file.exists():
            try:
                file_stat = self.metadata_file.stat()
                stats.update({
                    'file_size_bytes': file_stat.st_size,
                    'file_size_mb': round(file_stat.st_size / (1024 * 1024), 2),
                    'last_modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                })
            except Exception as e:
                self.logger.warning(f"Failed to get file stats: {e}")
        
        # Calculate embedding statistics
        if self._metadata_cache:
            embeddings = [m.embedding for m in self._metadata_cache.values() if m.embedding is not None]
            if embeddings:
                embedding_sizes = [len(emb) for emb in embeddings]
                stats.update({
                    'embedding_dimension': embedding_sizes[0] if embedding_sizes else 0,
                    'total_embeddings': len(embeddings),
                    'avg_features_per_image': round(
                        sum(len(m.features) for m in self._metadata_cache.values()) / len(self._metadata_cache), 1
                    )
                })
        
        return stats
    
    def cleanup_orphaned_metadata(self, image_directory: Union[str, Path]) -> int:
        """
        Remove metadata for images that no longer exist.
        
        Args:
            image_directory: Directory containing images
            
        Returns:
            int: Number of orphaned entries removed
        """
        image_directory = Path(image_directory)
        self._refresh_cache_if_needed()
        
        orphaned_paths = []
        
        for image_path in self._metadata_cache.keys():
            path = Path(image_path)
            
            # Check if path is within the image directory and exists
            try:
                if not path.exists() or not path.is_relative_to(image_directory):
                    orphaned_paths.append(image_path)
            except Exception:
                # is_relative_to might not be available in older Python versions
                if not path.exists():
                    orphaned_paths.append(image_path)
        
        # Remove orphaned entries
        for path in orphaned_paths:
            del self._metadata_cache[path]
        
        if orphaned_paths:
            self._save_metadata_to_file(self._metadata_cache)
            self.logger.info(f"Removed {len(orphaned_paths)} orphaned metadata entries")
        
        return len(orphaned_paths)
    
    def create_backup(self, backup_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Create a backup of the metadata file.
        
        Args:
            backup_path: Optional custom backup path
            
        Returns:
            Path: Path to the created backup file
            
        Raises:
            ValueError: If backup creation fails
        """
        if not self.metadata_file.exists():
            raise ValueError("No metadata file to backup")
        
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.metadata_file.with_name(f"{self.metadata_file.stem}_{timestamp}.json")
        else:
            backup_path = Path(backup_path)
        
        try:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            import shutil
            shutil.copy2(self.metadata_file, backup_path)
            
            self.logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            raise ValueError(f"Backup creation failed: {e}")
    
    def restore_from_backup(self, backup_path: Union[str, Path]):
        """
        Restore metadata from a backup file.
        
        Args:
            backup_path: Path to backup file
            
        Raises:
            ValueError: If restore fails
        """
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            raise ValueError(f"Backup file not found: {backup_path}")
        
        try:
            # Validate backup file
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, dict) or 'images' not in data:
                raise ValueError("Invalid backup file format")
            
            # Create backup of current file if it exists
            if self.metadata_file.exists():
                current_backup = self.metadata_file.with_suffix('.json.pre_restore')
                self.metadata_file.replace(current_backup)
                self.logger.info(f"Current file backed up to: {current_backup}")
            
            # Copy backup to metadata file
            import shutil
            shutil.copy2(backup_path, self.metadata_file)
            
            # Clear cache to force reload
            self._metadata_cache.clear()
            self._cache_loaded = False
            
            self.logger.info(f"Restored metadata from backup: {backup_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to restore from backup: {e}")
            raise ValueError(f"Restore failed: {e}")