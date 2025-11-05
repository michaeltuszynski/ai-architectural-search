"""
Unit tests for search functionality components.
Tests query embedding generation, similarity calculations, and result ranking.
"""
import unittest
import tempfile
import shutil
from pathlib import Path
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch

from src.models.config import AppConfig
from src.models.search_models import Query, SearchResult
from src.models.image_metadata import ImageMetadata
from src.processors.query_processor import QueryProcessor
from src.processors.result_ranker import ResultRanker
from src.processors.search_engine import SearchEngine
from src.processors.model_manager import ModelManager


class TestQueryEmbeddingGeneration(unittest.TestCase):
    """Test query embedding generation accuracy."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        cls.test_dir = Path(tempfile.mkdtemp())
        cls.config = AppConfig(
            image_directory=str(cls.test_dir / "images"),
            metadata_file=str(cls.test_dir / "metadata.json")
        )
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures."""
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)
    
    def setUp(self):
        """Set up for each test."""
        # Mock ModelManager to avoid loading actual CLIP model
        self.mock_model_manager = Mock(spec=ModelManager)
        self.query_processor = QueryProcessor(self.config, self.mock_model_manager)
    
    def test_query_text_validation(self):
        """Test query text validation and normalization."""
        # Test empty query
        with self.assertRaises(ValueError):
            self.query_processor._validate_and_normalize_query("")
        
        # Test whitespace-only query
        with self.assertRaises(ValueError):
            self.query_processor._validate_and_normalize_query("   ")
        
        # Test non-string query
        with self.assertRaises(ValueError):
            self.query_processor._validate_and_normalize_query(123)
        
        # Test too short query
        with self.assertRaises(ValueError):
            self.query_processor._validate_and_normalize_query("a")
        
        # Test valid query normalization
        normalized = self.query_processor._validate_and_normalize_query("  Red Brick Building  ")
        self.assertEqual(normalized, "Red Brick Building")
        
        # Test long query truncation
        long_query = "a" * 250
        normalized = self.query_processor._validate_and_normalize_query(long_query)
        self.assertEqual(len(normalized), 200)
    
    def test_query_processing_with_mock_embedding(self):
        """Test query processing with mocked embedding generation."""
        # Mock embedding generation
        mock_embedding = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        self.mock_model_manager.generate_text_embedding.return_value = mock_embedding
        
        # Process query
        query = self.query_processor.process_query("red brick building")
        
        # Validate query object
        self.assertIsInstance(query, Query)
        self.assertEqual(query.text, "red brick building")
        self.assertTrue(query.has_embedding())
        np.testing.assert_array_equal(query.embedding, mock_embedding)
        self.assertIsInstance(query.timestamp, datetime)
        self.assertIsInstance(query.processing_time, float)
        self.assertGreater(query.processing_time, 0)
        
        # Verify model manager was called correctly
        self.mock_model_manager.generate_text_embedding.assert_called_once_with("red brick building")
    
    def test_query_processing_error_handling(self):
        """Test error handling in query processing."""
        # Mock embedding generation failure
        self.mock_model_manager.generate_text_embedding.side_effect = Exception("Model error")
        
        # Should raise ValueError with descriptive message
        with self.assertRaises(ValueError) as context:
            self.query_processor.process_query("test query")
        
        self.assertIn("Query processing failed", str(context.exception))
    
    def test_query_validation_for_search(self):
        """Test query validation for search operations."""
        # Valid query with embedding
        mock_embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        valid_query = Query(
            text="red brick building",
            embedding=mock_embedding,
            timestamp=datetime.now()
        )
        self.assertTrue(self.query_processor.validate_query_for_search(valid_query))
        
        # Invalid query - no embedding
        invalid_query2 = Query(text="test", embedding=None)
        self.assertFalse(self.query_processor.validate_query_for_search(invalid_query2))
        
        # Invalid query - empty embedding
        invalid_query3 = Query(text="test", embedding=np.array([]))
        self.assertFalse(self.query_processor.validate_query_for_search(invalid_query3))
        
        # Invalid query - not a Query object
        self.assertFalse(self.query_processor.validate_query_for_search("not a query"))
        
        # Test that Query model itself validates empty text
        with self.assertRaises(ValueError):
            Query(text="", embedding=mock_embedding)


