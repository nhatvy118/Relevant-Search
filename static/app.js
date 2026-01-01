// Image Retrieval Frontend JavaScript

const API_BASE = '/api';
let currentResults = [];
let queryImageFile = null;

// DOM Elements
const elements = {
    buildIndexBtn: document.getElementById('buildIndexBtn'),
    loadIndexBtn: document.getElementById('loadIndexBtn'),
    imageFolder: document.getElementById('imageFolder'),
    indexStatus: document.getElementById('indexStatus'),
    queryImage: document.getElementById('queryImage'),
    queryPreview: document.getElementById('queryPreview'),
    searchBtn: document.getElementById('searchBtn'),
    applyFeedbackBtn: document.getElementById('applyFeedbackBtn'),
    resetBtn: document.getElementById('resetBtn'),
    feedbackInfo: document.getElementById('feedbackInfo'),
    resultsContainer: document.getElementById('resultsContainer'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    loadingText: document.getElementById('loadingText')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkStatus();
});

function setupEventListeners() {
    // Index management
    elements.buildIndexBtn.addEventListener('click', buildIndex);
    elements.loadIndexBtn.addEventListener('click', loadIndex);
    
    // Query image
    elements.queryImage.addEventListener('change', handleQueryImageSelect);
    
    // Search
    elements.searchBtn.addEventListener('click', performSearch);
    
    // Feedback
    elements.applyFeedbackBtn.addEventListener('click', applyFeedback);
    elements.resetBtn.addEventListener('click', resetFeedback);
}

async function checkStatus() {
    try {
        const response = await fetch(`${API_BASE}/status`);
        const data = await response.json();
        
        if (data.has_index) {
            elements.indexStatus.textContent = `✓ Index loaded: ${data.image_count} images`;
            elements.indexStatus.style.background = '#d4edda';
            elements.indexStatus.style.color = '#155724';
            elements.indexStatus.style.borderColor = '#c3e6cb';
        } else {
            elements.indexStatus.textContent = 'No index found. Please build or load index.';
            elements.indexStatus.style.background = '#f8d7da';
            elements.indexStatus.style.color = '#721c24';
            elements.indexStatus.style.borderColor = '#f5c6cb';
        }
    } catch (error) {
        console.error('Error checking status:', error);
        elements.indexStatus.textContent = 'Error checking status';
        elements.indexStatus.style.background = '#f8d7da';
        elements.indexStatus.style.color = '#721c24';
    }
}

async function buildIndex() {
    const folder = elements.imageFolder.value.trim() || 'images/';
    
    // Show modal to get max images
    const maxImagesStr = await showModal(
        'Enter Maximum Images',
        'Enter maximum number of images to index (leave empty for all):',
        '5000'
    );
    
    if (maxImagesStr === null) {
        return; // User cancelled
    }
    
    const maxImages = maxImagesStr === '' ? null : parseInt(maxImagesStr);
    
    showLoading('Building index... This may take a while.');
    
    try {
        const response = await fetch(`${API_BASE}/build_index`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                folder: folder,
                max_images: maxImages,
                force_rebuild: true
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            elements.indexStatus.textContent = `✓ ${data.message}`;
            elements.indexStatus.style.background = '#d4edda';
            elements.indexStatus.style.color = '#155724';
            elements.indexStatus.style.borderColor = '#c3e6cb';
            await showModal('Success', `Index built successfully with ${data.image_count} images!`, '');
        } else {
            throw new Error(data.error || 'Failed to build index');
        }
    } catch (error) {
        console.error('Error building index:', error);
        await showModal('Error', `Error building index: ${error.message}`, '');
        elements.indexStatus.textContent = `Error: ${error.message}`;
        elements.indexStatus.style.background = '#f8d7da';
        elements.indexStatus.style.color = '#721c24';
    } finally {
        hideLoading();
    }
}

async function loadIndex() {
    showLoading('Loading index...');
    
    try {
        const response = await fetch(`${API_BASE}/load_index`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            elements.indexStatus.textContent = `✓ ${data.message}`;
            elements.indexStatus.style.background = '#d4edda';
            elements.indexStatus.style.color = '#155724';
            elements.indexStatus.style.borderColor = '#c3e6cb';
            await showModal('Success', `Index loaded successfully with ${data.image_count} images!`, '');
        } else {
            throw new Error(data.error || 'Failed to load index');
        }
    } catch (error) {
        console.error('Error loading index:', error);
        await showModal('Error', `Error loading index: ${error.message}`, '');
        elements.indexStatus.textContent = `Error: ${error.message}`;
        elements.indexStatus.style.background = '#f8d7da';
        elements.indexStatus.style.color = '#721c24';
    } finally {
        hideLoading();
    }
}

