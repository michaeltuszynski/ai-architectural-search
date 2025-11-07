"""
Image processing and analysis for architectural feature extraction and description generation.
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
from PIL import Image
import numpy as np
from datetime import datetime

from ..models.config import AppConfig
from ..models.image_metadata import ImageMetadata
from .model_manager import ModelManager


class ImageProcessor:
    """
    Processes architectural images to extract features and generate descriptions.
    
    This class handles:
    - Batch processing of image directories
    - Feature extraction using CLIP embeddings
    - Automatic description generation for architectural elements
    - Image validation and preprocessing
    """
    
    # Architectural feature templates for description generation
    ARCHITECTURAL_FEATURES = {
        'materials': [
            'red brick', 'brown brick', 'white brick', 'brick facade',
            'stone facade', 'limestone', 'granite', 'marble',
            'glass facade', 'steel and glass', 'curtain wall',
            'concrete', 'exposed concrete', 'stucco', 'wood siding'
        ],
        'roof_types': [
            'flat roof', 'pitched roof', 'gabled roof', 'hip roof',
            'mansard roof', 'shed roof', 'curved roof', 'dome'
        ],
        'window_styles': [
            'large windows', 'floor-to-ceiling windows', 'bay windows',
            'arched windows', 'rectangular windows', 'ribbon windows',
            'small windows', 'symmetrical windows'
        ],
        'architectural_elements': [
            'columns', 'pillars', 'arches', 'balconies', 'terraces',
            'entrance canopy', 'portico', 'cornice', 'pediment',
            'decorative elements', 'geometric patterns'
        ],
        'building_types': [
            'residential building', 'commercial building', 'office building',
            'institutional building', 'mixed-use building', 'high-rise',
            'low-rise', 'mid-rise', 'single-family house', 'apartment building'
        ]
    }
    
    # Common architectural description templates
    DESCRIPTION_TEMPLATES = [
        "{material} {building_type} with {roof_type} and {window_style}",
        "{building_type} featuring {material} facade and {architectural_element}",
        "Modern {building_type} with {material} and {window_style}",
        "{material} building with {architectural_element} and {roof_type}",
        "Contemporary {building_type} featuring {material} facade"
    ]
    
    def __init__(self, config: AppConfig):
        """
        Initialize ImageProcessor with configuration and model manager.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.model_manager = ModelManager(config)
        self.logger = logging.getLogger(__name__)
        
        # Supported image formats
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    
    def _is_valid_image(self, image_path: Path) -> bool:
        """
        Check if file is a valid image format.
        
        Args:
            image_path: Path to image file
            
        Returns:
            bool: True if valid image format
        """
        return image_path.suffix.lower() in self.supported_formats
    
    def _get_image_info(self, image_path: Path) -> Tuple[int, Tuple[int, int]]:
        """
        Get basic image information (file size and dimensions).
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple[int, Tuple[int, int]]: File size in bytes and (width, height)
            
        Raises:
            ValueError: If image cannot be opened
        """
        try:
            file_size = image_path.stat().st_size
            
            with Image.open(image_path) as img:
                dimensions = img.size  # (width, height)
            
            return file_size, dimensions
            
        except Exception as e:
            self.logger.error(f"Failed to get image info for {image_path}: {e}")
            raise ValueError(f"Could not read image information: {e}")
    
    def _extract_features_from_embedding(self, embedding: np.ndarray, 
                                       image_path: Path) -> List[str]:
        """
        Extract architectural features by comparing embedding with feature templates.
        
        Args:
            embedding: CLIP embedding for the image
            image_path: Path to the image (for context)
            
        Returns:
            List[str]: List of detected architectural features
        """
        features = []
        
        try:
            # Generate embeddings for architectural feature terms
            all_features = []
            for category, feature_list in self.ARCHITECTURAL_FEATURES.items():
                all_features.extend(feature_list)
            
            # Calculate similarities with feature terms
            feature_similarities = {}
            
            for feature in all_features:
                try:
                    feature_embedding = self.model_manager.generate_text_embedding(feature)
                    similarity = self.model_manager.calculate_similarity(embedding, feature_embedding)
                    feature_similarities[feature] = similarity
                except Exception as e:
                    self.logger.debug(f"Failed to process feature '{feature}': {e}")
                    continue
            
            # Select top features above threshold
            similarity_threshold = 0.25  # Adjust based on testing
            top_features = sorted(
                feature_similarities.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            # Take top 3-5 features above threshold
            for feature, similarity in top_features[:5]:
                if similarity > similarity_threshold:
                    features.append(feature)
            
            # Ensure we have at least some features
            if not features and top_features:
                # Take the top feature even if below threshold
                features.append(top_features[0][0])
            
            self.logger.debug(f"Extracted features for {image_path.name}: {features}")
            
        except Exception as e:
            self.logger.warning(f"Feature extraction failed for {image_path}: {e}")
            # Fallback to basic features based on filename or directory
            features = self._extract_fallback_features(image_path)
        
        return features
    
    def _extract_fallback_features(self, image_path: Path) -> List[str]:
        """
        Extract basic features from filename and directory structure as fallback.
        
        Args:
            image_path: Path to the image
            
        Returns:
            List[str]: Basic features based on path analysis
        """
        features = []
        
        # Analyze directory name
        parent_dir = image_path.parent.name.lower()
        if 'brick' in parent_dir:
            features.append('brick facade')
        elif 'glass' in parent_dir or 'steel' in parent_dir:
            features.append('glass facade')
        elif 'stone' in parent_dir:
            features.append('stone facade')
        elif 'mixed' in parent_dir:
            features.append('mixed materials')
        
        # Analyze filename
        filename = image_path.stem.lower()
        if 'residential' in filename or 'house' in filename:
            features.append('residential building')
        elif 'commercial' in filename or 'office' in filename:
            features.append('commercial building')
        
        # Default features if none found
        if not features:
            features = ['building facade', 'architectural structure']
        
        return features
    
    def _generate_description(self, features: List[str], image_path: Path) -> str:
        """
        Generate human-readable description from extracted features.
        
        Args:
            features: List of architectural features
            image_path: Path to the image
            
        Returns:
            str: Generated description
        """
        try:
            # Categorize features
            materials = [f for f in features if any(m in f for m in 
                        ['brick', 'stone', 'glass', 'steel', 'concrete', 'wood'])]
            roof_types = [f for f in features if 'roof' in f]
            window_styles = [f for f in features if 'window' in f]
            building_types = [f for f in features if 'building' in f or 'house' in f]
            architectural_elements = [f for f in features if f not in materials + roof_types + window_styles + building_types]
            
            # Select primary elements for description
            material = materials[0] if materials else "modern"
            building_type = building_types[0] if building_types else "building"
            roof_type = roof_types[0] if roof_types else "contemporary roofline"
            window_style = window_styles[0] if window_styles else "well-proportioned windows"
            architectural_element = architectural_elements[0] if architectural_elements else "clean lines"
            
            # Choose template and generate description
            import random
            template = random.choice(self.DESCRIPTION_TEMPLATES)
            
            description = template.format(
                material=material,
                building_type=building_type,
                roof_type=roof_type,
                window_style=window_style,
                architectural_element=architectural_element
            )
            
            # Capitalize first letter
            description = description[0].upper() + description[1:]
            
            self.logger.debug(f"Generated description for {image_path.name}: {description}")
            return description
            
        except Exception as e:
            self.logger.warning(f"Description generation failed for {image_path}: {e}")
            # Fallback description
            return f"Architectural building with {', '.join(features[:3]) if features else 'distinctive features'}"
    
    def process_single_image(self, image_path: Union[str, Path]) -> ImageMetadata:
        """
        Process a single image to extract metadata, features, and description.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            ImageMetadata: Complete metadata for the image
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image processing fails
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        if not self._is_valid_image(image_path):
            raise ValueError(f"Unsupported image format: {image_path.suffix}")
        
        self.logger.info(f"Processing image: {image_path}")
        
        try:
            # Get basic image information
            file_size, dimensions = self._get_image_info(image_path)
            
            # Generate CLIP embedding
            embedding = self.model_manager.generate_image_embedding(image_path)
            
            # Extract architectural features
            features = self._extract_features_from_embedding(embedding, image_path)
            
            # Generate description
            description = self._generate_description(features, image_path)
            
            # Create metadata object
            metadata = ImageMetadata(
                path=str(image_path),
                embedding=embedding,
                description=description,
                features=features,
                file_size=file_size,
                dimensions=dimensions,
                processed_date=datetime.now()
            )
            
            self.logger.info(f"Successfully processed {image_path}")
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to process image {image_path}: {e}")
            raise ValueError(f"Image processing failed: {e}")
    
    def process_directory(self, directory_path: Union[str, Path], 
                         recursive: bool = True) -> List[ImageMetadata]:
        """
        Process all images in a directory and return metadata list.
        
        Args:
            directory_path: Path to directory containing images
            recursive: Whether to process subdirectories
            
        Returns:
            List[ImageMetadata]: List of metadata for all processed images
            
        Raises:
            FileNotFoundError: If directory doesn't exist
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        self.logger.info(f"Processing directory: {directory_path} (recursive={recursive})")
        
        # Find all image files
        image_files = []
        
        if recursive:
            for ext in self.supported_formats:
                image_files.extend(directory_path.rglob(f"*{ext}"))
                image_files.extend(directory_path.rglob(f"*{ext.upper()}"))
        else:
            for ext in self.supported_formats:
                image_files.extend(directory_path.glob(f"*{ext}"))
                image_files.extend(directory_path.glob(f"*{ext.upper()}"))
        
        # Remove duplicates and sort
        image_files = sorted(list(set(image_files)))
        
        self.logger.info(f"Found {len(image_files)} image files")
        
        if not image_files:
            self.logger.warning(f"No image files found in {directory_path}")
            return []
        
        # Process images
        metadata_list = []
        processed_count = 0
        failed_count = 0
        
        for image_path in image_files:
            try:
                metadata = self.process_single_image(image_path)
                metadata_list.append(metadata)
                processed_count += 1
                
                # Log progress
                if processed_count % 10 == 0:
                    self.logger.info(f"Processed {processed_count}/{len(image_files)} images")
                    
            except Exception as e:
                failed_count += 1
                self.logger.warning(f"Failed to process {image_path}: {e}")
                continue
        
        self.logger.info(f"Directory processing complete: {processed_count} successful, {failed_count} failed")
        return metadata_list
    
    def process_batch_images(self, image_paths: List[Union[str, Path]]) -> List[ImageMetadata]:
        """
        Process a batch of images with optimized embedding generation.
        
        Args:
            image_paths: List of paths to image files
            
        Returns:
            List[ImageMetadata]: List of metadata for successfully processed images
        """
        if not image_paths:
            return []
        
        self.logger.info(f"Processing batch of {len(image_paths)} images")
        
        # Filter valid image paths
        valid_paths = []
        for path in image_paths:
            path = Path(path)
            if path.exists() and self._is_valid_image(path):
                valid_paths.append(path)
            else:
                self.logger.warning(f"Skipping invalid image: {path}")
        
        if not valid_paths:
            self.logger.warning("No valid images found in batch")
            return []
        
        metadata_list = []
        
        try:
            # Generate embeddings in batch for efficiency
            embeddings = self.model_manager.generate_batch_image_embeddings(valid_paths)
            
            # Process each image with its embedding
            for i, (image_path, embedding) in enumerate(zip(valid_paths, embeddings)):
                try:
                    # Get basic image information
                    file_size, dimensions = self._get_image_info(image_path)
                    
                    # Extract features and generate description
                    features = self._extract_features_from_embedding(embedding, image_path)
                    description = self._generate_description(features, image_path)
                    
                    # Create metadata
                    metadata = ImageMetadata(
                        path=str(image_path),
                        embedding=embedding,
                        description=description,
                        features=features,
                        file_size=file_size,
                        dimensions=dimensions,
                        processed_date=datetime.now()
                    )
                    
                    metadata_list.append(metadata)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to process metadata for {image_path}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Batch processing failed, falling back to individual processing: {e}")
            # Fallback to individual processing
            for image_path in valid_paths:
                try:
                    metadata = self.process_single_image(image_path)
                    metadata_list.append(metadata)
                except Exception as individual_error:
                    self.logger.warning(f"Failed to process {image_path}: {individual_error}")
                    continue
        
        self.logger.info(f"Batch processing complete: {len(metadata_list)} images processed")
        return metadata_list
    
    def get_processing_stats(self) -> Dict[str, any]:
        """
        Get statistics about the image processor and model.
        
        Returns:
            dict: Processing statistics and model information
        """
        return {
            "model_info": self.model_manager.get_model_info(),
            "supported_formats": list(self.supported_formats),
            "batch_size": self.config.batch_size,
            "feature_categories": list(self.ARCHITECTURAL_FEATURES.keys()),
            "total_features": sum(len(features) for features in self.ARCHITECTURAL_FEATURES.values())
        }
    
    def cleanup(self):
        """Clean up processor resources."""
        if self.model_manager:
            self.model_manager.cleanup()
        self.logger.info("Image processor cleaned up")