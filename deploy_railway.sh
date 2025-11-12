#!/bin/bash
# Simple Railway deployment script

set -e

echo "🚂 Deploying to Railway..."

# Check for Railway token
if [ -z "$RAILWAY_TOKEN" ]; then
    echo "❌ Error: RAILWAY_TOKEN not set"
    exit 1
fi

# Install Railway CLI if needed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Login to Railway
echo "🔐 Logging in to Railway..."
railway login --browserless

# Deploy
echo "🚀 Deploying..."
railway up --detach

echo "✅ Deployment triggered!"
echo "Check your Railway dashboard: https://railway.app/"
