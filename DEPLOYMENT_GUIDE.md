# AI Architectural Search - Deployment Guide

This guide provides step-by-step instructions for deploying the AI Architectural Search system to various cloud platforms.

## 🚀 Quick Start

The fastest way to deploy is using our automated deployment script:

```bash
# Deploy to Hugging Face Spaces (free)
./scripts/deploy.sh huggingface --backup --monitor

# Deploy to Railway (paid)
./scripts/deploy.sh railway --backup --monitor

# Deploy to all platforms
./scripts/deploy.sh all --backup --monitor
```

## 📋 Prerequisites

### System Requirements
- **Python 3.9+**
- **Docker** (for containerized deployment)
- **Git** (for version control)
- **2GB+ RAM** (for CLIP model)
- **1GB+ disk space**

### Required Files
Ensure these files exist in your project:
- ✅ `src/` directory with application code
- ✅ `images/` directory with architectural photos
- ✅ `image_metadata.json` with processed embeddings
- ✅ `requirements.txt` with dependencies
- ✅ `Dockerfile` for containerization
- ✅ `config.py` with configuration settings

### Environment Variables
Set up the following environment variables based on your chosen platform:

```bash
# For Hugging Face Spaces
export HF_TOKEN="your_huggingface_token"
export HF_USERNAME="your_username"

# For Railway
export RAILWAY_TOKEN="your_railway_token"

# For Render
export RENDER_API_KEY="your_render_api_key"
export GITHUB_REPO="username/repository-name"
```

## 🤗 Hugging Face Spaces (Recommended - Free)

### Why Choose Hugging Face Spaces?
- ✅ **Free hosting** for public repositories
- ✅ **2GB RAM** - sufficient for CLIP model
- ✅ **ML-optimized** infrastructure
- ✅ **Easy sharing** and community visibility
- ✅ **Zero configuration** deployment

### Step-by-Step Deployment

