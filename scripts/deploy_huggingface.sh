#!/bin/bash
# Deployment script for Hugging Face Spaces

set -e

echo "🚀 Deploying AI Architectural Search to Hugging Face Spaces"

# Configuration
SPACE_NAME="ai-architectural-search"
HF_USERNAME="${HF_USERNAME:-your-username}"
SPACE_URL="https://huggingface.co/spaces/${HF_USERNAME}/${SPACE_NAME}"

# Check prerequisites
if [ -z "$HF_TOKEN" ]; then
    echo "❌ Error: HF_TOKEN environment variable not set"
    echo "Please set your Hugging Face token: export HF_TOKEN=your_token"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "❌ Error: git is required but not installed"
    exit 1
fi

# Install Hugging Face CLI if not present
if ! command -v huggingface-cli &> /dev/null; then
    echo "📦 Installing Hugging Face CLI..."
    pip install huggingface_hub[cli]
fi

# Login to Hugging Face
echo "🔐 Logging in to Hugging Face..."
huggingface-cli login --token "$HF_TOKEN"

# Create or clone the space repository
if [ ! -d "hf_space" ]; then
    echo "📁 Creating Hugging Face Space repository..."
    
    # Create the space if it doesn't exist
    huggingface-cli repo create --type space --space_sdk streamlit "$SPACE_NAME" || true
    
    # Clone the space repository
    git clone "https://huggingface.co/spaces/${HF_USERNAME}/${SPACE_NAME}" hf_space
else
    echo "📁 Using existing space repository..."
    cd hf_space
    git pull origin main
    cd ..
fi

# Prepare files for deployment
echo "📋 Preparing files for deployment..."

# Copy application files
cp app.py hf_space/
cp requirements.txt hf_space/
cp -r src/ hf_space/
cp -r images/ hf_space/
cp image_metadata.json hf_space/
cp config.py hf_space/
cp .env.production hf_space/.env

# Create README for Hugging Face Spaces
cat > hf_space/README.md << 'EOF'
---
title: AI Architectural Search
emoji: 🏗️
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: 1.28.1
app_file: app.py
pinned: false
license: mit
---

# AI Architectural Search

An AI-powered search system that enables users to find architectural building photographs using natural language queries about visual features.

## Features

- 🔍 Natural language search for architectural images
- 🏗️ Support for queries about materials (brick, glass, steel, stone)
- 🏛️ Recognition of architectural features (roofs, windows, columns)
- 📊 Confidence scores for search results
- 🎯 CLIP-based semantic matching

## Usage

1. Enter a natural language description of architectural features
2. Click search to find matching images
3. Browse results with confidence scores and descriptions

## Example Queries

- "red brick buildings"
- "glass and steel facades"
- "stone columns"
- "flat roof structures"
- "modern office buildings"

## Technology

Built with Streamlit, PyTorch, and OpenAI's CLIP model for state-of-the-art image-text matching.
EOF

# Create Hugging Face Spaces configuration
cat > hf_space/.streamlit/config.toml << 'EOF'
[server]
headless = true
port = 7860

[browser]
gatherUsageStats = false
EOF

mkdir -p hf_space/.streamlit

# Deploy to Hugging Face Spaces
echo "🚀 Deploying to Hugging Face Spaces..."
cd hf_space

git add .
git commit -m "Deploy AI Architectural Search System" || echo "No changes to commit"
git push origin main

echo "✅ Deployment completed!"
echo "🌐 Your app will be available at: $SPACE_URL"
echo "⏳ Note: It may take a few minutes for the space to build and become available"

# Cleanup
cd ..
echo "🧹 Cleaning up temporary files..."