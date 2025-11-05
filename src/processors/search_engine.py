"""
Integrated search engine that combines query processing, metadata storage, and result ranking.
"""
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import time
from pathlib import Path

from ..models.config import AppConfig
from ..models.search_models import Query, SearchResult
from ..models.image_metadata import ImageMetadata
from ..storage.metadata_store import MetadataStore
from ..processors.model_manager import ModelManager
from ..processors.query_processor import QueryProcessor
from ..processors.result_ranker import ResultRanker


class SearchEngine:
    """
    Integrated search engine that orchestrates query processing, similarity calculation,
    and result ranking with efficient metadata storage integration.
    
    This class provides:
    - End-to-end search functionality
    - Caching for frequently accessed embeddings
    - Error handling for missing or corrupted metadata
    - Performance optimization and monitoring
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize SearchEngine with configuration.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.model_manager = ModelManager(config)
        self.metadata_store = MetadataStore(config)
        self.query_processor = QueryProcessor(config, self.model_manager)
        self.result_ranker = ResultRanker(config)
        
        # Caching for embeddings and metadata
        self._embedding_cache: Dict[str, np.ndarray] = {}
        self._metadata_cache: Dict[str, ImageMetadata] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=30)  # Cache time-to-live
        
        # Search statistics
        self._search_count = 0
        self._total_search_time = 0.0
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Initialize caches
        self._refresh_caches()
    
    def search(self, query_text: str, 
               max_results: Optional[int] = None,
               similarity_threshold: Optional[float] = None,
               ranking_strategy: str = 'confidence',
               apply_diversity_filter: bool = False) -> Tuple[List[SearchResult], Query]:
        """
        Perform end-to-end search for architectural images with enhanced error handling.
        
        Args:
            query_text: Natural language query from user
            max_results: Maximum number of results to return
            similarity_threshold: Minimum similarity threshold for results
            ranking_strategy: Strategy for ranking results ('confidence', 'similarity', 'hybrid')
            apply_diversity_filter: Whether to apply diversity filtering
            
        Returns:
            Tuple[List[SearchResult], Query]: Search results and processed query
            
        Raises:
            ValueError: If search fails due to invalid input or processing errors
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting search for query: '{query_text[:50]}...'")
            
            # Validate input parameters
            if not query_text or not query_text.strip():
                raise ValueError("Query text cannot be empty")
            
            if max_results is not None and max_results <= 0:
                raise ValueError("max_results must be positive")
            
            if similarity_threshold is not None and not (0 <= similarity_threshold <= 1):
                raise ValueError("similarity_threshold must be between 0 and 1")
            
            # Process the query with error handling
            try:
                query = self.query_processor.process_query(query_text)
            except Exception as e:
                self.logger.error(f"Query processing failed: {e}")
                raise ValueError(f"Failed to process query: {e}")
            
            # Refresh caches if needed with error handling
            try:
                self._refresh_caches_if_needed()
            except Exception as e:
                self.logger.warning(f"Cache refresh failed, using existing cache: {e}")
            
            # Get image embeddings with fallback
            image_embeddings = self._get_cached_embeddings()
            
            if not image_embeddings:
                self.logger.warning("No image embeddings available for search")
                # Return empty results with valid query
                query.results_count = 0
                return [], query
            
            # Calculate similarities with error handling
            try:
                similarities = self.query_processor.calculate_similarities_vectorized(
                    query.embedding, image_embeddings
                )
            except Exception as e:
                self.logger.warning(f"Vectorized similarity calculation failed, falling back: {e}")
                similarities = self.query_processor.calculate_similarities(
                    query.embedding, image_embeddings
                )
            
            # Create search results with error handling
            try:
                results = self.result_ranker.create_search_results(
                    similarities, self._metadata_cache
                )
            except Exception as e:
                self.logger.error(f"Failed to create search results: {e}")
                query.results_count = 0
                return [], query
            
            # Apply threshold filtering with graceful degradation
            try:
                threshold = similarity_threshold if similarity_threshold is not None else self.config.similarity_threshold
                results = self.result_ranker.filter_by_threshold(
                    results, threshold, 'similarity'
                )
            except Exception as e:
                self.logger.warning(f"Threshold filtering failed, using all results: {e}")
            
            # Rank results with error handling
            try:
                results = self.result_ranker.rank_results(
                    results, max_results, ranking_strategy
                )
            except Exception as e:
                self.logger.warning(f"Result ranking failed, using default order: {e}")
                if max_results is not None:
                    results = results[:max_results]
            
            # Apply diversity filter if requested
            if apply_diversity_filter:
                try:
                    results = self.result_ranker.apply_diversity_filter(results)
                except Exception as e:
                    self.logger.warning(f"Diversity filtering failed, skipping: {e}")
            
            # Validate results before returning
            validated_results = []
            for result in results:
                if self._validate_search_result(result):
                    validated_results.append(result)
                else:
                    self.logger.warning(f"Invalid result filtered out: {result.image_path}")
            
            # Update query with results count
            query.results_count = len(validated_results)
            
            # Update statistics
            search_time = time.time() - start_time
            self._search_count += 1
            self._total_search_time += search_time
            
            self.logger.info(f"Search completed: {len(validated_results)} results in {search_time:.3f}s")
            
            return validated_results, query
            
        except Exception as e:
            search_time = time.time() - start_time
            self.logger.error(f"Search failed for query '{query_text}': {e}")
            
            # Create empty query for error case
            try:
                empty_query = Query(
                    text=query_text,
                    embedding=np.array([]),
                    timestamp=datetime.now(),
                    results_count=0
                )
            except:
                empty_query = None
            
            # Update error statistics
            self._search_count += 1
            self._total_search_time += search_time
            
            raise ValueError(f"Search operation failed: {e}")
    
    def _validate_search_result(self, result: SearchResult) -> bool:
        """
        Validate a search result to ensure it's complete and accessible.
        
        Args:
            result: SearchResult to validate
            
        Returns:
            bool: True if result is valid
        """
        try:
            # Check if image file exists
            if not Path(result.image_path).exists():
                return False
            
            # Check if confidence score is valid
            if not (0 <= result.confidence_score <= 1):
                return False
            
            # Check if similarity score is valid
            if not (-1 <= result.similarity_score <= 1):
                return False
            
            # Check if description exists
            if not result.description or not result.description.strip():
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Result validation error: {e}")
            return False
    
    def _refresh_caches_if_needed(self):
        """Refresh caches if they are stale or empty."""
        current_time = datetime.now()
        
        # Check if cache needs refresh
        needs_refresh = (
            not self._embedding_cache or 
            not self._metadata_cache or
            self._cache_timestamp is None or
            current_time - self._cache_timestamp > self._cache_ttl
        )
        
        if needs_refresh:
            self._refresh_caches()
    
    def _refresh_caches(self):
        """Refresh embedding and metadata caches from storage."""
        try:
            self.logger.debug("Refreshing search caches...")
            
            # Load metadata from storage
            metadata_dict = self.metadata_store.load_all_metadata()
            
            # Extract embeddings and update caches
            embedding_cache = {}
            metadata_cache = {}
            
            for path, metadata in metadata_dict.items():
                if metadata.embedding is not None:
                    embedding_cache[path] = metadata.embedding
                    metadata_cache[path] = metadata
                else:
                    self.logger.warning(f"No embedding found for {path}")
            
            # Update caches atomically
            self._embedding_cache = embedding_cache
            self._metadata_cache = metadata_cache
            self._cache_timestamp = datetime.now()
            
            self.logger.info(f"Refreshed caches: {len(self._embedding_cache)} embeddings, "
                           f"{len(self._metadata_cache)} metadata entries")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh caches: {e}")
            # Keep existing caches on error
    
    def _get_cached_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Get embeddings from cache with hit/miss tracking.
        
        Returns:
            Dict[str, np.ndarray]: Dictionary of cached embeddings
        """
        if self._embedding_cache:
            self._cache_hits += 1
            return self._embedding_cache.copy()
        else:
            self._cache_misses += 1
            self.logger.warning("Embedding cache miss - refreshing caches")
            self._refresh_caches()
            return self._embedding_cache.copy()
    
    def search_by_features(self, features: List[str], 
                          match_all: bool = False,
                          max_results: Optional[int] = None) -> List[SearchResult]:
        """
        Search for images by architectural features without natural language query.
        
        Args:
            features: List of architectural features to search for
            match_all: If True, all features must be present; if False, any feature
            max_results: Maximum number of results to return
            
        Returns:
            List[SearchResult]: Search results matching feature criteria
        """
        try:
            self._refresh_caches_if_needed()
            
            # Create dummy results with high confidence for feature matches
            results = []
            
            for path, metadata in self._metadata_cache.items():
                if not metadata.features:
                    continue
                
                # Check feature matching
                normalized_metadata_features = [f.lower().strip() for f in metadata.features]
                normalized_search_features = [f.lower().strip() for f in features]
                
                matches = [f for f in normalized_search_features if f in normalized_metadata_features]
                
                if match_all and len(matches) == len(normalized_search_features):
                    # All features match
                    confidence = 1.0
                elif not match_all and matches:
                    # Some features match
                    confidence = len(matches) / len(normalized_search_features)
                else:
                    continue
                
                result = SearchResult(
                    image_path=path,
                    confidence_score=confidence,
                    description=metadata.description,
                    similarity_score=confidence,  # Use confidence as similarity for feature search
                    features=metadata.features.copy()
                )
                
                results.append(result)
            
            # Rank and limit results
            results = self.result_ranker.rank_results(results, max_results, 'confidence')
            
            self.logger.info(f"Feature search completed: {len(results)} results for features {features}")
            return results
            
        except Exception as e:
            self.logger.error(f"Feature search failed: {e}")
            return []
    
    def get_similar_images(self, image_path: str, 
                          max_results: Optional[int] = None,
                          exclude_self: bool = True) -> List[SearchResult]:
        """
        Find images similar to a given image.
        
        Args:
            image_path: Path to the reference image
            max_results: Maximum number of results to return
            exclude_self: Whether to exclude the reference image from results
            
        Returns:
            List[SearchResult]: Similar images ranked by similarity
        """
        try:
            self._refresh_caches_if_needed()
            
            # Get embedding for reference image
            if image_path not in self._embedding_cache:
                self.logger.error(f"No embedding found for reference image: {image_path}")
                return []
            
            reference_embedding = self._embedding_cache[image_path]
            
            # Calculate similarities with all other images
            similarities = {}
            for path, embedding in self._embedding_cache.items():
                if exclude_self and path == image_path:
                    continue
                
                similarity = self.query_processor._calculate_cosine_similarity(
                    reference_embedding / np.linalg.norm(reference_embedding),
                    embedding
                )
                similarities[path] = similarity
            
            # Create and rank results
            results = self.result_ranker.create_search_results(similarities, self._metadata_cache)
            results = self.result_ranker.rank_results(results, max_results, 'similarity')
            
            self.logger.info(f"Similar image search completed: {len(results)} results for {image_path}")
            return results
            
        except Exception as e:
            self.logger.error(f"Similar image search failed: {e}")
            return []
    
    def validate_search_readiness(self) -> Dict[str, any]:
        """
        Validate that the search engine is ready for operations.
        
        Returns:
            dict: Validation results and system status
        """
        status = {
            'ready': True,
            'issues': [],
            'statistics': {}
        }
        
        try:
            # Check model manager
            model_info = self.model_manager.get_model_info()
            if model_info.get('status') != 'loaded':
                status['ready'] = False
                status['issues'].append('CLIP model not loaded')
            
            # Check metadata store
            storage_stats = self.metadata_store.get_storage_stats()
            if storage_stats['total_images'] == 0:
                status['ready'] = False
                status['issues'].append('No images in metadata store')
            
            # Check caches
            self._refresh_caches_if_needed()
            if not self._embedding_cache:
                status['ready'] = False
                status['issues'].append('No embeddings in cache')
            
            # Collect statistics
            status['statistics'] = {
                'total_images': len(self._embedding_cache),
                'cache_hits': self._cache_hits,
                'cache_misses': self._cache_misses,
                'total_searches': self._search_count,
                'avg_search_time': (
                    self._total_search_time / self._search_count 
                    if self._search_count > 0 else 0.0
                ),
                'cache_hit_rate': (
                    self._cache_hits / (self._cache_hits + self._cache_misses)
                    if (self._cache_hits + self._cache_misses) > 0 else 0.0
                )
            }
            
        except Exception as e:
            status['ready'] = False
            status['issues'].append(f'Validation error: {e}')
        
        return status
    
    def clear_caches(self):
        """Clear all caches and force refresh on next access."""
        self._embedding_cache.clear()
        self._metadata_cache.clear()
        self._cache_timestamp = None
        self.logger.info("Search caches cleared")
    
    def get_search_statistics(self) -> Dict[str, any]:
        """
        Get comprehensive search engine statistics.
        
        Returns:
            dict: Search engine performance statistics
        """
        cache_total = self._cache_hits + self._cache_misses
        
        return {
            'searches': {
                'total_searches': self._search_count,
                'total_search_time': round(self._total_search_time, 3),
                'average_search_time': round(
                    self._total_search_time / self._search_count 
                    if self._search_count > 0 else 0.0, 3
                ),
                'searches_per_second': round(
                    self._search_count / self._total_search_time 
                    if self._total_search_time > 0 else 0.0, 2
                )
            },
            'cache': {
                'cache_hits': self._cache_hits,
                'cache_misses': self._cache_misses,
                'hit_rate': round(
                    self._cache_hits / cache_total if cache_total > 0 else 0.0, 3
                ),
                'cached_embeddings': len(self._embedding_cache),
                'cached_metadata': len(self._metadata_cache),
                'cache_age_minutes': round(
                    (datetime.now() - self._cache_timestamp).total_seconds() / 60
                    if self._cache_timestamp else 0.0, 1
                )
            },
            'components': {
                'query_processor': self.query_processor.get_processing_stats(),
                'model_manager': self.model_manager.get_model_info(),
                'metadata_store': self.metadata_store.get_storage_stats()
            }
        }
    
    def reset_statistics(self):
        """Reset all performance statistics."""
        self._search_count = 0
        self._total_search_time = 0.0
        self._cache_hits = 0
        self._cache_misses = 0
        self.query_processor.reset_stats()
        self.logger.info("Search engine statistics reset")
    
    def cleanup(self):
        """Clean up resources and caches."""
        self.clear_caches()
        self.model_manager.cleanup()
        self.logger.info("Search engine cleanup completed")