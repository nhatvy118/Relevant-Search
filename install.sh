#!/bin/bash
# Script to install dependencies with correct order to avoid conflicts

echo "Installing dependencies..."

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated"
fi

# Install basic requirements (excluding torch/torchvision/clip)
echo "Installing basic packages..."
pip install numpy>=1.24.0 opencv-python>=4.8.0 Pillow>=10.0.0 scipy>=1.13.0 scikit-learn>=1.3.0 Flask>=2.3.0 flask-cors>=4.0.0

# Install torch and torchvision with compatible versions
echo "Installing torch and torchvision..."
pip install torch==2.8.0 torchvision==0.23.0

# Install clip-by-openai without dependencies (it requires old torch version but works with new one)
echo "Installing clip-by-openai..."
pip install clip-by-openai --no-deps

echo "Installation complete!"
echo "To verify, run: pip list | grep -E 'torch|clip'"