function handleQueryImageSelect(event) {
    const file = event.target.files[0];
    if (file) {
        queryImageFile = file;
        
        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            elements.queryPreview.innerHTML = `<img src="${e.target.result}" alt="Query Image">`;
            elements.searchBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }
}

async function performSearch() {
    if (!queryImageFile) {
        await showModal('Info', 'Please select a query image first', '');
        return;
    }
    
    showLoading('Searching...');
    
    try {
        // Convert image to base64
        const reader = new FileReader();
        reader.onload = async (e) => {
            try {
                const response = await fetch(`${API_BASE}/search`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        type: 'image',
                        image: e.target.result,
                        top_k: 20
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentResults = data.results;
                    displayResults(data.results);
                    updateFeedbackInfo(data.feedback);
                    elements.applyFeedbackBtn.disabled = false;
                    elements.resetBtn.disabled = false;
                } else {
                    throw new Error(data.error || 'Search failed');
                }
            } catch (error) {
                console.error('Error searching:', error);
                await showModal('Error', `Search error: ${error.message}`, '');
            } finally {
                hideLoading();
            }
        };
        reader.readAsDataURL(queryImageFile);
    } catch (error) {
        console.error('Error:', error);
        await showModal('Error', `Error: ${error.message}`, '');
        hideLoading();
    }
}

function displayResults(results) {
    if (results.length === 0) {
        elements.resultsContainer.innerHTML = `
            <div class="empty-state">
                <p>No results found</p>
            </div>
        `;
        return;
    }
    
    // Generate product name from filename
    function getProductName(path) {
        const filename = path.split('/').pop().replace(/\.[^/.]+$/, '');
        return filename.replace(/[-_]/g, ' ').toUpperCase();
    }
    
    elements.resultsContainer.innerHTML = results.map((result, idx) => {
        const productName = getProductName(result.path);
        const price = (result.similarity * 2999).toFixed(2);
        
        return `
        <div class="product-card" data-index="${result.index}">
            <div class="product-image-container">
                <img src="${API_BASE}/images/${encodeURIComponent(result.path)}" 
                     alt="${productName}" 
                     class="product-image"
                     onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'250\\' height=\\'250\\'%3E%3Crect fill=\\'%23fafafa\\' width=\\'250\\' height=\\'250\\'/%3E%3Ctext x=\\'50%25\\' y=\\'50%25\\' text-anchor=\\'middle\\' dy=\\'.3em\\' fill=\\'%23999\\' font-size=\\'14\\'%3EImage not found%3C/text%3E%3C/svg%3E'">
            </div>
            <div class="product-info">
                <div class="product-name">${productName}</div>
                <div class="product-price">RS. ${price}</div>
                <div class="product-score">Similarity: ${result.similarity.toFixed(3)}</div>
            </div>
            <div class="product-feedback">
                <label class="feedback-checkbox-label">
                    <input type="checkbox" class="relevant-checkbox" data-index="${result.index}">
                    <span>✓ Relevant</span>
                </label>
                <label class="feedback-checkbox-label">
                    <input type="checkbox" class="irrelevant-checkbox" data-index="${result.index}">
                    <span>✗ Irrelevant</span>
                </label>
            </div>
        </div>
        `;
    }).join('');
}

