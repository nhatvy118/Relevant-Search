"""
CLIP Feature Extraction Module
Extract image and text embeddings using CLIP model
"""

import torch
import numpy as np
from PIL import Image
from pathlib import Path
from typing import List, Tuple, Union
import os
import sys
import importlib.util

# Import CLIP package (clip-by-openai) - avoid conflict with local clip module
# The local clip/ directory conflicts with the clip-by-openai package
# Solution: Import CLIP package with a different approach
_original_path = list(sys.path)
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)

# Find site-packages path
_site_packages_path = None
for path in sys.path:
    if 'site-packages' in path and os.path.exists(os.path.join(path, 'clip')):
        _site_packages_path = path
        break

if _site_packages_path:
    # Save and remove local clip from sys.modules temporarily
    _local_clip = sys.modules.pop('clip', None)
    
    # Temporarily modify sys.path to prioritize site-packages
    sys.path.insert(0, _site_packages_path)
    # Remove current directory from path
    if '.' in sys.path:
        sys.path.remove('.')
    if _project_root in sys.path:
        sys.path.remove(_project_root)
    
    try:
        # Import the actual CLIP package from site-packages
        import clip as _openai_clip
        # Verify it has the load function
        if not hasattr(_openai_clip, 'load'):
            raise ImportError("Imported clip module does not have 'load' function")
        # Use the imported module
        clip = _openai_clip
    finally:
        # Restore original path
        sys.path = _original_path
        # Restore local clip module to sys.modules for other imports
        if _local_clip is not None:
            sys.modules['clip'] = _local_clip
else:
    raise ImportError("Could not find clip-by-openai package in site-packages")


class CLIPExtractor:
    """Extract CLIP embeddings for images and text"""
    
    def __init__(self, model_name: str = "ViT-B/32", device: str = None):
        """
        Initialize CLIP extractor
        
        Args:
            model_name: CLIP model name (default: "ViT-B/32")
            device: Device to use ('cuda' or 'cpu'). Auto-detect if None
        """
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        print(f"Loading CLIP model {model_name} on {self.device}...")
        # Use jit=False for compatibility with newer torch versions
        self.model, self.preprocess = clip.load(model_name, device=self.device, jit=False)
        self.model.eval()  # Set to evaluation mode
        print(f"CLIP model loaded successfully")
    
    def extract_image_features(self, image_path: str) -> np.ndarray:
        """
        Extract CLIP features from an image
        
        Args:
            image_path: Path to image file
            
        Returns:
            Normalized feature vector (512-dim for ViT-B/32)
        """
        try:
            image = Image.open(image_path).convert("RGB")
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                image_features = self.model.encode_image(image_tensor)
                # Normalize features
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy().flatten()
        except Exception as e:
            raise ValueError(f"Error extracting features from {image_path}: {e}")
    
    def extract_image_features_from_pil(self, image: Image.Image) -> np.ndarray:
        """
        Extract CLIP features from PIL Image object
        
        Args:
            image: PIL Image object
            
        Returns:
            Normalized feature vector
        """
        try:
            image_rgb = image.convert("RGB")
            image_tensor = self.preprocess(image_rgb).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                image_features = self.model.encode_image(image_tensor)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy().flatten()
        except Exception as e:
            raise ValueError(f"Error extracting features from PIL image: {e}")
    
    def extract_text_features(self, text: str) -> np.ndarray:
        """
        Extract CLIP features from text
        
        Args:
            text: Text string
            
        Returns:
            Normalized feature vector
        """
        try:
            text_tokens = clip.tokenize([text]).to(self.device)
            
            with torch.no_grad():
                text_features = self.model.encode_text(text_tokens)
                # Normalize features
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            return text_features.cpu().numpy().flatten()
        except Exception as e:
            raise ValueError(f"Error extracting features from text '{text}': {e}")
    
    def extract_features_from_folder(self, folder_path: str, max_images: int = None) -> Tuple[List[str], np.ndarray]:
        """
        Extract CLIP features from all images in a folder
        
        Args:
            folder_path: Path to folder containing images
            max_images: Maximum number of images to process (None for all)
            
        Returns:
            Tuple of (image_paths, feature_matrix)
        """
        folder = Path(folder_path)
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
        
        # Get all image files
        image_paths = []
        for ext in image_extensions:
            image_paths.extend(list(folder.glob(f'*{ext}')))
            image_paths.extend(list(folder.glob(f'*{ext.upper()}')))
        
        image_paths = sorted([str(p) for p in image_paths])
        
        if max_images:
            image_paths = image_paths[:max_images]
        
        print(f"Found {len(image_paths)} images. Extracting CLIP features...")
        
        features_list = []
        valid_paths = []
        
        for i, img_path in enumerate(image_paths):
            try:
                features = self.extract_image_features(img_path)
                features_list.append(features)
                valid_paths.append(img_path)
                
                if (i + 1) % 100 == 0:
                    print(f"Processed {i + 1}/{len(image_paths)} images...")
            except Exception as e:
                print(f"Error processing {img_path}: {e}")
                continue
        
        if not features_list:
            raise ValueError("No valid images found in folder")
        
        feature_matrix = np.array(features_list)
        print(f"Extracted CLIP features from {len(valid_paths)} images")
        print(f"Feature vector dimension: {feature_matrix.shape[1]}")
        
        return valid_paths, feature_matrix
    
    def get_feature_dimension(self) -> int:
        """Get the dimension of CLIP features"""
        # ViT-B/32 has 512 dimensions
        return 512