class TestSimilarityCalculations(unittest.TestCase):
    """Test similarity calculations with known examples."""
    
    def setUp(self):
        """Set up for each test."""
        self.config = AppConfig()
        self.mock_model_manager = Mock(spec=ModelManager)
        self.query_processor = QueryProcessor(self.config, self.mock_model_manager)
    
    def test_cosine_similarity_calculation(self):
        """Test cosine similarity calculation with known vectors."""
        # Test identical vectors (should be 1.0)
        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        similarity = self.query_processor._calculate_cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, 1.0, places=5)
        
        # Test orthogonal vectors (should be 0.0)
        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        similarity = self.query_processor._calculate_cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, 0.0, places=5)
        
        # Test opposite vectors (should be -1.0)
        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([-1.0, 0.0, 0.0], dtype=np.float32)
        similarity = self.query_processor._calculate_cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, -1.0, places=5)
        
        # Test 45-degree angle vectors (should be ~0.707)
        vec1 = np.array([1.0, 0.0], dtype=np.float32)
        vec2 = np.array([1.0, 1.0], dtype=np.float32)
        similarity = self.query_processor._calculate_cosine_similarity(vec1, vec2)
        expected = 1.0 / np.sqrt(2)  # cos(45°)
        self.assertAlmostEqual(similarity, expected, places=5)
    
    def test_similarity_calculation_error_handling(self):
        """Test error handling in similarity calculations."""
        # Test mismatched shapes
        vec1 = np.array([1.0, 0.0], dtype=np.float32)
        vec2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        
        with self.assertRaises(ValueError):
            self.query_processor._calculate_cosine_similarity(vec1, vec2)
        
        # Test empty vectors
        vec1 = np.array([], dtype=np.float32)
        vec2 = np.array([], dtype=np.float32)
        
        with self.assertRaises(ValueError):
            self.query_processor._calculate_cosine_similarity(vec1, vec2)
        
        # Test non-numpy arrays
        with self.assertRaises(ValueError):
            self.query_processor._calculate_cosine_similarity([1, 0], [0, 1])
    
    def test_batch_similarity_calculation(self):
        """Test similarity calculation for multiple images."""
        # Create test embeddings
        query_embedding = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        image_embeddings = {
            "image1.jpg": np.array([1.0, 0.0, 0.0], dtype=np.float32),  # identical
            "image2.jpg": np.array([0.0, 1.0, 0.0], dtype=np.float32),  # orthogonal
            "image3.jpg": np.array([-1.0, 0.0, 0.0], dtype=np.float32), # opposite
        }
        
        # Calculate similarities
        similarities = self.query_processor.calculate_similarities(query_embedding, image_embeddings)
        
        # Validate results
        self.assertEqual(len(similarities), 3)
        self.assertAlmostEqual(similarities["image1.jpg"], 1.0, places=5)
        self.assertAlmostEqual(similarities["image2.jpg"], 0.0, places=5)
        self.assertAlmostEqual(similarities["image3.jpg"], -1.0, places=5)
    
    def test_vectorized_similarity_calculation(self):
        """Test vectorized similarity calculation efficiency and accuracy."""
        # Create test data
        query_embedding = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        image_embeddings = {
            f"image{i}.jpg": np.random.rand(3).astype(np.float32) 
            for i in range(10)
        }
        
        # Calculate similarities using both methods
        similarities_regular = self.query_processor.calculate_similarities(
            query_embedding, image_embeddings
        )
        similarities_vectorized = self.query_processor.calculate_similarities_vectorized(
            query_embedding, image_embeddings
        )
        
        # Results should be nearly identical
        self.assertEqual(len(similarities_regular), len(similarities_vectorized))
        for path in similarities_regular:
            self.assertAlmostEqual(
                similarities_regular[path], 
                similarities_vectorized[path], 
                places=5
            )
    
    def test_similarity_calculation_with_empty_input(self):
        """Test similarity calculation with empty inputs."""
        query_embedding = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        
        # Empty image embeddings
        similarities = self.query_processor.calculate_similarities(query_embedding, {})
        self.assertEqual(len(similarities), 0)
        
        # Invalid query embedding
        with self.assertRaises(ValueError):
            self.query_processor.calculate_similarities(np.array([]), {"img.jpg": query_embedding})


