"""
Standalone script to build index from image folder
Useful for building index without GUI
"""

import argparse
import sys
from indexer import ImageIndexer


def main():
    parser = argparse.ArgumentParser(description='Build image index for retrieval')
    parser.add_argument('--folder', type=str, required=True,
                       help='Path to folder containing images')
    parser.add_argument('--max-images', type=int, default=None,
                       help='Maximum number of images to index (default: all)')
    parser.add_argument('--output', type=str, default='image_index.pkl',
                       help='Output index file (default: image_index.pkl)')
    parser.add_argument('--force', action='store_true',
                       help='Force rebuild even if index exists')
    
    args = parser.parse_args()
    
    print(f"Building index from: {args.folder}")
    print(f"Output file: {args.output}")
    if args.max_images:
        print(f"Maximum images: {args.max_images}")
    else:
        print("Processing all images...")
    
    indexer = ImageIndexer(index_file=args.output)
    
    try:
        indexer.build_index(args.folder, max_images=args.max_images, force_rebuild=args.force)
        print(f"\n✓ Index built successfully!")
        print(f"  Total images: {indexer.get_image_count()}")
        print(f"  Feature dimension: {indexer.features.shape[1]}")
        print(f"  Index saved to: {args.output}")
    except Exception as e:
        print(f"\n✗ Error building index: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

