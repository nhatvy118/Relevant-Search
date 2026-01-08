"""
Standalone script to build CLIP index from image folder
Useful for building CLIP index without GUI
"""

import argparse
import sys
from clip import TextIndexer


def main():
    parser = argparse.ArgumentParser(description='Build CLIP index for text-based image retrieval')
    parser.add_argument('--folder', type=str, required=True,
                       help='Path to folder containing images')
    parser.add_argument('--max-images', type=int, default=None,
                       help='Maximum number of images to index (default: all)')
    parser.add_argument('--output', type=str, default='text_index.pkl',
                       help='Output index file (default: text_index.pkl)')
    parser.add_argument('--force', action='store_true',
                       help='Force rebuild even if index exists')
    
    args = parser.parse_args()
    
    print(f"Building CLIP index from: {args.folder}")
    print(f"Output file: {args.output}")
    if args.max_images:
        print(f"Maximum images: {args.max_images}")
    else:
        print("Processing all images...")
    print("Note: This may take a while as CLIP model needs to process each image...")
    
    indexer = TextIndexer(index_file=args.output)
    
    try:
        indexer.build_index(args.folder, max_images=args.max_images, force_rebuild=args.force)
        print(f"\n✓ CLIP index built successfully!")
        print(f"  Total images: {indexer.get_image_count()}")
        print(f"  Feature dimension: {indexer.features.shape[1]}")
        print(f"  Index saved to: {args.output}")
    except Exception as e:
        print(f"\n✗ Error building CLIP index: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

