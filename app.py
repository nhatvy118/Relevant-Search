"""
Flask Backend API for Image Retrieval with Relevance Feedback
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from pathlib import Path
import base64
from PIL import Image
import io

from indexer import ImageIndexer
from retrieval import ImageRetrieval
from feature_extractor import FeatureExtractor

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)  # Enable CORS for all routes

# Global variables
indexer = ImageIndexer()
retrieval = None
extractor = FeatureExtractor()

# Configuration
IMAGES_FOLDER = 'images'
INDEX_FILE = 'image_index.pkl'


@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('static', 'index.html')


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    has_index = os.path.exists(INDEX_FILE)
    image_count = indexer.get_image_count() if has_index else 0
    
    return jsonify({
        'has_index': has_index,
        'image_count': image_count,
        'index_file': INDEX_FILE
    })


@app.route('/api/build_index', methods=['POST'])
def build_index():
    """Build index from image folder"""
    try:
        data = request.json
        image_folder = data.get('folder', IMAGES_FOLDER)
        max_images = data.get('max_images', None)
        force_rebuild = data.get('force_rebuild', False)
        
        if not os.path.exists(image_folder):
            return jsonify({'error': f'Folder not found: {image_folder}'}), 400
        
        indexer.build_index(image_folder, max_images=max_images, force_rebuild=force_rebuild)
        
        # Initialize retrieval
        global retrieval
        retrieval = ImageRetrieval(indexer.features, indexer.image_paths)
        
        return jsonify({
            'success': True,
            'image_count': indexer.get_image_count(),
            'message': f'Index built successfully with {indexer.get_image_count()} images'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/load_index', methods=['POST'])
def load_index():
    """Load existing index"""
    try:
        if indexer.load_index():
            global retrieval
            retrieval = ImageRetrieval(indexer.features, indexer.image_paths)
            
            return jsonify({
                'success': True,
                'image_count': indexer.get_image_count(),
                'message': f'Index loaded successfully with {indexer.get_image_count()} images'
            })
        else:
            return jsonify({'error': 'Index file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search', methods=['POST'])
def search():
    """Perform image search"""
    try:
        if retrieval is None:
            return jsonify({'error': 'Index not loaded. Please load or build index first.'}), 400
        
        data = request.json
        query_type = data.get('type', 'image')  # 'image' or 'file'
        
        if query_type == 'image':
            # Query from uploaded image
            image_data = data.get('image')
            if not image_data:
                return jsonify({'error': 'No image provided'}), 400
            
            # Decode base64 image
            image_data = image_data.split(',')[1] if ',' in image_data else image_data
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Save temporarily to extract features
            temp_path = 'temp_query.jpg'
            image.save(temp_path)
            
            try:
                query_features = extractor.extract_features(temp_path)
                retrieval.initial_query_from_features(query_features)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        elif query_type == 'file':
            # Query from file path in dataset
            query_path = data.get('query_path')
            if not query_path:
                return jsonify({'error': 'No query path provided'}), 400
            
            # Find image in index
            query_idx = None
            for i, path in enumerate(indexer.image_paths):
                if os.path.abspath(path) == os.path.abspath(query_path):
                    query_idx = i
                    break
            
            if query_idx is None:
                return jsonify({'error': 'Query image not found in index'}), 404
            
            retrieval.initial_query(query_idx)
        
        else:
            return jsonify({'error': 'Invalid query type'}), 400
        
        # Perform search
        top_k = data.get('top_k', 20)
        results = retrieval.search(top_k=top_k, exclude_feedback=False)
        
        # Prepare results
        search_results = []
        for img_idx, similarity in results:
            img_path = indexer.image_paths[img_idx]
            # Convert to relative path for frontend
            rel_path = os.path.relpath(img_path, IMAGES_FOLDER) if IMAGES_FOLDER in img_path else img_path
            
            search_results.append({
                'index': img_idx,
                'path': rel_path,
                'full_path': img_path,
                'similarity': float(similarity)
            })
        
        # Get feedback summary
        feedback_summary = retrieval.get_feedback_summary()
        
        return jsonify({
            'success': True,
            'results': search_results,
            'feedback': feedback_summary,
            'count': len(search_results)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/feedback', methods=['POST'])
def apply_feedback():
    """Apply relevance feedback"""
    try:
        if retrieval is None:
            return jsonify({'error': 'No active search. Please search first.'}), 400
        
        data = request.json
        feedback_list = data.get('feedback', [])
        
        # Clear previous feedback
        retrieval.clear_feedback()
        
        # Apply new feedback
        for item in feedback_list:
            img_idx = item.get('index')
            is_relevant = item.get('relevant', False)
            is_irrelevant = item.get('irrelevant', False)
            
            if img_idx is not None:
                if is_relevant:
                    retrieval.add_feedback(img_idx, is_relevant=True)
                elif is_irrelevant:
                    retrieval.add_feedback(img_idx, is_relevant=False)
        
        # Reformulate query
        retrieval.reformulate_query()
        
        # Perform new search
        top_k = data.get('top_k', 20)
        results = retrieval.search(top_k=top_k, exclude_feedback=False)
        
        # Prepare results
        search_results = []
        for img_idx, similarity in results:
            img_path = indexer.image_paths[img_idx]
            rel_path = os.path.relpath(img_path, IMAGES_FOLDER) if IMAGES_FOLDER in img_path else img_path
            
            search_results.append({
                'index': img_idx,
                'path': rel_path,
                'full_path': img_path,
                'similarity': float(similarity)
            })
        
        # Get feedback summary
        feedback_summary = retrieval.get_feedback_summary()
        
        return jsonify({
            'success': True,
            'results': search_results,
            'feedback': feedback_summary,
            'count': len(search_results),
            'message': 'Feedback applied successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reset', methods=['POST'])
def reset_feedback():
    """Reset all feedback"""
    try:
        if retrieval is None:
            return jsonify({'error': 'No active search'}), 400
        
        retrieval.clear_feedback()
        
        return jsonify({
            'success': True,
            'message': 'Feedback reset successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/images/<path:filename>')
def serve_image(filename):
    """Serve images from images folder"""
    try:
        # Decode URL encoding
        filename = filename.replace('%20', ' ')
        
        # Try to find image in various locations
        possible_paths = [
            os.path.join(IMAGES_FOLDER, filename),
            filename,
            os.path.join('.', filename)
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.path.isfile(path):
                directory = os.path.dirname(path) or '.'
                file_name = os.path.basename(path)
                return send_from_directory(directory, file_name)
        
        # If not found, try to find in indexer paths
        if indexer.image_paths:
            for img_path in indexer.image_paths:
                if filename in img_path or os.path.basename(img_path) == filename:
                    if os.path.exists(img_path):
                        directory = os.path.dirname(img_path) or '.'
                        file_name = os.path.basename(img_path)
                        return send_from_directory(directory, file_name)
        
        # Return 404 with error image
        return jsonify({'error': f'Image not found: {filename}'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/list_images', methods=['GET'])
def list_images():
    """List available images for query selection"""
    try:
        if not indexer.image_paths:
            return jsonify({'images': []})
        
        images = []
        for i, path in enumerate(indexer.image_paths[:100]):  # Limit to first 100 for performance
            rel_path = os.path.relpath(path, IMAGES_FOLDER) if IMAGES_FOLDER in path else path
            images.append({
                'index': i,
                'path': rel_path,
                'full_path': path,
                'filename': os.path.basename(path)
            })
        
        return jsonify({'images': images})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import sys
    import socket
    
    # Create static directory if it doesn't exist
    os.makedirs('static', exist_ok=True)
    
    # Get port from command line or use default
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}. Using default port 5000.")
    
    # Check if port is available, if not try to find available port
    def find_free_port(start_port):
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                continue
        return None
    
    # Try to use specified port, or find free port
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        test_socket.bind(('', port))
        test_socket.close()
        actual_port = port
    except OSError:
        print(f"Port {port} is in use. Finding available port...")
        actual_port = find_free_port(port)
        if actual_port is None:
            print("Error: Could not find available port. Please free up a port.")
            sys.exit(1)
        print(f"Using port {actual_port} instead.")
    
    print("Starting Image Retrieval Server...")
    print(f"Open your browser and go to: http://localhost:{actual_port}")
    app.run(debug=True, host='0.0.0.0', port=actual_port)

