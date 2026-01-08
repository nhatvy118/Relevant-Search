"""
Flask Backend API for Image Retrieval with Relevance Feedback
Supports both Traditional and Text-based (CLIP) methods
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from pathlib import Path
import base64
from PIL import Image
import io

# Traditional method imports
from traditional import ImageIndexer, TraditionalImageRetrieval, FeatureExtractor

# Text-based (CLIP) method imports
from clip import TextIndexer, TextRetrieval

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)  # Enable CORS for all routes

# Global variables - Traditional method
traditional_indexer = ImageIndexer()
traditional_retrieval = None
traditional_extractor = FeatureExtractor()

# Global variables - Text-based (CLIP) method
text_indexer = TextIndexer()
text_retrieval = None

# Configuration
IMAGES_FOLDER = 'images'
TRADITIONAL_INDEX_FILE = 'image_index.pkl'
TEXT_INDEX_FILE = 'text_index.pkl'


@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('static', 'index.html')


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status for both methods"""
    has_traditional_index = os.path.exists(TRADITIONAL_INDEX_FILE)
    has_text_index = os.path.exists(TEXT_INDEX_FILE)
    traditional_count = traditional_indexer.get_image_count() if has_traditional_index else 0
    text_count = text_indexer.get_image_count() if has_text_index else 0
    
    return jsonify({
        'traditional': {
            'has_index': has_traditional_index,
            'image_count': traditional_count,
            'index_file': TRADITIONAL_INDEX_FILE
        },
        'text': {
            'has_index': has_text_index,
            'image_count': text_count,
            'index_file': TEXT_INDEX_FILE
        }
    })