class TestResultRankingAndFiltering(unittest.TestCase):
    """Test result ranking and filtering logic."""
    
    def setUp(self):
        """Set up for each test."""
        self.config = AppConfig(max_results=5, similarity_threshold=0.1)
        self.result_ranker = ResultRanker(self.config)
        
        # Create sample metadata
        self.sample_metadata = {
            "image1.jpg": ImageMetadata(
                path="image1.jpg",
                embedding=np.array([0.1, 0.2, 0.3]),
                description="Red brick building with large windows",
                features=["red brick", "large windows", "residential"]
            ),
            "image2.jpg": ImageMetadata(
                path="image2.jpg", 
                embedding=np.array([0.4, 0.5, 0.6]),
                description="Modern glass and steel structure",
                features=["glass", "steel", "modern", "commercial"]
            ),
            "image3.jpg": ImageMetadata(
                path="image3.jpg",
                embedding=np.array([0.7, 0.8, 0.9]),
                description="Stone facade with classical columns",
                features=["stone", "columns", "classical"]
            )
        }
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation from similarity scores."""
        # Test various similarity scores
        test_cases = [
            (1.0, 1.0),    # Perfect similarity -> max confidence
            (0.0, 0.25),   # Neutral similarity -> mid-low confidence  
            (-1.0, 0.0),   # Opposite similarity -> min confidence
            (0.5, 0.5625), # Positive similarity -> higher confidence
        ]
        
        for similarity, expected_confidence in test_cases:
            confidence = self.result_ranker._calculate_confidence_score(similarity)
            self.assertAlmostEqual(confidence, expected_confidence, places=4)
            self.assertGreaterEqual(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)
    
    def test_search_result_creation(self):
        """Test creation of SearchResult objects from similarities and metadata."""
        similarities = {
            "image1.jpg": 0.8,
            "image2.jpg": 0.6,
            "image3.jpg": 0.4
        }
        
        results = self.result_ranker.create_search_results(similarities, self.sample_metadata)
        
        # Validate results
        self.assertEqual(len(results), 3)
        
        for result in results:
            self.assertIsInstance(result, SearchResult)
            self.assertIn(result.image_path, similarities)
            self.assertEqual(result.similarity_score, similarities[result.image_path])
            self.assertGreater(result.confidence_score, 0)
            self.assertLessEqual(result.confidence_score, 1)
            self.assertIsInstance(result.description, str)
            self.assertIsInstance(result.features, list)
    
    def test_result_ranking_by_confidence(self):
        """Test result ranking by confidence score."""
        # Create results with different confidence scores
        results = [
            SearchResult("image1.jpg", 0.9, "desc1", 0.8, ["feature1"]),
            SearchResult("image2.jpg", 0.7, "desc2", 0.6, ["feature2"]),
            SearchResult("image3.jpg", 0.5, "desc3", 0.4, ["feature3"]),
        ]
        
        ranked_results = self.result_ranker.rank_results(results, ranking_strategy='confidence')
        
        # Should be sorted by confidence score (descending)
        self.assertEqual(len(ranked_results), 3)
        self.assertEqual(ranked_results[0].confidence_score, 0.9)
        self.assertEqual(ranked_results[1].confidence_score, 0.7)
        self.assertEqual(ranked_results[2].confidence_score, 0.5)
    
    def test_result_ranking_by_similarity(self):
        """Test result ranking by similarity score."""
        results = [
            SearchResult("image1.jpg", 0.5, "desc1", 0.9, ["feature1"]),
            SearchResult("image2.jpg", 0.7, "desc2", 0.8, ["feature2"]),
            SearchResult("image3.jpg", 0.9, "desc3", 0.7, ["feature3"]),
        ]
        
        ranked_results = self.result_ranker.rank_results(results, ranking_strategy='similarity')
        
        # Should be sorted by similarity score (descending)
        self.assertEqual(ranked_results[0].similarity_score, 0.9)
        self.assertEqual(ranked_results[1].similarity_score, 0.8)
        self.assertEqual(ranked_results[2].similarity_score, 0.7)
    
    def test_result_ranking_hybrid_strategy(self):
        """Test hybrid ranking strategy."""
        results = [
            SearchResult("image1.jpg", 0.6, "desc1", 0.9, ["feature1"]),  # High sim, med conf
            SearchResult("image2.jpg", 0.9, "desc2", 0.6, ["feature2"]),  # Med sim, high conf
            SearchResult("image3.jpg", 0.5, "desc3", 0.5, ["feature3"]),  # Med sim, med conf
        ]
        
        ranked_results = self.result_ranker.rank_results(results, ranking_strategy='hybrid')
        
        # Should combine both scores - exact order depends on weights
        self.assertEqual(len(ranked_results), 3)
        # All results should be present
        result_paths = [r.image_path for r in ranked_results]
        self.assertIn("image1.jpg", result_paths)
        self.assertIn("image2.jpg", result_paths)
        self.assertIn("image3.jpg", result_paths)
    
    def test_result_limiting(self):
        """Test limiting number of results."""
        results = [
            SearchResult(f"image{i}.jpg", 0.9 - i*0.1, f"desc{i}", 0.8 - i*0.1, [f"feature{i}"])
            for i in range(10)
        ]
        
        # Limit to 3 results
        limited_results = self.result_ranker.rank_results(results, max_results=3)
        
        self.assertEqual(len(limited_results), 3)
        # Should be the top 3 by confidence
        self.assertEqual(limited_results[0].confidence_score, 0.9)
        self.assertEqual(limited_results[1].confidence_score, 0.8)
        self.assertEqual(limited_results[2].confidence_score, 0.7)
    
    def test_threshold_filtering(self):
        """Test filtering results by threshold."""
        results = [
            SearchResult("image1.jpg", 0.9, "desc1", 0.8, ["feature1"]),
            SearchResult("image2.jpg", 0.3, "desc2", 0.2, ["feature2"]),
            SearchResult("image3.jpg", 0.1, "desc3", 0.05, ["feature3"]),
            SearchResult("image4.jpg", 0.05, "desc4", 0.01, ["feature4"]),
        ]
        
        # Filter by confidence threshold
        filtered_results = self.result_ranker.filter_by_threshold(
            results, threshold=0.2, threshold_type='confidence'
        )
        
        self.assertEqual(len(filtered_results), 2)  # Only first two should pass
        self.assertGreaterEqual(filtered_results[0].confidence_score, 0.2)
        self.assertGreaterEqual(filtered_results[1].confidence_score, 0.2)
        
        # Filter by similarity threshold
        filtered_results = self.result_ranker.filter_by_threshold(
            results, threshold=0.1, threshold_type='similarity'
        )
        
        self.assertEqual(len(filtered_results), 2)  # Only first two should pass
    
    def test_feature_filtering(self):
        """Test filtering results by architectural features."""
        results = [
            SearchResult("image1.jpg", 0.9, "desc1", 0.8, ["red brick", "windows"]),
            SearchResult("image2.jpg", 0.8, "desc2", 0.7, ["glass", "steel", "modern"]),
            SearchResult("image3.jpg", 0.7, "desc3", 0.6, ["stone", "columns"]),
            SearchResult("image4.jpg", 0.6, "desc4", 0.5, ["red brick", "residential"]),
        ]
        
        # Filter for "red brick" (any match)
        filtered_results = self.result_ranker.filter_by_features(
            results, ["red brick"], match_all=False
        )
        
        self.assertEqual(len(filtered_results), 2)  # image1 and image4
        
        # Filter for multiple features (all must match)
        filtered_results = self.result_ranker.filter_by_features(
            results, ["red brick", "windows"], match_all=True
        )
        
        self.assertEqual(len(filtered_results), 1)  # Only image1
    
    def test_diversity_filtering(self):
        """Test diversity filtering to avoid similar results."""
        results = [
            SearchResult("image1.jpg", 0.9, "desc1", 0.8, ["red brick", "windows"]),
            SearchResult("image2.jpg", 0.8, "desc2", 0.7, ["red brick", "windows"]),  # Similar to image1
            SearchResult("image3.jpg", 0.7, "desc3", 0.6, ["glass", "steel"]),        # Different
            SearchResult("image4.jpg", 0.6, "desc4", 0.5, ["stone", "columns"]),      # Different
        ]
        
        diverse_results = self.result_ranker.apply_diversity_filter(results, diversity_threshold=0.5)
        
        # Should remove image2 as it's too similar to image1
        self.assertLess(len(diverse_results), len(results))
        self.assertEqual(diverse_results[0].image_path, "image1.jpg")  # Top result always included
        
        # Check that remaining results are diverse
        result_paths = [r.image_path for r in diverse_results]
        self.assertIn("image1.jpg", result_paths)
        self.assertIn("image3.jpg", result_paths)
        self.assertIn("image4.jpg", result_paths)
    
    def test_result_statistics(self):
        """Test calculation of result statistics."""
        results = [
            SearchResult("image1.jpg", 0.9, "desc1", 0.8, ["feature1"]),
            SearchResult("image2.jpg", 0.7, "desc2", 0.6, ["feature2"]),
            SearchResult("image3.jpg", 0.5, "desc3", 0.4, ["feature3"]),
        ]
        
        stats = self.result_ranker.get_result_statistics(results)
        
        # Validate statistics
        self.assertEqual(stats['total_results'], 3)
        self.assertAlmostEqual(stats['avg_confidence'], 0.7, places=3)
        self.assertAlmostEqual(stats['avg_similarity'], 0.6, places=3)
        self.assertEqual(stats['confidence_range'], (0.5, 0.9))
        self.assertEqual(stats['similarity_range'], (0.4, 0.8))
        
        # Test with empty results
        empty_stats = self.result_ranker.get_result_statistics([])
        self.assertEqual(empty_stats['total_results'], 0)
        self.assertEqual(empty_stats['avg_confidence'], 0.0)


class TestSearchEngineIntegration(unittest.TestCase):
    """Test integrated search engine functionality."""
    
    def setUp(self):
        """Set up for each test."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.config = AppConfig(
            image_directory=str(self.test_dir / "images"),
            metadata_file=str(self.test_dir / "metadata.json"),
            max_results=3,
            similarity_threshold=0.1
        )
        
        # Mock the components to avoid loading actual models
        with patch('src.processors.search_engine.ModelManager'), \
             patch('src.processors.search_engine.MetadataStore'), \
             patch('src.processors.search_engine.QueryProcessor'), \
             patch('src.processors.search_engine.ResultRanker'):
            
            self.search_engine = SearchEngine(self.config)
            
            # Setup mocks
            self.search_engine.query_processor = Mock()
            self.search_engine.result_ranker = Mock()
            self.search_engine._embedding_cache = {
                "image1.jpg": np.array([1.0, 0.0, 0.0]),
                "image2.jpg": np.array([0.0, 1.0, 0.0]),
                "image3.jpg": np.array([0.0, 0.0, 1.0]),
            }
            self.search_engine._metadata_cache = {
                "image1.jpg": ImageMetadata("image1.jpg", np.array([1.0, 0.0, 0.0]), "desc1", ["feat1"]),
                "image2.jpg": ImageMetadata("image2.jpg", np.array([0.0, 1.0, 0.0]), "desc2", ["feat2"]),
                "image3.jpg": ImageMetadata("image3.jpg", np.array([0.0, 0.0, 1.0]), "desc3", ["feat3"]),
            }
    
    def tearDown(self):
        """Clean up after each test."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_search_validation_readiness(self):
        """Test search engine readiness validation."""
        # Mock successful validation
        self.search_engine.model_manager = Mock()
        self.search_engine.model_manager.get_model_info.return_value = {'status': 'loaded'}
        self.search_engine.metadata_store = Mock()
        self.search_engine.metadata_store.get_storage_stats.return_value = {'total_images': 3}
        
        status = self.search_engine.validate_search_readiness()
        
        self.assertTrue(status['ready'])
        self.assertEqual(len(status['issues']), 0)
        self.assertIn('statistics', status)
        self.assertEqual(status['statistics']['total_images'], 3)
    
    def test_search_statistics_tracking(self):
        """Test search statistics tracking."""
        # Get initial statistics
        initial_stats = self.search_engine.get_search_statistics()
        
        self.assertEqual(initial_stats['searches']['total_searches'], 0)
        self.assertEqual(initial_stats['cache']['cached_embeddings'], 3)
        
        # Reset statistics
        self.search_engine.reset_statistics()
        
        reset_stats = self.search_engine.get_search_statistics()
        self.assertEqual(reset_stats['searches']['total_searches'], 0)


if __name__ == '__main__':
    unittest.main()