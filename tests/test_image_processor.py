"""
Unit tests for image processing components.
Tests CLIP model integration, metadata serialization, and batch processing.
"""
import unittest
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import numpy as np
import json
from datetime import datetime

from src.models.config import AppConfig
from src.models.image_metadata import ImageMetadata
from src.processors.image_processor import ImageProcessor
from src.processors.model_manager import ModelManager
from src.storage.metadata_store import MetadataStore


class TestImageProcessor(unittest.TestCase):
    """Test cases for ImageProcessor class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        # Create temporary directory for test files
        cls.test_dir = Path(tempfile.mkdtemp())
        cls.images_dir = cls.test_dir / "images"
        cls.images_dir.mkdir()
        
        # Create test configuration
        cls.config = AppConfig(
            image_directory=str(cls.images_dir),
            metadata_file=str(cls.test_dir / "test_metadata.json"),
            batch_size=2
        )
        
        # Create sample test images
        cls._create_test_images()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures."""
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)
    
    @classmethod
    def _create_test_images(cls):
        """Create sample images for testing."""
        # Create different colored test images
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green  
            (0, 0, 255),    # Blue
            (128, 128, 128) # Gray
        ]
        
        cls.test_image_paths = []
        
        for i, color in enumerate(colors):
            # Create a simple colored rectangle image
            img = Image.new('RGB', (224, 224), color)
            image_path = cls.images_dir / f"test_image_{i}.jpg"
            img.save(image_path, 'JPEG')
            cls.test_image_paths.append(image_path)
    
    def setUp(self):
        """Set up for each test."""
        self.processor = ImageProcessor(self.config)
    
    def tearDown(self):
        """Clean up after each test."""
        if hasattr(self.processor, 'cleanup'):
            self.processor.cleanup()


class TestCLIPModelIntegration(TestImageProcessor):
    """Test CLIP model integration with sample images."""
    
    def test_model_loading(self):
        """Test that CLIP model loads successfully."""
        model_manager = ModelManager(self.config)
        
        # Check model is loaded
        self.assertIsNotNone(model_manager.model)
        self.assertIsNotNone(model_manager.preprocess)
        
        # Check model info
        info = model_manager.get_model_info()
        self.assertEqual(info['status'], 'loaded')
        self.assertIn('parameter_count', info)
        
        model_manager.cleanup()
    
    def test_image_embedding_generation(self):
        """Test CLIP embedding generation for sample images."""
        test_image = self.test_image_paths[0]
        
        # Generate embedding
        embedding = self.processor.model_manager.generate_image_embedding(test_image)
        
        # Validate embedding properties
        self.assertIsInstance(embedding, np.ndarray)
        self.assertEqual(len(embedding.shape), 1)  # Should be 1D array
        self.assertGreater(len(embedding), 0)  # Should have elements
        
        # Check embedding is normalized (approximately unit length)
        norm = np.linalg.norm(embedding)
        self.assertAlmostEqual(norm, 1.0, places=5)
    
    def test_text_embedding_generation(self):
        """Test CLIP text embedding generation."""
        test_text = "red brick building with large windows"
        
        # Generate embedding
        embedding = self.processor.model_manager.generate_text_embedding(test_text)
        
        # Validate embedding properties
        self.assertIsInstance(embedding, np.ndarray)
        self.assertEqual(len(embedding.shape), 1)  # Should be 1D array
        self.assertGreater(len(embedding), 0)  # Should have elements
        
        # Check embedding is normalized
        norm = np.linalg.norm(embedding)
        self.assertAlmostEqual(norm, 1.0, places=5)
    
    def test_similarity_calculation(self):
        """Test similarity calculation between embeddings."""
        # Generate embeddings for two images
        embedding1 = self.processor.model_manager.generate_image_embedding(self.test_image_paths[0])
        embedding2 = self.processor.model_manager.generate_image_embedding(self.test_image_paths[1])
        
        # Calculate similarity
        similarity = self.processor.model_manager.calculate_similarity(embedding1, embedding2)
        
        # Validate similarity score
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, -1.0)
        self.assertLessEqual(similarity, 1.0)
    
    def test_image_preprocessing(self):
        """Test image preprocessing pipeline."""
        test_image = self.test_image_paths[0]
        
        # Preprocess image
        processed = self.processor.model_manager.preprocess_image(test_image)
        
        # Validate processed tensor
        self.assertEqual(len(processed.shape), 4)  # Batch dimension included
        self.assertEqual(processed.shape[0], 1)    # Batch size 1
        self.assertEqual(processed.shape[1], 3)    # RGB channels


