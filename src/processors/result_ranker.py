"""
Result ranking and filtering system for search results.
"""
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple, Callable
from datetime import datetime

from ..models.config import AppConfig
from ..models.search_models import SearchResult
from ..models.image_metadata import ImageMetadata


class ResultRanker:
    """
    Handles ranking and filtering of search results based on similarity scores and confidence metrics.
    
    This class provides:
    - Result ranking based on similarity scores
    - Confidence score calculation and normalization
    - Filtering for minimum similarity thresholds
    - Advanced ranking strategies
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize ResultRanker with configuration.
        
        Args:
            config: Application configuration containing ranking settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def create_search_results(self, similarities: Dict[str, float], 
                            metadata_dict: Dict[str, ImageMetadata]) -> List[SearchResult]:
        """
        Create SearchResult objects from similarity scores and metadata.
        
        Args:
            similarities: Dictionary mapping image paths to similarity scores
            metadata_dict: Dictionary mapping image paths to metadata
            
        Returns:
            List[SearchResult]: List of search result objects
            
        Raises:
            ValueError: If input data is invalid
        """
        if not similarities:
            self.logger.warning("No similarities provided for result creation")
            return []
        
        if not metadata_dict:
            self.logger.warning("No metadata provided for result creation")
            return []
        
        results = []
        
        for image_path, similarity_score in similarities.items():
            try:
                # Get metadata for this image
                metadata = metadata_dict.get(image_path)
                if metadata is None:
                    self.logger.warning(f"No metadata found for {image_path}")
                    continue
                
                # Calculate confidence score
                confidence_score = self._calculate_confidence_score(similarity_score)
                
                # Create SearchResult
                result = SearchResult(
                    image_path=image_path,
                    confidence_score=confidence_score,
                    description=metadata.description,
                    similarity_score=similarity_score,
                    features=metadata.features.copy() if metadata.features else []
                )
                
                results.append(result)
                
            except Exception as e:
                self.logger.warning(f"Failed to create result for {image_path}: {e}")
                continue
        
        self.logger.debug(f"Created {len(results)} search results from {len(similarities)} similarities")
        return results
    
    def _calculate_confidence_score(self, similarity_score: float) -> float:
        """
        Calculate normalized confidence score from raw similarity score.
        
        The confidence score is a normalized value between 0 and 1 that represents
        how confident we are in the match quality.
        
        Args:
            similarity_score: Raw cosine similarity score (-1 to 1)
            
        Returns:
            float: Normalized confidence score (0 to 1)
        """
        # Cosine similarity ranges from -1 to 1
        # We normalize to 0-1 range and apply a curve to emphasize higher similarities
        
        # First, shift from [-1, 1] to [0, 1]
        normalized = (similarity_score + 1.0) / 2.0
        
        # Apply sigmoid-like transformation to emphasize higher similarities
        # This makes the confidence score more discriminative
        confidence = normalized ** 2  # Square to emphasize higher values
        
        # Ensure result is within bounds
        confidence = np.clip(confidence, 0.0, 1.0)
        
        return float(confidence)
    
    def rank_results(self, results: List[SearchResult], 
                    max_results: Optional[int] = None,
                    ranking_strategy: str = 'confidence') -> List[SearchResult]:
        """
        Rank search results using the specified strategy.
        
        Args:
            results: List of SearchResult objects to rank
            max_results: Maximum number of results to return (uses config default if None)
            ranking_strategy: Strategy for ranking ('confidence', 'similarity', 'hybrid')
            
        Returns:
            List[SearchResult]: Ranked and limited list of results
            
        Raises:
            ValueError: If ranking strategy is invalid
        """
        if not results:
            return []
        
        if max_results is None:
            max_results = self.config.max_results
        
        try:
            # Choose ranking function based on strategy
            if ranking_strategy == 'confidence':
                sorted_results = self._rank_by_confidence(results)
            elif ranking_strategy == 'similarity':
                sorted_results = self._rank_by_similarity(results)
            elif ranking_strategy == 'hybrid':
                sorted_results = self._rank_by_hybrid_score(results)
            else:
                raise ValueError(f"Unknown ranking strategy: {ranking_strategy}")
            
            # Limit results
            if max_results > 0:
                sorted_results = sorted_results[:max_results]
            
            self.logger.debug(f"Ranked {len(results)} results using '{ranking_strategy}' strategy, "
                            f"returning top {len(sorted_results)}")
            
            return sorted_results
            
        except Exception as e:
            self.logger.error(f"Failed to rank results: {e}")
            # Fallback to confidence-based ranking
            return self._rank_by_confidence(results)[:max_results if max_results > 0 else len(results)]
    
    def _rank_by_confidence(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Rank results by confidence score in descending order.
        
        Args:
            results: List of SearchResult objects
            
        Returns:
            List[SearchResult]: Results sorted by confidence score
        """
        return sorted(results, key=lambda x: x.confidence_score, reverse=True)
    
    def _rank_by_similarity(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Rank results by raw similarity score in descending order.
        
        Args:
            results: List of SearchResult objects
            
        Returns:
            List[SearchResult]: Results sorted by similarity score
        """
        return sorted(results, key=lambda x: x.similarity_score, reverse=True)
    
    def _rank_by_hybrid_score(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Rank results using a hybrid score combining confidence and similarity.
        
        Args:
            results: List of SearchResult objects
            
        Returns:
            List[SearchResult]: Results sorted by hybrid score
        """
        def hybrid_score(result: SearchResult) -> float:
            # Combine confidence and similarity with weights
            confidence_weight = 0.7
            similarity_weight = 0.3
            
            # Normalize similarity to 0-1 range for combination
            normalized_similarity = (result.similarity_score + 1.0) / 2.0
            
            return (confidence_weight * result.confidence_score + 
                   similarity_weight * normalized_similarity)
        
        return sorted(results, key=hybrid_score, reverse=True)
    
    def filter_by_threshold(self, results: List[SearchResult], 
                          threshold: Optional[float] = None,
                          threshold_type: str = 'confidence') -> List[SearchResult]:
        """
        Filter results by minimum threshold value.
        
        Args:
            results: List of SearchResult objects to filter
            threshold: Minimum threshold value (uses config default if None)
            threshold_type: Type of threshold ('confidence' or 'similarity')
            
        Returns:
            List[SearchResult]: Filtered results above threshold
            
        Raises:
            ValueError: If threshold type is invalid
        """
        if not results:
            return []
        
        if threshold is None:
            threshold = self.config.similarity_threshold
        
        try:
            if threshold_type == 'confidence':
                filtered_results = [r for r in results if r.confidence_score >= threshold]
            elif threshold_type == 'similarity':
                filtered_results = [r for r in results if r.similarity_score >= threshold]
            else:
                raise ValueError(f"Unknown threshold type: {threshold_type}")
            
            self.logger.debug(f"Filtered {len(results)} results to {len(filtered_results)} "
                            f"using {threshold_type} threshold {threshold}")
            
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"Failed to filter results: {e}")
            return results  # Return unfiltered results on error
    
    def filter_by_features(self, results: List[SearchResult], 
                          required_features: List[str],
                          match_all: bool = False) -> List[SearchResult]:
        """
        Filter results by architectural features.
        
        Args:
            results: List of SearchResult objects to filter
            required_features: List of features that must be present
            match_all: If True, all features must be present; if False, any feature
            
        Returns:
            List[SearchResult]: Filtered results matching feature criteria
        """
        if not results or not required_features:
            return results
        
        # Normalize feature names for comparison
        normalized_required = [f.lower().strip() for f in required_features]
        
        filtered_results = []
        
        for result in results:
            if not result.features:
                continue
            
            # Normalize result features
            normalized_result_features = [f.lower().strip() for f in result.features]
            
            if match_all:
                # All required features must be present
                if all(req_feature in normalized_result_features for req_feature in normalized_required):
                    filtered_results.append(result)
            else:
                # Any required feature must be present
                if any(req_feature in normalized_result_features for req_feature in normalized_required):
                    filtered_results.append(result)
        
        self.logger.debug(f"Filtered {len(results)} results to {len(filtered_results)} "
                        f"using feature filter (match_all={match_all})")
        
        return filtered_results
    
    def apply_diversity_filter(self, results: List[SearchResult], 
                             diversity_threshold: float = 0.8) -> List[SearchResult]:
        """
        Apply diversity filtering to avoid too many similar results.
        
        This method removes results that are too similar to higher-ranked results
        to provide more diverse search results.
        
        Args:
            results: List of SearchResult objects (should be pre-sorted)
            diversity_threshold: Similarity threshold for diversity filtering
            
        Returns:
            List[SearchResult]: Filtered results with improved diversity
        """
        if len(results) <= 1:
            return results
        
        diverse_results = [results[0]]  # Always include the top result
        
        for candidate in results[1:]:
            is_diverse = True
            
            # Check similarity with already selected results
            for selected in diverse_results:
                # Simple diversity check based on feature overlap
                if self._calculate_feature_similarity(candidate, selected) > diversity_threshold:
                    is_diverse = False
                    break
            
            if is_diverse:
                diverse_results.append(candidate)
        
        self.logger.debug(f"Applied diversity filter: {len(results)} -> {len(diverse_results)} results")
        return diverse_results
    
    def _calculate_feature_similarity(self, result1: SearchResult, result2: SearchResult) -> float:
        """
        Calculate similarity between two results based on their features.
        
        Args:
            result1: First search result
            result2: Second search result
            
        Returns:
            float: Feature similarity score (0 to 1)
        """
        if not result1.features or not result2.features:
            return 0.0
        
        # Convert to sets for intersection/union operations
        features1 = set(f.lower().strip() for f in result1.features)
        features2 = set(f.lower().strip() for f in result2.features)
        
        # Calculate Jaccard similarity
        intersection = len(features1.intersection(features2))
        union = len(features1.union(features2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def get_result_statistics(self, results: List[SearchResult]) -> Dict[str, any]:
        """
        Calculate statistics for a list of search results.
        
        Args:
            results: List of SearchResult objects
            
        Returns:
            dict: Statistics about the results
        """
        if not results:
            return {
                'total_results': 0,
                'avg_confidence': 0.0,
                'avg_similarity': 0.0,
                'confidence_range': (0.0, 0.0),
                'similarity_range': (0.0, 0.0)
            }
        
        confidences = [r.confidence_score for r in results]
        similarities = [r.similarity_score for r in results]
        
        return {
            'total_results': len(results),
            'avg_confidence': round(np.mean(confidences), 3),
            'avg_similarity': round(np.mean(similarities), 3),
            'confidence_range': (round(min(confidences), 3), round(max(confidences), 3)),
            'similarity_range': (round(min(similarities), 3), round(max(similarities), 3)),
            'std_confidence': round(np.std(confidences), 3),
            'std_similarity': round(np.std(similarities), 3)
        }