async function applyFeedback() {
    const feedback = [];
    
    // Collect feedback from checkboxes
    document.querySelectorAll('.product-card').forEach(item => {
        const index = parseInt(item.dataset.index);
        const relevantCheckbox = item.querySelector('.relevant-checkbox');
        const irrelevantCheckbox = item.querySelector('.irrelevant-checkbox');
        
        if (relevantCheckbox.checked || irrelevantCheckbox.checked) {
            feedback.push({
                index: index,
                relevant: relevantCheckbox.checked,
                irrelevant: irrelevantCheckbox.checked
            });
        }
    });
    
    if (feedback.length === 0) {
        await showModal('Info', 'Please mark at least one image as relevant or irrelevant', '');
        return;
    }
    
    showLoading('Applying feedback and reformulating query...');
    
    try {
        const response = await fetch(`${API_BASE}/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                feedback: feedback,
                top_k: 20
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentResults = data.results;
            displayResults(data.results);
            updateFeedbackInfo(data.feedback);
            await showModal('Success', 'Feedback applied! Query has been reformulated.', '');
        } else {
            throw new Error(data.error || 'Failed to apply feedback');
        }
    } catch (error) {
        console.error('Error applying feedback:', error);
        await showModal('Error', `Error: ${error.message}`, '');
    } finally {
        hideLoading();
    }
}

async function resetFeedback() {
    if (!confirm('Reset all feedback? This will clear all relevance marks.')) {
        return;
    }
    
    showLoading('Resetting feedback...');
    
    try {
        const response = await fetch(`${API_BASE}/reset`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Clear all checkboxes
            document.querySelectorAll('.relevant-checkbox, .irrelevant-checkbox').forEach(cb => {
                cb.checked = false;
            });
            
            // Refresh display if there are results
            if (currentResults.length > 0) {
                displayResults(currentResults);
            }
            
            updateFeedbackInfo({ relevant_count: 0, irrelevant_count: 0 });
            await showModal('Success', 'Feedback reset successfully', '');
        } else {
            throw new Error(data.error || 'Failed to reset feedback');
        }
    } catch (error) {
        console.error('Error resetting feedback:', error);
        await showModal('Error', `Error: ${error.message}`, '');
    } finally {
        hideLoading();
    }
}

function updateFeedbackInfo(feedback) {
    const relevant = feedback.relevant_count || 0;
    const irrelevant = feedback.irrelevant_count || 0;
    elements.feedbackInfo.textContent = `Relevant: ${relevant} | Irrelevant: ${irrelevant}`;
}

function showLoading(text = 'Loading...') {
    elements.loadingText.textContent = text;
    elements.loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    elements.loadingOverlay.style.display = 'none';
}

// Modal functions
function showModal(title, message, defaultValue = '') {
    return new Promise((resolve) => {
        const modalOverlay = document.getElementById('modalOverlay');
        const modalTitle = document.getElementById('modalTitle');
        const modalMessage = document.getElementById('modalMessage');
        const modalInput = document.getElementById('modalInput');
        const modalOk = document.getElementById('modalOk');
        const modalCancel = document.getElementById('modalCancel');
        const modalClose = document.getElementById('modalClose');
        
        // Set content
        modalTitle.textContent = title;
        modalMessage.textContent = message;
        
        // Check if this is input mode or message-only mode
        const isInputMode = defaultValue !== '' || message.includes('Enter');
        
        if (isInputMode) {
            modalInput.style.display = 'block';
            modalInput.value = defaultValue;
            modalCancel.style.display = 'block';
            setTimeout(() => modalInput.focus(), 100);
            modalInput.select();
        } else {
            modalInput.style.display = 'none';
            modalCancel.style.display = 'none';
        }
        
        // Show modal
        modalOverlay.style.display = 'flex';
        
        // Handle OK
        const handleOk = () => {
            if (isInputMode) {
                const value = modalInput.value.trim();
                modalOverlay.style.display = 'none';
                resolve(value === '' ? null : value);
            } else {
                modalOverlay.style.display = 'none';
                resolve('');
            }
            cleanup();
        };
        
        // Handle Cancel
        const handleCancel = () => {
            if (isInputMode) {
                modalOverlay.style.display = 'none';
                resolve(null);
                cleanup();
            }
        };
        
        // Cleanup event listeners
        function cleanup() {
            modalOk.removeEventListener('click', handleOk);
            modalCancel.removeEventListener('click', handleCancel);
            modalClose.removeEventListener('click', handleCancel);
            modalOverlay.removeEventListener('click', handleOverlayClick);
            document.removeEventListener('keydown', handleKeyDown);
        }
        
        // Handle overlay click (close if clicking outside)
        const handleOverlayClick = (e) => {
            if (e.target === modalOverlay) {
                handleCancel();
            }
        };
        
        // Handle Enter key
        const handleKeyDown = (e) => {
            if (e.key === 'Enter') {
                handleOk();
            } else if (e.key === 'Escape') {
                handleCancel();
            }
        };
        
        // Add event listeners
        modalOk.addEventListener('click', handleOk);
        if (isInputMode) {
            modalCancel.addEventListener('click', handleCancel);
            modalClose.addEventListener('click', handleCancel);
            modalOverlay.addEventListener('click', handleOverlayClick);
        } else {
            modalClose.addEventListener('click', handleOk);
            modalOverlay.addEventListener('click', (e) => {
                if (e.target === modalOverlay) {
                    handleOk();
                }
            });
        }
        document.addEventListener('keydown', handleKeyDown);
    });
}

