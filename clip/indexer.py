"""
Text Indexing Module using CLIP
Save and load CLIP image embeddings for text-based retrieval
"""

import numpy as np
import pickle
import os
from pathlib import Path
from typing import List, Tuple, Optional
from .extractor import CLIPExtractor


class TextIndexer:
    """Index and manage CLIP image embeddings for text-based retrieval"""
    
    def __init__(self, index_file: str = "text_index.pkl", clip_model: str = "ViT-B/32"):
        self.index_file = index_file
        self.image_paths: List[str] = []
        self.features: Optional[np.ndarray] = None
        self.extractor = CLIPExtractor(model_name=clip_model)
    
    def build_index(self, image_folder: str, max_images: int = None, force_rebuild: bool = False):
        """
        Build CLIP index from image folder
        
        Args:
            image_folder: Path to folder containing images
            max_images: Maximum number of images to index
            force_rebuild: Force rebuild even if index exists
        """
        # Check if index exists
        if os.path.exists(self.index_file) and not force_rebuild:
            print(f"Index file {self.index_file} already exists. Use force_rebuild=True to rebuild.")
            return
        
        print(f"Building CLIP index from {image_folder}...")
        self.image_paths, self.features = self.extractor.extract_features_from_folder(
            image_folder, max_images=max_images
        )
        
        # Save index
        self.save_index()
        print(f"CLIP index built and saved to {self.index_file}")
    
    def save_index(self):
        """Save CLIP index to disk"""
        index_data = {
            'image_paths': self.image_paths,
            'features': self.features,
            'index_type': 'clip'
        }
        
        with open(self.index_file, 'wb') as f:
            pickle.dump(index_data, f)
    
    def load_index(self) -> bool:
        """
        Load CLIP index from disk
        
        Returns:
            True if loaded successfully, False otherwise
        """
        if not os.path.exists(self.index_file):
            print(f"Index file {self.index_file} not found.")
            return False
        
        try:
            with open(self.index_file, 'rb') as f:
                index_data = pickle.load(f)
            
            self.image_paths = index_data['image_paths']
            self.features = index_data['features']
            
            print(f"Loaded CLIP index with {len(self.image_paths)} images")
            print(f"Feature dimension: {self.features.shape[1]}")
            return True
        except Exception as e:
            print(f"Error loading CLIP index: {e}")
            return False
    
    def get_image_paths(self) -> List[str]:
        """Get list of indexed image paths"""
        return self.image_paths
    
    def get_features(self) -> np.ndarray:
        """Get feature matrix"""
        if self.features is None:
            raise ValueError("Index not loaded. Call load_index() first.")
        return self.features
    
    def get_image_count(self) -> int:
        """Get number of indexed images"""
        return len(self.image_paths) if self.image_paths else 0
    
    def add_image(self, image_path: str) -> bool:
        """
        Add a single image to the index
        
        Args:
            image_path: Path to image file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            features = self.extractor.extract_image_features(image_path)
            
            if self.features is None:
                self.features = features.reshape(1, -1)
                self.image_paths = [image_path]
            else:
                self.features = np.vstack([self.features, features])
                self.image_paths.append(image_path)
            
            return True
        except Exception as e:
            print(f"Error adding image {image_path}: {e}")
            return False