class TestMetadataSerializationAndStorage(TestImageProcessor):
    """Test metadata serialization and storage functionality."""
    
    def test_single_image_processing(self):
        """Test processing a single image and creating metadata."""
        test_image = self.test_image_paths[0]
        
        # Process image
        metadata = self.processor.process_single_image(test_image)
        
        # Validate metadata structure
        self.assertIsInstance(metadata, ImageMetadata)
        self.assertEqual(metadata.path, str(test_image))
        self.assertIsInstance(metadata.embedding, np.ndarray)
        self.assertIsInstance(metadata.description, str)
        self.assertIsInstance(metadata.features, list)
        self.assertGreater(len(metadata.description), 0)
        self.assertGreater(len(metadata.features), 0)
    
    def test_metadata_serialization(self):
        """Test metadata serialization to/from dictionary."""
        test_image = self.test_image_paths[0]
        
        # Create metadata
        original_metadata = self.processor.process_single_image(test_image)
        
        # Serialize to dictionary
        metadata_dict = original_metadata.to_dict()
        
        # Validate dictionary structure
        self.assertIsInstance(metadata_dict, dict)
        self.assertIn('path', metadata_dict)
        self.assertIn('embedding', metadata_dict)
        self.assertIn('description', metadata_dict)
        self.assertIn('features', metadata_dict)
        
        # Deserialize from dictionary
        restored_metadata = ImageMetadata.from_dict(metadata_dict)
        
        # Validate restored metadata
        self.assertEqual(restored_metadata.path, original_metadata.path)
        self.assertEqual(restored_metadata.description, original_metadata.description)
        self.assertEqual(restored_metadata.features, original_metadata.features)
        np.testing.assert_array_equal(restored_metadata.embedding, original_metadata.embedding)
    
    def test_metadata_store_operations(self):
        """Test metadata store save and load operations."""
        store = MetadataStore(self.config)
        test_image = self.test_image_paths[0]
        
        # Create and save metadata
        metadata = self.processor.process_single_image(test_image)
        store.save_metadata(metadata)
        
        # Load metadata
        loaded_metadata = store.get_metadata(test_image)
        
        # Validate loaded metadata
        self.assertIsNotNone(loaded_metadata)
        self.assertEqual(loaded_metadata.path, metadata.path)
        self.assertEqual(loaded_metadata.description, metadata.description)
        np.testing.assert_array_equal(loaded_metadata.embedding, metadata.embedding)
    
    def test_batch_metadata_storage(self):
        """Test batch metadata storage operations."""
        store = MetadataStore(self.config)
        
        # Process multiple images
        metadata_list = []
        for image_path in self.test_image_paths[:3]:
            metadata = self.processor.process_single_image(image_path)
            metadata_list.append(metadata)
        
        # Save batch
        store.save_batch_metadata(metadata_list)
        
        # Load all metadata
        all_metadata = store.load_all_metadata()
        
        # Validate batch storage
        self.assertEqual(len(all_metadata), 3)
        for metadata in metadata_list:
            self.assertIn(metadata.path, all_metadata)


class TestBatchProcessing(TestImageProcessor):
    """Test batch processing functionality."""
    
    def test_batch_image_processing(self):
        """Test batch processing of multiple images."""
        # Process batch of images
        metadata_list = self.processor.process_batch_images(self.test_image_paths[:3])
        
        # Validate batch results
        self.assertEqual(len(metadata_list), 3)
        
        for metadata in metadata_list:
            self.assertIsInstance(metadata, ImageMetadata)
            self.assertIsInstance(metadata.embedding, np.ndarray)
            self.assertIsInstance(metadata.description, str)
            self.assertGreater(len(metadata.features), 0)
    
    def test_directory_processing(self):
        """Test processing entire directory of images."""
        # Process directory
        metadata_list = self.processor.process_directory(self.images_dir)
        
        # Validate directory processing
        self.assertEqual(len(metadata_list), len(self.test_image_paths))
        
        # Check all images were processed
        processed_paths = {metadata.path for metadata in metadata_list}
        expected_paths = {str(path) for path in self.test_image_paths}
        self.assertEqual(processed_paths, expected_paths)
    
    def test_batch_embedding_generation(self):
        """Test batch embedding generation efficiency."""
        # Generate embeddings in batch
        embeddings = self.processor.model_manager.generate_batch_image_embeddings(
            self.test_image_paths[:3]
        )
        
        # Validate batch embeddings
        self.assertEqual(len(embeddings), 3)
        
        for embedding in embeddings:
            self.assertIsInstance(embedding, np.ndarray)
            self.assertEqual(len(embedding.shape), 1)
            
            # Check normalization
            norm = np.linalg.norm(embedding)
            self.assertAlmostEqual(norm, 1.0, places=5)
    
    def test_incremental_processing(self):
        """Test incremental processing of new images."""
        store = MetadataStore(self.config)
        
        # Process first batch
        first_batch = self.test_image_paths[:2]
        metadata_list = self.processor.process_batch_images(first_batch)
        store.save_batch_metadata(metadata_list)
        
        # Check which images need processing
        images_needing_processing = store.get_images_needing_processing(self.images_dir)
        
        # Should find remaining unprocessed images
        unprocessed_paths = {str(path) for path in self.test_image_paths[2:]}
        found_paths = {str(path) for path in images_needing_processing}
        
        self.assertTrue(unprocessed_paths.issubset(found_paths))


class TestErrorHandling(TestImageProcessor):
    """Test error handling in image processing."""
    
    def test_invalid_image_path(self):
        """Test handling of invalid image paths."""
        invalid_path = self.test_dir / "nonexistent.jpg"
        
        with self.assertRaises(FileNotFoundError):
            self.processor.process_single_image(invalid_path)
    
    def test_empty_directory_processing(self):
        """Test processing empty directory."""
        empty_dir = self.test_dir / "empty"
        empty_dir.mkdir()
        
        metadata_list = self.processor.process_directory(empty_dir)
        self.assertEqual(len(metadata_list), 0)
    
    def test_invalid_embedding_similarity(self):
        """Test similarity calculation with invalid embeddings."""
        embedding1 = np.array([1.0, 0.0, 0.0])
        embedding2 = np.array([1.0, 0.0])  # Different shape
        
        with self.assertRaises(ValueError):
            self.processor.model_manager.calculate_similarity(embedding1, embedding2)


if __name__ == '__main__':
    unittest.main()