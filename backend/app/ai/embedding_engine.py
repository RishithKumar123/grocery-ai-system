import json
import numpy as np
import cv2
from typing import List, Dict, Any, Optional
from PIL import Image
from app.core.logging import logger

try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logger.warning("torch package is missing or not installed.")

try:
    from transformers import AutoModel, AutoProcessor, AutoImageProcessor
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logger.warning("transformers package is missing or not installed.")


class EmbeddingEngine:
    """
    Visual embedding engine for product verification.
    
    Supports:
    - SigLIP (Significant Image-Language Pre-training)
    - DINOv2 (Vision Transformers for Self-Supervised Learning)
    - CLIP (Contrastive Language-Image Pre-training)
    
    Generates high-quality visual embeddings for:
    - Reference images (stored in database)
    - Detected product crops (for matching)
    """
    
    def __init__(self, model_name: str = "google/siglip-base-patch16-224"):
        """
        Initialize embedding engine.
        
        Args:
            model_name: Model to use for embeddings
                - "google/siglip-base-patch16-224" (default, recommended)
                - "google/siglip-large-patch16-384"
                - "facebook/dinov2-base" (DINOv2)
                - "facebook/dinov2-large"
                - "openai/clip-vit-base-patch32" (CLIP)
        """
        self.model_name = model_name
        self.model = None
        self.processor = None
        self.device = "cpu"
        self.embedding_dim = None
        
        if HAS_TORCH and HAS_TRANSFORMERS:
            try:
                # Detect GPU availability
                if torch.cuda.is_available():
                    self.device = "cuda"
                    logger.info(f"EmbeddingEngine: GPU (CUDA) detected! Using {self.device}")
                else:
                    self.device = "cpu"
                    logger.info(f"EmbeddingEngine: GPU not available. Using {self.device}")
                
                # Load model and processor
                if "siglip" in model_name.lower():
                    self.model = AutoModel.from_pretrained(model_name).to(self.device)
                    self.processor = AutoImageProcessor.from_pretrained(model_name)
                    self.embedding_dim = 768  # SigLIP base dimension
                    logger.info(f"EmbeddingEngine: SigLIP model loaded: {model_name}")
                elif "dinov2" in model_name.lower():
                    self.model = AutoModel.from_pretrained(model_name).to(self.device)
                    self.processor = AutoImageProcessor.from_pretrained(model_name)
                    self.embedding_dim = 768  # DINOv2 base dimension
                    logger.info(f"EmbeddingEngine: DINOv2 model loaded: {model_name}")
                elif "clip" in model_name.lower():
                    self.model = AutoModel.from_pretrained(model_name).to(self.device)
                    self.processor = AutoImageProcessor.from_pretrained(model_name)
                    self.embedding_dim = 512  # CLIP base dimension
                    logger.info(f"EmbeddingEngine: CLIP model loaded: {model_name}")
                else:
                    # Default to SigLIP
                    self.model = AutoModel.from_pretrained("google/siglip-base-patch16-224").to(self.device)
                    self.processor = AutoImageProcessor.from_pretrained("google/siglip-base-patch16-224")
                    self.embedding_dim = 768
                    logger.info(f"EmbeddingEngine: Default SigLIP model loaded")
                
                self.model.eval()
                
            except Exception as e:
                logger.error(f"EmbeddingEngine: Failed to load model: {str(e)}")
                self.model = None
        else:
            logger.warning("EmbeddingEngine: Required packages not available")
    
    def generate_embedding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Generate embedding for a single image.
        
        Args:
            image: BGR image array (OpenCV format)
        
        Returns:
            Normalized embedding vector (numpy array) or None
        """
        if self.model is None:
            logger.error("EmbeddingEngine: Model not loaded")
            return None
        
        try:
            # Convert BGR to RGB
            if len(image.shape) == 3 and image.shape[2] == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = image
            
            # Convert to PIL Image
            pil_image = Image.fromarray(rgb_image)
            
            # Preprocess
            inputs = self.processor(images=pil_image, return_tensors="pt").to(self.device)
            
            # Generate embedding
            with torch.no_grad():
                if "siglip" in self.model_name.lower():
                    # SigLIP: use image embeddings from vision model
                    outputs = self.model(**inputs)
                    embedding = outputs.image_embeds
                elif "dinov2" in self.model_name.lower():
                    # DINOv2: use pooler output
                    outputs = self.model(**inputs)
                    embedding = outputs.pooler_output
                elif "clip" in self.model_name.lower():
                    # CLIP: use image features
                    outputs = self.model.get_image_features(**inputs)
                    embedding = outputs
                else:
                    # Default: use last hidden state pooled
                    outputs = self.model(**inputs)
                    embedding = outputs.last_hidden_state.mean(dim=1)
            
            # Convert to numpy and normalize
            embedding_np = embedding.squeeze().cpu().numpy()
            
            # L2 normalize
            norm = np.linalg.norm(embedding_np)
            if norm > 0:
                embedding_np = embedding_np / norm
            
            return embedding_np
            
        except Exception as e:
            logger.error(f"EmbeddingEngine: Error generating embedding: {str(e)}")
            return None
    
    def generate_batch_embeddings(self, images: List[np.ndarray]) -> List[Optional[np.ndarray]]:
        """
        Generate embeddings for multiple images.
        
        Args:
            images: List of BGR image arrays
        
        Returns:
            List of embedding vectors (or None for failed images)
        """
        embeddings = []
        for img in images:
            emb = self.generate_embedding(img)
            embeddings.append(emb)
        return embeddings
    
    def calculate_similarity(
        self, 
        embedding1: np.ndarray, 
        embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
        
        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        if embedding1 is None or embedding2 is None:
            return 0.0
        
        try:
            # Ensure both are normalized
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 > 0:
                embedding1 = embedding1 / norm1
            if norm2 > 0:
                embedding2 = embedding2 / norm2
            
            # Cosine similarity (dot product of normalized vectors)
            similarity = float(np.dot(embedding1, embedding2))
            
            # Clip to [0, 1] range
            similarity = max(0.0, min(1.0, similarity))
            
            return similarity
            
        except Exception as e:
            logger.error(f"EmbeddingEngine: Error calculating similarity: {str(e)}")
            return 0.0
    
    def find_best_match(
        self, 
        query_embedding: np.ndarray, 
        reference_embeddings: List[np.ndarray],
        threshold: float = 0.75
    ) -> Dict[str, Any]:
        """
        Find best matching reference embedding.
        
        Args:
            query_embedding: Query embedding vector
            reference_embeddings: List of reference embedding vectors
            threshold: Minimum similarity threshold
        
        Returns:
            {
                "best_index": int or None,
                "best_similarity": float,
                "above_threshold": bool
            }
        """
        if not reference_embeddings:
            return {
                "best_index": None,
                "best_similarity": 0.0,
                "above_threshold": False
            }
        
        best_similarity = -1.0
        best_index = None
        
        for idx, ref_emb in enumerate(reference_embeddings):
            if ref_emb is None:
                continue
            
            similarity = self.calculate_similarity(query_embedding, ref_emb)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_index = idx
        
        return {
            "best_index": best_index,
            "best_similarity": best_similarity,
            "above_threshold": best_similarity >= threshold
        }
    
    def embedding_to_json(self, embedding: np.ndarray) -> str:
        """Convert embedding to JSON string for storage."""
        if embedding is None:
            return "[]"
        return json.dumps(embedding.tolist())
    
    def embedding_from_json(self, json_str: str) -> Optional[np.ndarray]:
        """Convert JSON string back to embedding."""
        try:
            data = json.loads(json_str)
            return np.array(data)
        except Exception as e:
            logger.error(f"EmbeddingEngine: Error parsing embedding JSON: {str(e)}")
            return None
    
    def get_embedding_dimension(self) -> Optional[int]:
        """Return the dimension of the embedding vectors."""
        return self.embedding_dim
