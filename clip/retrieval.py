"""
Text-based Image Retrieval Module with Relevance Feedback
Uses CLIP embeddings and implements Rocchio method for query reformulation
"""

import numpy as np
from typing import List, Tuple, Set
from .extractor import CLIPExtractor


class TextRetrieval:
    """Text-based image retrieval system with relevance feedback using CLIP"""
    
    def __init__(self, features: np.ndarray, image_paths: List[str], clip_model: str = "ViT-B/32"):
        """
        Initialize text-based retrieval system
        
        Args:
            features: CLIP feature matrix (N x D) where N is number of images, D is feature dimension
            image_paths: List of image paths corresponding to features
            clip_model: CLIP model name
        """
        self.features = features
        self.image_paths = image_paths
        self.normalized_features = self._normalize_features(features)
        
        # CLIP extractor for text queries
        self.clip_extractor = CLIPExtractor(model_name=clip_model)
        
        # Current query vector (can be from text or image)
        self.current_query: np.ndarray = None
        self.original_query: np.ndarray = None  # Store original query for Rocchio
        
        # Feedback history
        self.relevant_images: Set[int] = set()
        self.irrelevant_images: Set[int] = set()
        self.text_feedback_texts: List[str] = []  # Text feedback descriptions
        
        # Rocchio parameters
        self.alpha = 1.0  # Weight for original query
        self.beta = 0.75  # Weight for relevant documents
        self.gamma = 0.25  # Weight for irrelevant documents
        self.text_feedback_weight = 0.5  # Weight for text feedback
    
    def _normalize_features(self, features: np.ndarray) -> np.ndarray:
        """Normalize features to unit vectors"""
        norms = np.linalg.norm(features, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        return features / norms
    
    def set_rocchio_params(self, alpha: float = 1.0, beta: float = 0.75, gamma: float = 0.25):
        """
        Set Rocchio method parameters
        
        Args:
            alpha: Weight for original query
            beta: Weight for relevant documents
            gamma: Weight for irrelevant documents
        """
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
    
    def initial_query_from_text(self, text_query: str):
        """
        Create initial query from text using CLIP
        
        Args:
            text_query: Text query string
        """
        # Extract text features using CLIP
        text_features = self.clip_extractor.extract_text_features(text_query)
        
        # Normalize
        norm = np.linalg.norm(text_features)
        if norm > 0:
            text_features = text_features / norm
        
        self.original_query = text_features.copy()
        self.current_query = text_features.copy()
        self.relevant_images = set()
        self.irrelevant_images = set()
    
    def initial_query_from_image(self, image_path: str):
        """
        Create initial query from image using CLIP
        
        Args:
            image_path: Path to query image
        """
        # Extract image features using CLIP
        image_features = self.clip_extractor.extract_image_features(image_path)
        
        # Normalize
        norm = np.linalg.norm(image_features)
        if norm > 0:
            image_features = image_features / norm
        
        self.original_query = image_features.copy()
        self.current_query = image_features.copy()
        self.relevant_images = set()
        self.irrelevant_images = set()
    
    def initial_query_from_image_pil(self, image):
        """
        Create initial query from PIL Image using CLIP
        
        Args:
            image: PIL Image object
        """
        # Extract image features using CLIP
        image_features = self.clip_extractor.extract_image_features_from_pil(image)
        
        # Normalize
        norm = np.linalg.norm(image_features)
        if norm > 0:
            image_features = image_features / norm
        
        self.original_query = image_features.copy()
        self.current_query = image_features.copy()
        self.relevant_images = set()
        self.irrelevant_images = set()
    
    def initial_query_from_features(self, query_features: np.ndarray):
        """
        Create initial query from feature vector
        
        Args:
            query_features: Feature vector
        """
        # Normalize query features
        norm = np.linalg.norm(query_features)
        if norm > 0:
            query_features = query_features / norm
        
        self.original_query = query_features.copy()
        self.current_query = query_features.copy()
        self.relevant_images = set()
        self.irrelevant_images = set()
    
    def add_feedback(self, image_idx: int, is_relevant: bool):
        """
        Add relevance feedback for an image
        
        Args:
            image_idx: Index of image in dataset
            is_relevant: True if relevant, False if irrelevant
        """
        if image_idx < 0 or image_idx >= len(self.image_paths):
            raise ValueError(f"Invalid image index: {image_idx}")
        
        if is_relevant:
            self.relevant_images.add(image_idx)
            # Remove from irrelevant if it was there
            self.irrelevant_images.discard(image_idx)
        else:
            self.irrelevant_images.add(image_idx)
            # Remove from relevant if it was there
            self.relevant_images.discard(image_idx)
    
    def remove_feedback(self, image_idx: int):
        """
        Remove feedback for an image
        
        Args:
            image_idx: Index of image
        """
        self.relevant_images.discard(image_idx)
        self.irrelevant_images.discard(image_idx)
    
    def add_text_feedback(self, text_description: str):
        """
        Add text feedback description
        
        Args:
            text_description: Text description to improve query (e.g., "red dress", "blue jeans")
        """
        if text_description and text_description.strip():
            self.text_feedback_texts.append(text_description.strip())
    
    def clear_text_feedback(self):
        """Clear all text feedback"""
        self.text_feedback_texts = []
    
    def clear_feedback(self):
        """Clear all feedback (images and text)"""
        self.relevant_images = set()
        self.irrelevant_images = set()
        self.text_feedback_texts = []
        # Reset query to original
        if self.original_query is not None:
            self.current_query = self.original_query.copy()
    
    def reformulate_query(self) -> np.ndarray:
        """
        Reformulate query using Rocchio method with text feedback
        
        Returns:
            Reformulated query vector
        """
        if self.original_query is None:
            raise ValueError("No initial query set. Call initial_query_from_text() or initial_query_from_image() first.")
        
        # Start with original query
        new_query = self.alpha * self.original_query
        
        # Add relevant documents
        if len(self.relevant_images) > 0:
            relevant_features = self.normalized_features[list(self.relevant_images)]
            relevant_center = np.mean(relevant_features, axis=0)
            new_query += (self.beta / len(self.relevant_images)) * relevant_center
        
        # Add text feedback (convert text descriptions to CLIP embeddings)
        if len(self.text_feedback_texts) > 0:
            text_embeddings = []
            for text_desc in self.text_feedback_texts:
                try:
                    text_features = self.clip_extractor.extract_text_features(text_desc)
                    text_embeddings.append(text_features)
                except Exception as e:
                    print(f"Warning: Could not process text feedback '{text_desc}': {e}")
                    continue
            
            if len(text_embeddings) > 0:
                text_embeddings = np.array(text_embeddings)
                # Normalize text embeddings
                norms = np.linalg.norm(text_embeddings, axis=1, keepdims=True)
                norms[norms == 0] = 1
                text_embeddings = text_embeddings / norms
                
                # Average text embeddings
                text_center = np.mean(text_embeddings, axis=0)
                new_query += (self.text_feedback_weight / len(text_embeddings)) * text_center
        
        # Subtract irrelevant documents
        if len(self.irrelevant_images) > 0:
            irrelevant_features = self.normalized_features[list(self.irrelevant_images)]
            irrelevant_center = np.mean(irrelevant_features, axis=0)
            new_query -= (self.gamma / len(self.irrelevant_images)) * irrelevant_center
        
        # Normalize
        norm = np.linalg.norm(new_query)
        if norm > 0:
            new_query = new_query / norm
        
        self.current_query = new_query
        return new_query
    
    def search(self, top_k: int = 20, exclude_feedback: bool = True) -> List[Tuple[int, float]]:
        """
        Search for similar images using current query
        
        Args:
            top_k: Number of results to return
            exclude_feedback: Exclude images that have been marked as relevant/irrelevant
            
        Returns:
            List of (image_idx, similarity_score) tuples, sorted by similarity
        """
        if self.current_query is None:
            raise ValueError("No query set. Call initial_query_from_text() or initial_query_from_image() first.")
        
        # Calculate cosine similarity
        similarities = np.dot(self.normalized_features, self.current_query)
        
        # Create list of (idx, similarity) pairs
        results = [(i, float(sim)) for i, sim in enumerate(similarities)]
        
        # Exclude feedback images if requested
        if exclude_feedback:
            exclude_set = self.relevant_images | self.irrelevant_images
            results = [(idx, sim) for idx, sim in results if idx not in exclude_set]
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k
        return results[:top_k]
    
    def get_feedback_summary(self) -> dict:
        """Get summary of current feedback"""
        return {
            'relevant_count': len(self.relevant_images),
            'irrelevant_count': len(self.irrelevant_images),
            'text_feedback_count': len(self.text_feedback_texts),
            'text_feedback_texts': self.text_feedback_texts.copy(),
            'relevant_indices': list(self.relevant_images),
            'irrelevant_indices': list(self.irrelevant_images)
        }

