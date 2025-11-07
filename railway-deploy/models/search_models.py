"""
Search-related data models for query processing and result handling.
"""
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import numpy as np


@dataclass
class SearchResult:
    """
    Represents a search result with confidence scoring and metadata.
    
    Attributes:
        image_path: Path to the matching image file
        confidence_score: Normalized confidence score (0-1)
        description: AI-generated description of the image
        similarity_score: Raw cosine similarity score
        features: List of architectural features found in the image
    """
    image_path: str
    confidence_score: float
    description: str
    similarity_score: float
    features: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validate fields after initialization."""
        if not self.image_path:
            raise ValueError("Image path is required")
            
        if not isinstance(self.image_path, str):
            raise TypeError("Image path must be a string")
            
        if not isinstance(self.confidence_score, (int, float)):
            raise TypeError("Confidence score must be a number")
            
        if not (0 <= self.confidence_score <= 1):
            raise ValueError("Confidence score must be between 0 and 1")
            
        if not isinstance(self.similarity_score, (int, float)):
            raise TypeError("Similarity score must be a number")
            
        if not self.description:
            raise ValueError("Description is required")
            
        if not isinstance(self.description, str):
            raise TypeError("Description must be a string")
            
        if self.features is None:
            self.features = []
    
    def __lt__(self, other: 'SearchResult') -> bool:
        """Enable sorting by confidence score (descending order)."""
        return self.confidence_score > other.confidence_score
    
    def __eq__(self, other: 'SearchResult') -> bool:
        """Check equality based on image path and confidence score."""
        if not isinstance(other, SearchResult):
            return False
        return (self.image_path == other.image_path and 
                abs(self.confidence_score - other.confidence_score) < 1e-6)
    
    def __hash__(self) -> int:
        """Enable use in sets and as dictionary keys."""
        return hash((self.image_path, round(self.confidence_score, 6)))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchResult':
        """Create SearchResult from dictionary."""
        required_fields = ['image_path', 'confidence_score', 'description', 'similarity_score']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Required field '{field}' is missing")
        
        return cls(**data)


@dataclass
class Query:
    """
    Represents a user search query with metadata and processing information.
    
    Attributes:
        text: The original query text from the user
        embedding: CLIP embedding vector for the query text
        timestamp: When the query was created
        results_count: Number of results returned for this query
        processing_time: Time taken to process the query in seconds
    """
    text: str
    embedding: Optional[np.ndarray] = None
    timestamp: Optional[datetime] = None
    results_count: Optional[int] = None
    processing_time: Optional[float] = None
    
    def __post_init__(self):
        """Validate fields and set defaults after initialization."""
        if not self.text:
            raise ValueError("Query text is required")
            
        if not isinstance(self.text, str):
            raise TypeError("Query text must be a string")
            
        if self.text.strip() == "":
            raise ValueError("Query text cannot be empty or whitespace only")
            
        if self.embedding is not None and not isinstance(self.embedding, np.ndarray):
            raise TypeError("Embedding must be a numpy array")
            
        if self.results_count is not None and not isinstance(self.results_count, int):
            raise TypeError("Results count must be an integer")
            
        if self.results_count is not None and self.results_count < 0:
            raise ValueError("Results count cannot be negative")
            
        if self.processing_time is not None and not isinstance(self.processing_time, (int, float)):
            raise TypeError("Processing time must be a number")
            
        if self.processing_time is not None and self.processing_time < 0:
            raise ValueError("Processing time cannot be negative")
            
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Query to dictionary for serialization.
        
        Returns:
            Dictionary representation with embedding converted to list
        """
        data = asdict(self)
        # Convert numpy array to list for JSON serialization
        if self.embedding is not None:
            data['embedding'] = self.embedding.tolist()
        # Convert datetime to ISO string
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Query':
        """
        Create Query instance from dictionary.
        
        Args:
            data: Dictionary containing query fields
            
        Returns:
            Query instance
        """
        if 'text' not in data:
            raise ValueError("Required field 'text' is missing")
        
        # Convert embedding list back to numpy array
        if 'embedding' in data and isinstance(data['embedding'], list):
            data['embedding'] = np.array(data['embedding'], dtype=np.float32)
        
        # Convert ISO string back to datetime
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize Query to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Query':
        """Deserialize Query from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def get_normalized_text(self) -> str:
        """
        Get normalized version of query text for processing.
        
        Returns:
            Lowercase, stripped query text
        """
        return self.text.strip().lower()
    
    def has_embedding(self) -> bool:
        """Check if query has an associated embedding."""
        return self.embedding is not None and len(self.embedding) > 0


def rank_search_results(results: List[SearchResult], 
                       max_results: Optional[int] = None) -> List[SearchResult]:
    """
    Rank and filter search results by confidence score.
    
    Args:
        results: List of SearchResult objects to rank
        max_results: Maximum number of results to return (optional)
        
    Returns:
        Sorted list of search results in descending order of confidence
    """
    if not results:
        return []
    
    # Sort by confidence score (descending)
    sorted_results = sorted(results, key=lambda x: x.confidence_score, reverse=True)
    
    # Limit results if specified
    if max_results is not None and max_results > 0:
        sorted_results = sorted_results[:max_results]
    
    return sorted_results


def filter_results_by_threshold(results: List[SearchResult], 
                               threshold: float = 0.1) -> List[SearchResult]:
    """
    Filter search results by minimum confidence threshold.
    
    Args:
        results: List of SearchResult objects to filter
        threshold: Minimum confidence score to include (0-1)
        
    Returns:
        Filtered list of results above threshold
    """
    if not (0 <= threshold <= 1):
        raise ValueError("Threshold must be between 0 and 1")
    
    return [result for result in results if result.confidence_score >= threshold]