1. **Create Hugging Face Account**
   - Visit [huggingface.co](https://huggingface.co)
   - Sign up for a free account
   - Generate an access token at [Settings > Access Tokens](https://huggingface.co/settings/tokens)

2. **Set Environment Variables**
   ```bash
   export HF_TOKEN="hf_your_token_here"
   export HF_USERNAME="your_username"
   ```

3. **Deploy Using Script**
   ```bash
   ./scripts/deploy_huggingface.sh
   ```

4. **Manual Deployment (Alternative)**
   ```bash
   # Install Hugging Face CLI
   pip install huggingface_hub[cli]
   
   # Login
   huggingface-cli login --token $HF_TOKEN
   
   # Create Space
   huggingface-cli repo create --type space --space_sdk streamlit ai-architectural-search
   
   # Clone and deploy
   git clone https://huggingface.co/spaces/$HF_USERNAME/ai-architectural-search
   cd ai-architectural-search
   
   # Copy files
   cp ../app.py .
   cp ../requirements.txt .
   cp -r ../src/ .
   cp -r ../images/ .
   cp ../image_metadata.json .
   cp ../config.py .
   
   # Commit and push
   git add .
   git commit -m "Deploy AI Architectural Search"
   git push origin main
   ```

5. **Access Your Deployment**
   - URL: `https://huggingface.co/spaces/YOUR_USERNAME/ai-architectural-search`
   - Build time: 5-10 minutes
   - Cold start: 30-60 seconds

### Hugging Face Configuration

Create `.streamlit/config.toml` in your Space:
```toml
[server]
headless = true
port = 7860

[browser]
gatherUsageStats = false
```

## 🚂 Railway (Paid - Professional)

### Why Choose Railway?
- ✅ **No cold starts** - always available
- ✅ **Custom domains** available
- ✅ **Automatic scaling**
- ✅ **Professional reliability**
- ✅ **Simple deployment** from GitHub

### Pricing
- **Starter Plan**: $5/month + usage
- **Estimated Cost**: $20-30/month for 2GB RAM

### Step-by-Step Deployment

1. **Create Railway Account**
   - Visit [railway.app](https://railway.app)
   - Sign up and connect your GitHub account
   - Generate an API token in Settings

2. **Set Environment Variables**
   ```bash
   export RAILWAY_TOKEN="your_railway_token"
   ```

3. **Deploy Using Script**
   ```bash
   ./scripts/deploy_railway.sh
   ```

4. **Manual Deployment (Alternative)**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   # or on macOS: brew install railway
   
   # Login
   railway login --token $RAILWAY_TOKEN
   
   # Initialize project
   railway init ai-architectural-search
   
   # Set environment variables
   railway variables set ENVIRONMENT=production
   railway variables set MEMORY_OPTIMIZATION=true
   railway variables set CPU_ONLY_MODE=true
   
   # Deploy
   railway up
   ```

5. **Configure Custom Domain (Optional)**
   ```bash
   railway domain add your-domain.com
   ```

## 🎨 Render (Paid - Alternative)

### Why Choose Render?
- ✅ **Docker support**
- ✅ **Auto-deploy** from Git
- ✅ **Custom domains**
- ✅ **Environment variables**

### Pricing
- **Starter Plan**: $7/month
- **Standard Plan**: $25/month (recommended for 2GB RAM)

### Step-by-Step Deployment

1. **Create Render Account**
   - Visit [render.com](https://render.com)
   - Sign up and connect your GitHub account
   - Generate an API key in Account Settings

2. **Set Environment Variables**
   ```bash
   export RENDER_API_KEY="your_render_api_key"
   export GITHUB_REPO="username/repository-name"
   ```

3. **Deploy Using Script**
   ```bash
   ./scripts/deploy_render.sh
   ```

4. **Manual Deployment (Alternative)**
   - Connect your GitHub repository in Render dashboard
   - Choose "Web Service" type
   - Set build command: `docker build -t ai-search .`
   - Set start command: `streamlit run src/web/app.py --server.port=$PORT`
   - Configure environment variables in dashboard

## 🐳 Docker Deployment (Self-Hosted)

### Local Testing
```bash
# Build image
docker build -t ai-architectural-search .

# Run locally
docker run -p 8501:8501 ai-architectural-search

# Access at http://localhost:8501
```

### Production Docker Deployment
```bash
# Build for production
docker build -t ai-architectural-search:production .

# Run with production settings
docker run -d \
  --name ai-search \
  -p 80:8501 \
  -e ENVIRONMENT=production \
  -e MEMORY_OPTIMIZATION=true \
  -e CPU_ONLY_MODE=true \
  --restart unless-stopped \
  ai-architectural-search:production
```

### Docker Compose
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📊 Monitoring and Health Checks

### Automated Monitoring
```bash
# Monitor all deployments
./scripts/monitor_deployment.sh

# Check specific URL
./scripts/monitor_deployment.sh check https://your-app-url.com

# Performance test
./scripts/monitor_deployment.sh performance https://your-app-url.com
```

### Health Check Endpoints
- **Application Health**: `https://your-app.com/_stcore/health`
- **Custom Health Check**: `python health_check.py`

### Key Metrics to Monitor
- **Response Time**: < 5 seconds for queries
- **Memory Usage**: < 2GB during operation
- **Uptime**: > 95% availability
- **Error Rate**: < 1% of requests

## 🔧 Troubleshooting

### Common Issues

#### 1. Memory Errors
**Symptoms**: App crashes, out of memory errors
**Solutions**:
```bash
# Enable memory optimization
export MEMORY_OPTIMIZATION=true
export CPU_ONLY_MODE=true
export BATCH_SIZE=16
export MAX_IMAGE_SIZE=256,256
```

#### 2. Slow Cold Starts
**Symptoms**: Long loading times on first access
**Solutions**:
- Use paid platforms (Railway, Render) for no cold starts
- Enable model caching: `ENABLE_MODEL_CACHING=true`
- Pre-warm with health checks

#### 3. Build Failures
**Symptoms**: Docker build fails, dependency errors
**Solutions**:
```bash
# Test build locally
docker build -t test-build .

# Check dependencies
pip install -r requirements.txt

# Validate files
python health_check.py
```

#### 4. File Not Found Errors
**Symptoms**: Images or metadata not found
**Solutions**:
```bash
# Verify files exist
ls -la images/
ls -la image_metadata.json

# Re-run offline processing if needed
python run_offline_processing.py
```

### Getting Help

1. **Check Logs**: Review deployment logs for error details
2. **Run Health Check**: `python health_check.py`
3. **Test Locally**: `streamlit run src/web/app.py`
4. **Monitor Resources**: Use platform dashboards
5. **Rollback**: Use backup scripts if needed

## 🔄 Backup and Rollback

### Create Backup
```bash
./scripts/backup_rollback.sh backup stable_version
```

### List Backups
```bash
./scripts/backup_rollback.sh list
```

### Restore from Backup
```bash
./scripts/backup_rollback.sh restore stable_version
```

### Quick Rollback
```bash
./scripts/backup_rollback.sh rollback
```

## 🚀 CI/CD Automation

### GitHub Actions
The repository includes automated deployment via GitHub Actions:

1. **Set Repository Secrets**:
   - `HF_TOKEN`: Hugging Face token
   - `HF_USERNAME`: Hugging Face username
   - `RAILWAY_TOKEN`: Railway token
   - `RENDER_API_KEY`: Render API key

2. **Trigger Deployment**:
   - Push to `main` branch for automatic deployment
   - Use "Actions" tab for manual deployment with platform selection

3. **Monitor Workflow**:
   - Check "Actions" tab for deployment status
   - Review logs for any issues
   - Automatic issue creation on failures

## 📈 Performance Optimization

### For Free Tiers (Hugging Face Spaces)
```bash
export MEMORY_OPTIMIZATION=true
export CPU_ONLY_MODE=true
export BATCH_SIZE=16
export MAX_IMAGE_SIZE=256,256
export MAX_RESULTS=5
```

### For Paid Tiers (Railway, Render)
```bash
export MEMORY_OPTIMIZATION=false
export CPU_ONLY_MODE=false
export BATCH_SIZE=32
export MAX_IMAGE_SIZE=512,512
export MAX_RESULTS=10
```

## 🌐 Custom Domains

### Railway
```bash
railway domain add your-domain.com
```

### Render
- Configure in Render dashboard under "Settings > Custom Domains"

### Hugging Face Spaces
- Custom domains available for Pro subscribers

## 📋 Deployment Checklist

Before deploying, ensure:

- [ ] All required files are present
- [ ] Images are processed and metadata exists
- [ ] Environment variables are configured
- [ ] Docker build succeeds locally
- [ ] Health check passes
- [ ] Backup is created
- [ ] Platform tokens/keys are valid
- [ ] Repository is pushed to GitHub (for automated deployment)

## 🎯 Next Steps

After successful deployment:

1. **Test the Application**: Run sample queries to verify functionality
2. **Monitor Performance**: Set up monitoring and alerts
3. **Share with Users**: Provide access URLs and usage instructions
4. **Gather Feedback**: Collect user feedback for improvements
5. **Plan Updates**: Set up process for future deployments

## 📞 Support

For deployment issues:
1. Check this guide and troubleshooting section
2. Review platform-specific documentation
3. Test deployment locally first
4. Check repository issues for known problems
5. Create new issue with deployment logs if needed