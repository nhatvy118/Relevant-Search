"""
Image Retrieval Module with Relevance Feedback
Implements Rocchio method for query reformulation
"""

import numpy as np
from typing import List, Tuple, Set
from scipy.spatial.distance import cosine


class ImageRetrieval:
    """Image retrieval system with relevance feedback"""
    
    def __init__(self, features: np.ndarray, image_paths: List[str]):
        """
        Initialize retrieval system
        
        Args:
            features: Feature matrix (N x D) where N is number of images, D is feature dimension
            image_paths: List of image paths corresponding to features
        """
        self.features = features
        self.image_paths = image_paths
        self.normalized_features = self._normalize_features(features)
        
        # Current query vector
        self.current_query: np.ndarray = None
        
        # Feedback history
        self.relevant_images: Set[int] = set()
        self.irrelevant_images: Set[int] = set()
        
        # Rocchio parameters (recommended values from slide)
        self.alpha = 1.0  # Weight for original query
        self.beta = 0.75  # Weight for relevant documents
        self.gamma = 0.25  # Weight for irrelevant documents
    
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
    
    def initial_query(self, query_image_idx: int) -> np.ndarray:
        """
        Create initial query from an image
        
        Args:
            query_image_idx: Index of query image in the dataset
            
        Returns:
            Query vector
        """
        if query_image_idx < 0 or query_image_idx >= len(self.image_paths):
            raise ValueError(f"Invalid image index: {query_image_idx}")
        
        self.current_query = self.normalized_features[query_image_idx].copy()
        self.relevant_images = set()
        self.irrelevant_images = set()
        
        return self.current_query
    
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
    
    def clear_feedback(self):
        """Clear all feedback"""
        self.relevant_images = set()
        self.irrelevant_images = set()
    
    def reformulate_query(self) -> np.ndarray:
        """
        Reformulate query using Rocchio method
        
        Returns:
            Reformulated query vector
        """
        if self.current_query is None:
            raise ValueError("No initial query set. Call initial_query() first.")
        
        # Start with original query
        new_query = self.alpha * self.current_query
        
        # Add relevant documents
        if len(self.relevant_images) > 0:
            relevant_features = self.normalized_features[list(self.relevant_images)]
            relevant_center = np.mean(relevant_features, axis=0)
            new_query += (self.beta / len(self.relevant_images)) * relevant_center
        
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
            raise ValueError("No query set. Call initial_query() first.")
        
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
            'relevant_indices': list(self.relevant_images),
            'irrelevant_indices': list(self.irrelevant_images)
        }

