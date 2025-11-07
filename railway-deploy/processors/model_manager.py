"""
CLIP model management for image and text embedding generation.
"""
import torch
import clip
import numpy as np
from PIL import Image
from typing import Union, List, Optional, Tuple
import logging
from pathlib import Path

from ..models.config import AppConfig


class ModelManager:
    """
    Manages CLIP model loading, inference, and preprocessing for architectural image search.
    
    This class handles:
    - CLIP model initialization and device management
    - Image preprocessing pipeline for CLIP compatibility
    - Text and image embedding generation
    - Batch processing capabilities
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize ModelManager with configuration.
        
        Args:
            config: Application configuration containing model settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.device = self._get_device()
        self.model = None
        self.preprocess = None
        
        # Initialize model on creation
        self._load_model()
    
    def _get_device(self) -> torch.device:
        """
        Determine the best available device for model inference.
        
        Returns:
            torch.device: CUDA if available, otherwise CPU
        """
        if torch.cuda.is_available():
            device = torch.device("cuda")
            self.logger.info(f"Using CUDA device: {torch.cuda.get_device_name()}")
        else:
            device = torch.device("cpu")
            self.logger.info("Using CPU device")
        
        return device
    
    def _load_model(self):
        """
        Load CLIP model and preprocessing pipeline.
        
        Raises:
            RuntimeError: If model loading fails
        """
        try:
            self.logger.info(f"Loading CLIP model: {self.config.clip_model_name}")
            self.model, self.preprocess = clip.load(
                self.config.clip_model_name, 
                device=self.device
            )
            self.model.eval()  # Set to evaluation mode
            self.logger.info("CLIP model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load CLIP model: {e}")
            raise RuntimeError(f"Could not load CLIP model '{self.config.clip_model_name}': {e}")
    
    def preprocess_image(self, image_path: Union[str, Path]) -> torch.Tensor:
        """
        Preprocess image for CLIP model inference.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            torch.Tensor: Preprocessed image tensor ready for CLIP
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image cannot be processed
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            processed_image = self.preprocess(image).unsqueeze(0).to(self.device)
            
            self.logger.debug(f"Preprocessed image: {image_path}")
            return processed_image
            
        except Exception as e:
            self.logger.error(f"Failed to preprocess image {image_path}: {e}")
            raise ValueError(f"Could not process image '{image_path}': {e}")
    
    def generate_image_embedding(self, image_path: Union[str, Path]) -> np.ndarray:
        """
        Generate CLIP embedding for a single image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            np.ndarray: Normalized embedding vector
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If embedding generation fails
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call _load_model() first.")
        
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image_path)
            
            # Generate embedding
            with torch.no_grad():
                image_features = self.model.encode_image(processed_image)
                # Normalize the embedding
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                
            # Convert to numpy array
            embedding = image_features.cpu().numpy().flatten()
            
            self.logger.debug(f"Generated embedding for {image_path}, shape: {embedding.shape}")
            return embedding
            
        except Exception as e:
            self.logger.error(f"Failed to generate embedding for {image_path}: {e}")
            raise ValueError(f"Could not generate embedding for '{image_path}': {e}")
    
    def generate_text_embedding(self, text: str) -> np.ndarray:
        """
        Generate CLIP embedding for text description or query.
        
        Args:
            text: Text to encode (query or description)
            
        Returns:
            np.ndarray: Normalized embedding vector
            
        Raises:
            ValueError: If text is empty or embedding generation fails
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call _load_model() first.")
        
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            # Tokenize text
            text_tokens = clip.tokenize([text.strip()]).to(self.device)
            
            # Generate embedding
            with torch.no_grad():
                text_features = self.model.encode_text(text_tokens)
                # Normalize the embedding
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            # Convert to numpy array
            embedding = text_features.cpu().numpy().flatten()
            
            self.logger.debug(f"Generated text embedding for: '{text[:50]}...', shape: {embedding.shape}")
            return embedding
            
        except Exception as e:
            self.logger.error(f"Failed to generate text embedding for '{text}': {e}")
            raise ValueError(f"Could not generate text embedding: {e}")
    
    def generate_batch_image_embeddings(self, image_paths: List[Union[str, Path]]) -> List[np.ndarray]:
        """
        Generate CLIP embeddings for multiple images in batches.
        
        Args:
            image_paths: List of paths to image files
            
        Returns:
            List[np.ndarray]: List of normalized embedding vectors
            
        Raises:
            ValueError: If batch processing fails
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call _load_model() first.")
        
        if not image_paths:
            return []
        
        embeddings = []
        batch_size = self.config.batch_size
        
        self.logger.info(f"Processing {len(image_paths)} images in batches of {batch_size}")
        
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            batch_embeddings = []
            
            try:
                # Process each image in the batch
                batch_tensors = []
                valid_paths = []
                
                for path in batch_paths:
                    try:
                        processed_image = self.preprocess_image(path)
                        batch_tensors.append(processed_image)
                        valid_paths.append(path)
                    except Exception as e:
                        self.logger.warning(f"Skipping image {path}: {e}")
                        continue
                
                if not batch_tensors:
                    continue
                
                # Concatenate batch tensors
                batch_tensor = torch.cat(batch_tensors, dim=0)
                
                # Generate embeddings for the batch
                with torch.no_grad():
                    batch_features = self.model.encode_image(batch_tensor)
                    # Normalize embeddings
                    batch_features = batch_features / batch_features.norm(dim=-1, keepdim=True)
                
                # Convert to numpy arrays
                batch_numpy = batch_features.cpu().numpy()
                for j, embedding in enumerate(batch_numpy):
                    embeddings.append(embedding)
                    self.logger.debug(f"Processed {valid_paths[j]}")
                
            except Exception as e:
                self.logger.error(f"Failed to process batch {i//batch_size + 1}: {e}")
                # Continue with individual processing for this batch
                for path in batch_paths:
                    try:
                        embedding = self.generate_image_embedding(path)
                        embeddings.append(embedding)
                    except Exception as individual_error:
                        self.logger.warning(f"Skipping image {path}: {individual_error}")
                        continue
        
        self.logger.info(f"Successfully processed {len(embeddings)} images")
        return embeddings
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            float: Cosine similarity score between -1 and 1
            
        Raises:
            ValueError: If embeddings have different shapes or are invalid
        """
        if not isinstance(embedding1, np.ndarray) or not isinstance(embedding2, np.ndarray):
            raise ValueError("Both embeddings must be numpy arrays")
        
        if embedding1.shape != embedding2.shape:
            raise ValueError(f"Embedding shapes must match: {embedding1.shape} vs {embedding2.shape}")
        
        if len(embedding1) == 0:
            raise ValueError("Embeddings cannot be empty")
        
        try:
            # Normalize embeddings
            norm1 = embedding1 / np.linalg.norm(embedding1)
            norm2 = embedding2 / np.linalg.norm(embedding2)
            
            # Calculate cosine similarity
            similarity = np.dot(norm1, norm2)
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate similarity: {e}")
            raise ValueError(f"Could not calculate similarity: {e}")
    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.
        
        Returns:
            dict: Model information including name, device, and parameters
        """
        if self.model is None:
            return {"status": "not_loaded"}
        
        try:
            param_count = sum(p.numel() for p in self.model.parameters())
            
            return {
                "status": "loaded",
                "model_name": self.config.clip_model_name,
                "device": str(self.device),
                "parameter_count": param_count,
                "batch_size": self.config.batch_size
            }
        except Exception as e:
            self.logger.error(f"Failed to get model info: {e}")
            return {"status": "error", "error": str(e)}
    
    def cleanup(self):
        """
        Clean up model resources and free memory.
        """
        if self.model is not None:
            del self.model
            self.model = None
        
        if self.preprocess is not None:
            del self.preprocess
            self.preprocess = None
        
        # Clear CUDA cache if using GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.logger.info("Model resources cleaned up")