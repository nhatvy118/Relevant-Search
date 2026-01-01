"""
Feature Extraction Module
Extract color, intensity, and texture features from images
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple
import os


class FeatureExtractor:
    """Extract features from images for retrieval"""
    
    def __init__(self):
        self.color_bins = 32  # Number of bins for color histogram
        self.intensity_bins = 32  # Number of bins for intensity histogram
        
    def extract_color_histogram(self, image: np.ndarray) -> np.ndarray:
        """
        Extract color histogram from image (RGB)
        
        Args:
            image: Input image (BGR format from OpenCV)
            
        Returns:
            Color histogram feature vector
        """
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Calculate histogram for each channel
        hist_r = cv2.calcHist([rgb_image], [0], None, [self.color_bins], [0, 256])
        hist_g = cv2.calcHist([rgb_image], [1], None, [self.color_bins], [0, 256])
        hist_b = cv2.calcHist([rgb_image], [2], None, [self.color_bins], [0, 256])
        
        # Normalize histograms
        hist_r = hist_r / (hist_r.sum() + 1e-7)
        hist_g = hist_g / (hist_g.sum() + 1e-7)
        hist_b = hist_b / (hist_b.sum() + 1e-7)
        
        # Concatenate
        color_hist = np.concatenate([hist_r.flatten(), hist_g.flatten(), hist_b.flatten()])
        
        return color_hist
    
    def extract_intensity_histogram(self, image: np.ndarray) -> np.ndarray:
        """
        Extract intensity histogram from grayscale image
        
        Args:
            image: Input image (BGR format from OpenCV)
            
        Returns:
            Intensity histogram feature vector
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate histogram
        hist = cv2.calcHist([gray], [0], None, [self.intensity_bins], [0, 256])
        
        # Normalize
        hist = hist / (hist.sum() + 1e-7)
        
        return hist.flatten()
    
    def extract_texture_features(self, image: np.ndarray) -> np.ndarray:
        """
        Extract texture features using Local Binary Pattern (LBP) and GLCM
        
        Args:
            image: Input image (BGR format from OpenCV)
            
        Returns:
            Texture feature vector
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Simple texture features: standard deviation and mean of gradients
        # Calculate gradients
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # Calculate gradient magnitude
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # Extract statistics
        texture_features = np.array([
            np.mean(gradient_magnitude),
            np.std(gradient_magnitude),
            np.mean(gray),
            np.std(gray)
        ])
        
        # Normalize
        texture_features = texture_features / (texture_features.max() + 1e-7)
        
        return texture_features
    
    def extract_features(self, image_path: str) -> np.ndarray:
        """
        Extract all features from an image
        
        Args:
            image_path: Path to image file
            
        Returns:
            Combined feature vector
        """
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Extract features
        color_hist = self.extract_color_histogram(image)
        intensity_hist = self.extract_intensity_histogram(image)
        texture_features = self.extract_texture_features(image)
        
        # Combine all features
        features = np.concatenate([color_hist, intensity_hist, texture_features])
        
        return features
    
    def extract_features_from_folder(self, folder_path: str, max_images: int = None) -> Tuple[List[str], np.ndarray]:
        """
        Extract features from all images in a folder
        
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
        
        print(f"Found {len(image_paths)} images. Extracting features...")
        
        features_list = []
        valid_paths = []
        
        for i, img_path in enumerate(image_paths):
            try:
                features = self.extract_features(img_path)
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
        print(f"Extracted features from {len(valid_paths)} images")
        print(f"Feature vector dimension: {feature_matrix.shape[1]}")
        
        return valid_paths, feature_matrix

