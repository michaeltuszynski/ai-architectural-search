#!/bin/bash
# Deployment script for Render

set -e

echo "🎨 Deploying AI Architectural Search to Render"

# Check prerequisites
if [ -z "$RENDER_API_KEY" ]; then
    echo "❌ Error: RENDER_API_KEY environment variable not set"
    echo "Please set your Render API key: export RENDER_API_KEY=your_key"
    exit 1
fi

if [ -z "$GITHUB_REPO" ]; then
    echo "❌ Error: GITHUB_REPO environment variable not set"
    echo "Please set your GitHub repository: export GITHUB_REPO=username/repo-name"
    exit 1
fi

# Install Render CLI if not present (using curl for API calls)
echo "🔧 Preparing Render deployment..."

# Create service configuration
SERVICE_NAME="ai-architectural-search"
REPO_URL="https://github.com/${GITHUB_REPO}"

# Create deployment payload
cat > render_deploy.json << EOF
{
  "type": "web_service",
  "name": "$SERVICE_NAME",
  "repo": "$REPO_URL",
  "branch": "main",
  "buildCommand": "docker build -t ai-search .",
  "startCommand": "streamlit run src/web/app.py --server.port=\$PORT --server.address=0.0.0.0",
  "plan": "starter",
  "region": "oregon",
  "env": "docker",
  "dockerfilePath": "./Dockerfile",
  "healthCheckPath": "/_stcore/health",
  "envVars": [
    {
      "key": "ENVIRONMENT",
      "value": "production"
    },
    {
      "key": "MEMORY_OPTIMIZATION",
      "value": "true"
    },
    {
      "key": "CPU_ONLY_MODE",
      "value": "true"
    },
    {
      "key": "LOG_LEVEL",
      "value": "INFO"
    },
    {
      "key": "MAX_RESULTS",
      "value": "5"
    },
    {
      "key": "BATCH_SIZE",
      "value": "16"
    }
  ]
}
EOF

# Deploy using Render API
echo "🚀 Creating Render service..."
RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d @render_deploy.json \
  https://api.render.com/v1/services)

# Extract service ID and URL from response
SERVICE_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
SERVICE_URL=$(echo "$RESPONSE" | grep -o '"url":"[^"]*"' | cut -d'"' -f4)

if [ -n "$SERVICE_ID" ]; then
    echo "✅ Deployment initiated!"
    echo "🆔 Service ID: $SERVICE_ID"
    
    if [ -n "$SERVICE_URL" ]; then
        echo "🌐 Your app will be available at: $SERVICE_URL"
    fi
    
    echo "📊 Monitor deployment at: https://dashboard.render.com/web/$SERVICE_ID"
    echo "⏳ Note: Initial deployment may take 10-15 minutes"
else
    echo "❌ Deployment failed. Response:"
    echo "$RESPONSE"
    exit 1
fi

# Cleanup
rm render_deploy.json

echo "🎉 Render deployment script completed!"