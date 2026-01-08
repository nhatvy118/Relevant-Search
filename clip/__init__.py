"""
CLIP-based Image Retrieval Method
Uses CLIP embeddings for text and image retrieval
"""

from .extractor import CLIPExtractor
from .indexer import TextIndexer
from .retrieval import TextRetrieval

__all__ = ['CLIPExtractor', 'TextIndexer', 'TextRetrieval']

