"""
Image metadata model for storing and managing architectural image information.
"""
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
import json
import numpy as np


@dataclass
class ImageMetadata:
    """
    Represents metadata for an architectural image including embeddings and descriptions.
    
    Attributes:
        path: File path to the image
        embedding: CLIP embedding vector for the image
        description: Human-readable description of architectural features
        features: List of extracted architectural features
        file_size: Size of the image file in bytes
        dimensions: Image dimensions as (width, height)
        processed_date: When the image was processed
    """
    path: str
    embedding: np.ndarray
    description: str
    features: List[str]
    file_size: Optional[int] = None
    dimensions: Optional[Tuple[int, int]] = None
    processed_date: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate required fields and data types after initialization."""
        if not self.path:
            raise ValueError("Image path is required")
        
        if not isinstance(self.path, str):
            raise TypeError("Image path must be a string")
            
        if self.embedding is None or len(self.embedding) == 0:
            raise ValueError("Image embedding is required")
            
        if not isinstance(self.embedding, np.ndarray):
            raise TypeError("Embedding must be a numpy array")
            
        if not self.description:
            raise ValueError("Image description is required")
            
        if not isinstance(self.description, str):
            raise TypeError("Description must be a string")
            
        if not isinstance(self.features, list):
            raise TypeError("Features must be a list")
            
        if self.dimensions is not None:
            if not isinstance(self.dimensions, tuple) or len(self.dimensions) != 2:
                raise TypeError("Dimensions must be a tuple of (width, height)")
                
        if self.processed_date is None:
            self.processed_date = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ImageMetadata to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation with embedding converted to list
        """
        data = asdict(self)
        # Convert numpy array to list for JSON serialization
        data['embedding'] = self.embedding.tolist()
        # Convert datetime to ISO string
        if self.processed_date:
            data['processed_date'] = self.processed_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImageMetadata':
        """
        Create ImageMetadata instance from dictionary.
        
        Args:
            data: Dictionary containing metadata fields
            
        Returns:
            ImageMetadata instance
            
        Raises:
            ValueError: If required fields are missing
            TypeError: If data types are incorrect
        """
        # Validate required fields
        required_fields = ['path', 'embedding', 'description', 'features']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Required field '{field}' is missing")
        
        # Convert embedding list back to numpy array
        if isinstance(data['embedding'], list):
            data['embedding'] = np.array(data['embedding'], dtype=np.float32)
        
        # Convert ISO string back to datetime
        if 'processed_date' in data and isinstance(data['processed_date'], str):
            data['processed_date'] = datetime.fromisoformat(data['processed_date'])
        
        # Convert dimensions list back to tuple
        if 'dimensions' in data and isinstance(data['dimensions'], list):
            data['dimensions'] = tuple(data['dimensions'])
        
        return cls(**data)
    
    def to_json(self) -> str:
        """
        Serialize ImageMetadata to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ImageMetadata':
        """
        Deserialize ImageMetadata from JSON string.
        
        Args:
            json_str: JSON string containing metadata
            
        Returns:
            ImageMetadata instance
            
        Raises:
            json.JSONDecodeError: If JSON is invalid
            ValueError: If required fields are missing
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def get_embedding_similarity(self, other_embedding: np.ndarray) -> float:
        """
        Calculate cosine similarity between this image's embedding and another.
        
        Args:
            other_embedding: Another embedding vector to compare against
            
        Returns:
            Cosine similarity score between 0 and 1
        """
        if not isinstance(other_embedding, np.ndarray):
            raise TypeError("Other embedding must be a numpy array")
            
        # Normalize vectors
        norm_self = self.embedding / np.linalg.norm(self.embedding)
        norm_other = other_embedding / np.linalg.norm(other_embedding)
        
        # Calculate cosine similarity
        similarity = np.dot(norm_self, norm_other)
        return float(similarity)