@app.route('/api/build_index', methods=['POST'])
def build_index():
    """Build index from image folder - supports both methods"""
    try:
        data = request.json
        method = data.get('method', 'traditional')  # 'traditional' or 'text'
        image_folder = data.get('folder', IMAGES_FOLDER)
        max_images = data.get('max_images', None)
        force_rebuild = data.get('force_rebuild', False)
        
        if not os.path.exists(image_folder):
            return jsonify({'error': f'Folder not found: {image_folder}'}), 400
        
        if method == 'traditional':
            traditional_indexer.build_index(image_folder, max_images=max_images, force_rebuild=force_rebuild)
            global traditional_retrieval
            traditional_retrieval = TraditionalImageRetrieval(traditional_indexer.features, traditional_indexer.image_paths)
            
            return jsonify({
                'success': True,
                'method': 'traditional',
                'image_count': traditional_indexer.get_image_count(),
                'message': f'Traditional index built successfully with {traditional_indexer.get_image_count()} images'
            })
        elif method == 'text':
            text_indexer.build_index(image_folder, max_images=max_images, force_rebuild=force_rebuild)
            global text_retrieval
            text_retrieval = TextRetrieval(text_indexer.features, text_indexer.image_paths)
            
            return jsonify({
                'success': True,
                'method': 'text',
                'image_count': text_indexer.get_image_count(),
                'message': f'Text (CLIP) index built successfully with {text_indexer.get_image_count()} images'
            })
        else:
            return jsonify({'error': f'Invalid method: {method}. Use "traditional" or "text"'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/load_index', methods=['POST'])
def load_index():
    """Load existing index - supports both methods"""
    try:
        data = request.json
        method = data.get('method', 'traditional')  # 'traditional' or 'text'
        
        if method == 'traditional':
            if traditional_indexer.load_index():
                global traditional_retrieval
                traditional_retrieval = TraditionalImageRetrieval(traditional_indexer.features, traditional_indexer.image_paths)
                
                return jsonify({
                    'success': True,
                    'method': 'traditional',
                    'image_count': traditional_indexer.get_image_count(),
                    'message': f'Traditional index loaded successfully with {traditional_indexer.get_image_count()} images'
                })
            else:
                return jsonify({'error': 'Traditional index file not found'}), 404
        elif method == 'text':
            if text_indexer.load_index():
                global text_retrieval
                text_retrieval = TextRetrieval(text_indexer.features, text_indexer.image_paths)
                
                return jsonify({
                    'success': True,
                    'method': 'text',
                    'image_count': text_indexer.get_image_count(),
                    'message': f'Text (CLIP) index loaded successfully with {text_indexer.get_image_count()} images'
                })
            else:
                return jsonify({'error': 'Text index file not found'}), 404
        else:
            return jsonify({'error': f'Invalid method: {method}. Use "traditional" or "text"'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search', methods=['POST'])
def search():
    """Perform image search - supports both traditional and text methods"""
    try:
        data = request.json
        method = data.get('method', 'traditional')  # 'traditional' or 'text'
        query_type = data.get('type', 'image')  # 'image', 'file', or 'text'
        
        if method == 'traditional':
            if traditional_retrieval is None:
                return jsonify({'error': 'Traditional index not loaded. Please load or build index first.'}), 400
            
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
                    query_features = traditional_extractor.extract_features(temp_path)
                    traditional_retrieval.initial_query_from_features(query_features)
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
                for i, path in enumerate(traditional_indexer.image_paths):
                    if os.path.abspath(path) == os.path.abspath(query_path):
                        query_idx = i
                        break
                
                if query_idx is None:
                    return jsonify({'error': 'Query image not found in index'}), 404
                
                traditional_retrieval.initial_query(query_idx)
            else:
                return jsonify({'error': 'Invalid query type for traditional method. Use "image" or "file"'}), 400
            
            # Perform search
            top_k = data.get('top_k', 20)
            results = traditional_retrieval.search(top_k=top_k, exclude_feedback=False)
            
            # Prepare results
            search_results = []
            for img_idx, similarity in results:
                img_path = traditional_indexer.image_paths[img_idx]
                rel_path = os.path.relpath(img_path, IMAGES_FOLDER) if IMAGES_FOLDER in img_path else img_path
                
                search_results.append({
                    'index': img_idx,
                    'path': rel_path,
                    'full_path': img_path,
                    'similarity': float(similarity)
                })
            
            indexer = traditional_indexer
            
        elif method == 'text':
            if text_retrieval is None:
                return jsonify({'error': 'Text (CLIP) index not loaded. Please load or build index first.'}), 400
            
            if query_type == 'text':
                # Query from text
                text_query = data.get('text_query')
                if not text_query:
                    return jsonify({'error': 'No text query provided'}), 400
                
                text_retrieval.initial_query_from_text(text_query)
            
            elif query_type == 'image':
                # Query from uploaded image using CLIP
                image_data = data.get('image')
                if not image_data:
                    return jsonify({'error': 'No image provided'}), 400
                
                # Decode base64 image
                image_data = image_data.split(',')[1] if ',' in image_data else image_data
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
                
                text_retrieval.initial_query_from_image_pil(image)
            
            elif query_type == 'file':
                # Query from file path in dataset
                query_path = data.get('query_path')
                if not query_path:
                    return jsonify({'error': 'No query path provided'}), 400
                
                text_retrieval.initial_query_from_image(query_path)
            else:
                return jsonify({'error': 'Invalid query type for text method. Use "text", "image", or "file"'}), 400
            
            # Perform search
            top_k = data.get('top_k', 20)
            results = text_retrieval.search(top_k=top_k, exclude_feedback=False)
            
            # Prepare results
            search_results = []
            for img_idx, similarity in results:
                img_path = text_indexer.image_paths[img_idx]
                rel_path = os.path.relpath(img_path, IMAGES_FOLDER) if IMAGES_FOLDER in img_path else img_path
                
                search_results.append({
                    'index': img_idx,
                    'path': rel_path,
                    'full_path': img_path,
                    'similarity': float(similarity)
                })
            
            indexer = text_indexer
        else:
            return jsonify({'error': f'Invalid method: {method}. Use "traditional" or "text"'}), 400
        
        return jsonify({
            'success': True,
            'method': method,
            'results': search_results,
            'count': len(search_results)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/feedback', methods=['POST'])
def apply_feedback():
    """Apply relevance feedback - supports both methods"""
    try:
        data = request.json
        method = data.get('method', 'traditional')  # 'traditional' or 'text'
        feedback_list = data.get('feedback', [])
        
        if method == 'traditional':
            if traditional_retrieval is None:
                return jsonify({'error': 'No active search. Please search first.'}), 400
            
            # Clear previous feedback
            traditional_retrieval.clear_feedback()
            
            # Apply new feedback
            for item in feedback_list:
                img_idx = item.get('index')
                is_relevant = item.get('relevant', False)
                is_irrelevant = item.get('irrelevant', False)
                
                if img_idx is not None:
                    if is_relevant:
                        traditional_retrieval.add_feedback(img_idx, is_relevant=True)
                    elif is_irrelevant:
                        traditional_retrieval.add_feedback(img_idx, is_relevant=False)
            
            # Reformulate query
            traditional_retrieval.reformulate_query()
            
            # Perform new search
            top_k = data.get('top_k', 20)
            results = traditional_retrieval.search(top_k=top_k, exclude_feedback=False)
            
            # Prepare results
            search_results = []
            for img_idx, similarity in results:
                img_path = traditional_indexer.image_paths[img_idx]
                rel_path = os.path.relpath(img_path, IMAGES_FOLDER) if IMAGES_FOLDER in img_path else img_path
                
                search_results.append({
                    'index': img_idx,
                    'path': rel_path,
                    'full_path': img_path,
                    'similarity': float(similarity)
                })
            
        elif method == 'text':
            if text_retrieval is None:
                return jsonify({'error': 'No active search. Please search first.'}), 400
            
            # Clear previous feedback
            text_retrieval.clear_feedback()
            
            # Apply image feedback
            for item in feedback_list:
                img_idx = item.get('index')
                is_relevant = item.get('relevant', False)
                is_irrelevant = item.get('irrelevant', False)
                
                if img_idx is not None:
                    if is_relevant:
                        text_retrieval.add_feedback(img_idx, is_relevant=True)
                    elif is_irrelevant:
                        text_retrieval.add_feedback(img_idx, is_relevant=False)
            
            # Reformulate query
            text_retrieval.reformulate_query()
            
            # Perform new search
            top_k = data.get('top_k', 20)
            results = text_retrieval.search(top_k=top_k, exclude_feedback=False)
            
            # Prepare results
            search_results = []
            for img_idx, similarity in results:
                img_path = text_indexer.image_paths[img_idx]
                rel_path = os.path.relpath(img_path, IMAGES_FOLDER) if IMAGES_FOLDER in img_path else img_path
                
                search_results.append({
                    'index': img_idx,
                    'path': rel_path,
                    'full_path': img_path,
                    'similarity': float(similarity)
                })
        else:
            return jsonify({'error': f'Invalid method: {method}. Use "traditional" or "text"'}), 400
        
        return jsonify({
            'success': True,
            'method': method,
            'results': search_results,
            'count': len(search_results),
            'message': 'Feedback applied successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reset', methods=['POST'])
def reset_feedback():
    """Reset all feedback - supports both methods"""
    try:
        data = request.json
        method = data.get('method', 'traditional')  # 'traditional' or 'text'
        
        if method == 'traditional':
            if traditional_retrieval is None:
                return jsonify({'error': 'No active search'}), 400
            traditional_retrieval.clear_feedback()
        elif method == 'text':
            if text_retrieval is None:
                return jsonify({'error': 'No active search'}), 400
            text_retrieval.clear_feedback()
            text_retrieval.clear_text_feedback()
        else:
            return jsonify({'error': f'Invalid method: {method}. Use "traditional" or "text"'}), 400
        
        return jsonify({
            'success': True,
            'method': method,
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
        
        # If not found, try to find in indexer paths (both methods)
        for indexer in [traditional_indexer, text_indexer]:
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
    """List available images for query selection - supports both methods"""
    try:
        data = request.args
        method = data.get('method', 'traditional')  # 'traditional' or 'text'
        
        if method == 'traditional':
            indexer = traditional_indexer
        elif method == 'text':
            indexer = text_indexer
        else:
            return jsonify({'error': f'Invalid method: {method}. Use "traditional" or "text"'}), 400
        
        if not indexer.image_paths:
            return jsonify({'images': [], 'method': method})
        
        images = []
        for i, path in enumerate(indexer.image_paths[:100]):  # Limit to first 100 for performance
            rel_path = os.path.relpath(path, IMAGES_FOLDER) if IMAGES_FOLDER in path else path
            images.append({
                'index': i,
                'path': rel_path,
                'full_path': path,
                'filename': os.path.basename(path)
            })
        
        return jsonify({'images': images, 'method': method})
    
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

