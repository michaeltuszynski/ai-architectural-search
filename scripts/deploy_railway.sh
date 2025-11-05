#!/bin/bash
# Deployment script for Railway

set -e

echo "🚂 Deploying AI Architectural Search to Railway"

# Check prerequisites
if [ -z "$RAILWAY_TOKEN" ]; then
    echo "❌ Error: RAILWAY_TOKEN environment variable not set"
    echo "Please set your Railway token: export RAILWAY_TOKEN=your_token"
    exit 1
fi

# Install Railway CLI if not present
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    
    # Install Railway CLI
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install railway
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -fsSL https://railway.app/install.sh | sh
    else
        echo "❌ Unsupported OS. Please install Railway CLI manually: https://docs.railway.app/develop/cli"
        exit 1
    fi
fi

# Login to Railway
echo "🔐 Logging in to Railway..."
railway login --token "$RAILWAY_TOKEN"

# Create or connect to Railway project
PROJECT_NAME="ai-architectural-search"

if railway status &> /dev/null; then
    echo "📁 Using existing Railway project..."
else
    echo "📁 Creating new Railway project..."
    railway init "$PROJECT_NAME"
fi

# Set environment variables for production
echo "⚙️ Setting environment variables..."
railway variables set ENVIRONMENT=production
railway variables set MEMORY_OPTIMIZATION=true
railway variables set CPU_ONLY_MODE=true
railway variables set LOG_LEVEL=INFO
railway variables set MAX_RESULTS=5
railway variables set BATCH_SIZE=16
railway variables set MAX_IMAGE_SIZE=256,256

# Deploy the application
echo "🚀 Deploying to Railway..."
railway up --detach

# Get deployment URL
echo "🌐 Getting deployment URL..."
DEPLOYMENT_URL=$(railway domain)

if [ -n "$DEPLOYMENT_URL" ]; then
    echo "✅ Deployment completed!"
    echo "🌐 Your app is available at: https://$DEPLOYMENT_URL"
else
    echo "✅ Deployment completed!"
    echo "🌐 Check your Railway dashboard for the deployment URL"
fi

echo "📊 You can monitor your deployment with: railway logs"