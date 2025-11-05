"""
Query processing system for natural language search against architectural images.
"""
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import time

from ..models.config import AppConfig
from ..models.search_models import Query, SearchResult
from ..processors.model_manager import ModelManager


class QueryProcessor:
    """
    Processes natural language queries and performs similarity-based search against image embeddings.
    
    This class handles:
    - CLIP text encoding for user queries
    - Cosine similarity calculation between query and image embeddings
    - Efficient vectorized similarity computation
    - Query validation and preprocessing
    """
    
    def __init__(self, config: AppConfig, model_manager: ModelManager):
        """
        Initialize QueryProcessor with configuration and model manager.
        
        Args:
            config: Application configuration containing search settings
            model_manager: ModelManager instance for CLIP text encoding
        """
        self.config = config
        self.model_manager = model_manager
        self.logger = logging.getLogger(__name__)
        
        # Query processing statistics
        self._query_count = 0
        self._total_processing_time = 0.0
    
    def process_query(self, query_text: str) -> Query:
        """
        Process a natural language query and generate its embedding.
        
        Args:
            query_text: User's natural language query
            
        Returns:
            Query: Processed query object with embedding
            
        Raises:
            ValueError: If query is invalid or processing fails
        """
        start_time = time.time()
        
        try:
            # Validate and normalize query
            normalized_text = self._validate_and_normalize_query(query_text)
            
            # Generate query embedding using CLIP
            query_embedding = self.model_manager.generate_text_embedding(normalized_text)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create Query object
            query = Query(
                text=query_text,
                embedding=query_embedding,
                timestamp=datetime.now(),
                processing_time=processing_time
            )
            
            # Update statistics
            self._query_count += 1
            self._total_processing_time += processing_time
            
            self.logger.info(f"Processed query: '{query_text[:50]}...' in {processing_time:.3f}s")
            return query
            
        except Exception as e:
            self.logger.error(f"Failed to process query '{query_text}': {e}")
            raise ValueError(f"Query processing failed: {e}")
    
    def _validate_and_normalize_query(self, query_text: str) -> str:
        """
        Validate and normalize user query text.
        
        Args:
            query_text: Raw query text from user
            
        Returns:
            str: Normalized query text
            
        Raises:
            ValueError: If query is invalid
        """
        if not query_text:
            raise ValueError("Query cannot be empty")
        
        if not isinstance(query_text, str):
            raise ValueError("Query must be a string")
        
        # Strip whitespace and normalize
        normalized = query_text.strip()
        
        if not normalized:
            raise ValueError("Query cannot be empty or whitespace only")
        
        # Check minimum length
        if len(normalized) < 2:
            raise ValueError("Query must be at least 2 characters long")
        
        # Check maximum length (CLIP has token limits)
        max_length = 200  # Conservative limit for CLIP tokenization
        if len(normalized) > max_length:
            self.logger.warning(f"Query truncated from {len(normalized)} to {max_length} characters")
            normalized = normalized[:max_length]
        
        return normalized
    
    def calculate_similarities(self, query_embedding: np.ndarray, 
                             image_embeddings: Dict[str, np.ndarray]) -> Dict[str, float]:
        """
        Calculate cosine similarities between query embedding and all image embeddings.
        
        Args:
            query_embedding: CLIP embedding for the user query
            image_embeddings: Dictionary mapping image paths to their embeddings
            
        Returns:
            Dict[str, float]: Dictionary mapping image paths to similarity scores
            
        Raises:
            ValueError: If embeddings are invalid or calculation fails
        """
        if not isinstance(query_embedding, np.ndarray):
            raise ValueError("Query embedding must be a numpy array")
        
        if len(query_embedding) == 0:
            raise ValueError("Query embedding cannot be empty")
        
        if not image_embeddings:
            self.logger.warning("No image embeddings provided for similarity calculation")
            return {}
        
        try:
            similarities = {}
            
            # Normalize query embedding once
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            
            # Calculate similarities for each image
            for image_path, image_embedding in image_embeddings.items():
                try:
                    similarity = self._calculate_cosine_similarity(query_norm, image_embedding)
                    similarities[image_path] = similarity
                    
                except Exception as e:
                    self.logger.warning(f"Failed to calculate similarity for {image_path}: {e}")
                    continue
            
            self.logger.debug(f"Calculated similarities for {len(similarities)} images")
            return similarities
            
        except Exception as e:
            self.logger.error(f"Failed to calculate similarities: {e}")
            raise ValueError(f"Similarity calculation failed: {e}")
    
    def calculate_similarities_vectorized(self, query_embedding: np.ndarray, 
                                        image_embeddings: Dict[str, np.ndarray]) -> Dict[str, float]:
        """
        Calculate cosine similarities using efficient vectorized operations with enhanced error handling.
        
        Args:
            query_embedding: CLIP embedding for the user query
            image_embeddings: Dictionary mapping image paths to their embeddings
            
        Returns:
            Dict[str, float]: Dictionary mapping image paths to similarity scores
            
        Raises:
            ValueError: If embeddings are invalid or calculation fails
        """
        if not isinstance(query_embedding, np.ndarray):
            raise ValueError("Query embedding must be a numpy array")
        
        if len(query_embedding) == 0:
            raise ValueError("Query embedding cannot be empty")
        
        if not image_embeddings:
            self.logger.warning("No image embeddings provided for similarity calculation")
            return {}
        
        try:
            # Filter out invalid embeddings
            valid_embeddings = {}
            for path, embedding in image_embeddings.items():
                if isinstance(embedding, np.ndarray) and embedding.size > 0:
                    # Check for NaN or infinite values
                    if not np.isfinite(embedding).all():
                        self.logger.warning(f"Invalid embedding for {path}: contains NaN or infinite values")
                        continue
                    
                    # Check embedding dimension matches query
                    if embedding.shape != query_embedding.shape:
                        self.logger.warning(f"Embedding dimension mismatch for {path}: {embedding.shape} vs {query_embedding.shape}")
                        continue
                    
                    valid_embeddings[path] = embedding
                else:
                    self.logger.warning(f"Invalid embedding for {path}: not a valid numpy array")
            
            if not valid_embeddings:
                self.logger.error("No valid embeddings found for similarity calculation")
                return {}
            
            # Convert embeddings to matrix for vectorized operations
            image_paths = list(valid_embeddings.keys())
            
            try:
                embedding_matrix = np.array([valid_embeddings[path] for path in image_paths])
            except Exception as e:
                self.logger.error(f"Failed to create embedding matrix: {e}")
                # Fallback to individual processing
                return self.calculate_similarities(query_embedding, valid_embeddings)
            
            # Validate query embedding
            if not np.isfinite(query_embedding).all():
                raise ValueError("Query embedding contains NaN or infinite values")
            
            # Normalize query embedding with error handling
            try:
                query_norm_value = np.linalg.norm(query_embedding)
                if query_norm_value == 0:
                    raise ValueError("Query embedding has zero norm")
                query_norm = query_embedding / query_norm_value
            except Exception as e:
                self.logger.error(f"Failed to normalize query embedding: {e}")
                raise ValueError(f"Query embedding normalization failed: {e}")
            
            # Normalize image embeddings with error handling
            try:
                image_norms_values = np.linalg.norm(embedding_matrix, axis=1, keepdims=True)
                
                # Check for zero norms
                zero_norm_mask = (image_norms_values == 0).flatten()
                if zero_norm_mask.any():
                    self.logger.warning(f"Found {zero_norm_mask.sum()} embeddings with zero norm")
                    # Set zero norms to 1 to avoid division by zero
                    image_norms_values[zero_norm_mask] = 1.0
                
                image_norms = embedding_matrix / image_norms_values
                
            except Exception as e:
                self.logger.error(f"Failed to normalize image embeddings: {e}")
                # Fallback to individual processing
                return self.calculate_similarities(query_embedding, valid_embeddings)
            
            # Vectorized cosine similarity calculation
            try:
                similarities_array = np.dot(image_norms, query_norm)
                
                # Validate results
                if not np.isfinite(similarities_array).all():
                    self.logger.warning("Some similarity scores are NaN or infinite")
                    # Replace invalid values with 0
                    similarities_array = np.nan_to_num(similarities_array, nan=0.0, posinf=1.0, neginf=-1.0)
                
                # Clip to valid range
                similarities_array = np.clip(similarities_array, -1.0, 1.0)
                
            except Exception as e:
                self.logger.error(f"Failed to calculate similarities: {e}")
                # Fallback to individual processing
                return self.calculate_similarities(query_embedding, valid_embeddings)
            
            # Create result dictionary
            similarities = dict(zip(image_paths, similarities_array.tolist()))
            
            self.logger.debug(f"Calculated vectorized similarities for {len(similarities)} images")
            return similarities
            
        except Exception as e:
            self.logger.error(f"Failed to calculate vectorized similarities: {e}")
            # Fallback to non-vectorized calculation
            self.logger.info("Falling back to non-vectorized similarity calculation")
            try:
                return self.calculate_similarities(query_embedding, image_embeddings)
            except Exception as fallback_error:
                self.logger.error(f"Fallback similarity calculation also failed: {fallback_error}")
                return {}
    
    def _calculate_cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two normalized embeddings.
        
        Args:
            embedding1: First embedding (should be normalized)
            embedding2: Second embedding
            
        Returns:
            float: Cosine similarity score between -1 and 1
            
        Raises:
            ValueError: If embeddings are invalid
        """
        if not isinstance(embedding1, np.ndarray) or not isinstance(embedding2, np.ndarray):
            raise ValueError("Both embeddings must be numpy arrays")
        
        if embedding1.shape != embedding2.shape:
            raise ValueError(f"Embedding shapes must match: {embedding1.shape} vs {embedding2.shape}")
        
        if len(embedding1) == 0:
            raise ValueError("Embeddings cannot be empty")
        
        try:
            # Normalize second embedding
            embedding2_norm = embedding2 / np.linalg.norm(embedding2)
            
            # Calculate dot product (cosine similarity for normalized vectors)
            similarity = np.dot(embedding1, embedding2_norm)
            
            # Ensure result is within valid range
            similarity = np.clip(similarity, -1.0, 1.0)
            
            return float(similarity)
            
        except Exception as e:
            raise ValueError(f"Could not calculate cosine similarity: {e}")
    
    def get_processing_stats(self) -> Dict[str, any]:
        """
        Get statistics about query processing performance.
        
        Returns:
            dict: Processing statistics
        """
        avg_processing_time = (
            self._total_processing_time / self._query_count 
            if self._query_count > 0 else 0.0
        )
        
        return {
            'total_queries_processed': self._query_count,
            'total_processing_time': round(self._total_processing_time, 3),
            'average_processing_time': round(avg_processing_time, 3),
            'queries_per_second': round(
                self._query_count / self._total_processing_time 
                if self._total_processing_time > 0 else 0.0, 2
            )
        }
    
    def reset_stats(self):
        """Reset processing statistics."""
        self._query_count = 0
        self._total_processing_time = 0.0
        self.logger.info("Query processing statistics reset")
    
    def validate_query_for_search(self, query: Query) -> bool:
        """
        Validate that a query is ready for search operations.
        
        Args:
            query: Query object to validate
            
        Returns:
            bool: True if query is valid for search
        """
        if not isinstance(query, Query):
            return False
        
        if not query.text or not query.text.strip():
            return False
        
        if not query.has_embedding():
            return False
        
        if query.embedding.size == 0:
            return False
        
        return True