#!/bin/bash
# Main deployment orchestration script

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="deployment.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" >> "$LOG_FILE"
}

# Function to show usage
show_usage() {
    print_status $BLUE "🚀 AI Architectural Search - Deployment Tool"
    echo ""
    echo "Usage: $0 <platform> [options]"
    echo ""
    echo "Platforms:"
    echo "  huggingface     - Deploy to Hugging Face Spaces (free)"
    echo "  railway         - Deploy to Railway (paid)"
    echo "  render          - Deploy to Render (paid)"
    echo "  docker          - Build and test Docker image locally"
    echo "  all             - Deploy to all configured platforms"
    echo ""
    echo "Options:"
    echo "  --backup        - Create backup before deployment"
    echo "  --no-test       - Skip pre-deployment tests"
    echo "  --monitor       - Monitor deployment after completion"
    echo "  --dry-run       - Show what would be deployed without actually deploying"
    echo ""
    echo "Environment Variables:"
    echo "  HF_TOKEN        - Hugging Face token (for huggingface deployment)"
    echo "  HF_USERNAME     - Hugging Face username"
    echo "  RAILWAY_TOKEN   - Railway token (for railway deployment)"
    echo "  RENDER_API_KEY  - Render API key (for render deployment)"
    echo "  GITHUB_REPO     - GitHub repository (username/repo-name)"
    echo ""
    echo "Examples:"
    echo "  $0 huggingface --backup"
    echo "  $0 railway --monitor"
    echo "  $0 docker"
    echo "  $0 all --backup --monitor"
}

# Function to run pre-deployment checks
run_pre_checks() {
    print_status $BLUE "🔍 Running pre-deployment checks..."
    
    # Check if we're in the right directory
    if [ ! -f "$PROJECT_ROOT/config.py" ] || [ ! -d "$PROJECT_ROOT/src" ]; then
        print_status $RED "❌ Error: Not in project root directory"
        return 1
    fi
    
    # Check if required files exist
    local required_files=("requirements.txt" "Dockerfile" "src/web/app.py" "config.py")
    for file in "${required_files[@]}"; do
        if [ ! -f "$PROJECT_ROOT/$file" ]; then
            print_status $RED "❌ Error: Required file missing: $file"
            return 1
        fi
    done
    
    # Check if images and metadata exist
    if [ ! -d "$PROJECT_ROOT/images" ]; then
        print_status $RED "❌ Error: Images directory not found"
        return 1
    fi
    
    if [ ! -f "$PROJECT_ROOT/image_metadata.json" ]; then
        print_status $RED "❌ Error: Image metadata file not found"
        return 1
    fi
    
    # Count images
    local image_count=$(find "$PROJECT_ROOT/images" -name "*.jpg" | wc -l)
    if [ "$image_count" -eq 0 ]; then
        print_status $RED "❌ Error: No images found in dataset"
        return 1
    fi
    
    print_status $GREEN "✅ Pre-deployment checks passed ($image_count images found)"
    return 0
}

# Function to run tests
run_tests() {
    if [ "$SKIP_TESTS" = "true" ]; then
        print_status $YELLOW "⏭️  Skipping tests (--no-test flag)"
        return 0
    fi
    
    print_status $BLUE "🧪 Running tests..."
    
    cd "$PROJECT_ROOT"
    
    # Run Python tests if available
    if [ -d "tests" ] && command -v pytest &> /dev/null; then
        print_status $BLUE "🐍 Running Python tests..."
        if pytest tests/ -v --tb=short; then
            print_status $GREEN "✅ Python tests passed"
        else
            print_status $YELLOW "⚠️  Some Python tests failed (continuing anyway)"
        fi
    fi
    
    # Test Docker build
    print_status $BLUE "🐳 Testing Docker build..."
    if docker build -t ai-architectural-search-test . > /dev/null 2>&1; then
        print_status $GREEN "✅ Docker build successful"
        
        # Test basic import
        if docker run --rm ai-architectural-search-test python -c "import torch; import clip; print('Dependencies OK')" > /dev/null 2>&1; then
            print_status $GREEN "✅ Dependencies test passed"
        else
            print_status $YELLOW "⚠️  Dependencies test failed"
        fi
        
        # Cleanup test image
        docker rmi ai-architectural-search-test > /dev/null 2>&1 || true
    else
        print_status $RED "❌ Docker build failed"
        return 1
    fi
    
    return 0
}

# Function to create backup
create_backup() {
    if [ "$CREATE_BACKUP" = "true" ]; then
        print_status $BLUE "💾 Creating pre-deployment backup..."
        cd "$PROJECT_ROOT"
        
        if [ -f "scripts/backup_rollback.sh" ]; then
            local backup_name=$(bash scripts/backup_rollback.sh backup "pre_deploy_$(date +%Y%m%d_%H%M%S)")
            print_status $GREEN "✅ Backup created: $backup_name"
        else
            print_status $YELLOW "⚠️  Backup script not found, skipping backup"
        fi
    fi
}

# Function to deploy to specific platform
deploy_platform() {
    local platform=$1
    
    print_status $BLUE "🚀 Deploying to $platform..."
    
    cd "$PROJECT_ROOT"
    
    case $platform in
        "huggingface")
            if [ -f "scripts/deploy_huggingface.sh" ]; then
                bash scripts/deploy_huggingface.sh
            else
                print_status $RED "❌ Hugging Face deployment script not found"
                return 1
            fi
            ;;
        "railway")
            if [ -f "scripts/deploy_railway.sh" ]; then
                bash scripts/deploy_railway.sh
            else
                print_status $RED "❌ Railway deployment script not found"
                return 1
            fi
            ;;
        "render")
            if [ -f "scripts/deploy_render.sh" ]; then
                bash scripts/deploy_render.sh
            else
                print_status $RED "❌ Render deployment script not found"
                return 1
            fi
            ;;
        "docker")
            print_status $BLUE "🐳 Building Docker image..."
            docker build -t ai-architectural-search .
            print_status $GREEN "✅ Docker image built successfully"
            print_status $BLUE "💡 Run with: docker run -p 8501:8501 ai-architectural-search"
            ;;
        *)
            print_status $RED "❌ Unknown platform: $platform"
            return 1
            ;;
    esac
}

# Function to monitor deployments
monitor_deployments() {
    if [ "$MONITOR_DEPLOYMENT" = "true" ]; then
        print_status $BLUE "📊 Monitoring deployments..."
        
        if [ -f "scripts/monitor_deployment.sh" ]; then
            sleep 30  # Wait for deployment to start
            bash scripts/monitor_deployment.sh
        else
            print_status $YELLOW "⚠️  Monitoring script not found, skipping monitoring"
        fi
    fi
}

# Main deployment function
main() {
    local platform="$1"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backup)
                CREATE_BACKUP="true"
                shift
                ;;
            --no-test)
                SKIP_TESTS="true"
                shift
                ;;
            --monitor)
                MONITOR_DEPLOYMENT="true"
                shift
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                if [ -z "$platform" ]; then
                    platform="$1"
                fi
                shift
                ;;
        esac
    done
    
    # Show usage if no platform specified
    if [ -z "$platform" ]; then
        show_usage
        exit 1
    fi
    
    # Initialize log file
    echo "=== Deployment started at $(date) ===" > "$LOG_FILE"
    
    print_status $BLUE "🚀 Starting deployment to $platform"
    
    if [ "$DRY_RUN" = "true" ]; then
        print_status $YELLOW "🔍 DRY RUN MODE - No actual deployment will occur"
    fi
    
    # Run pre-deployment checks
    if ! run_pre_checks; then
        print_status $RED "❌ Pre-deployment checks failed"
        exit 1
    fi
    
    # Run tests
    if ! run_tests; then
        print_status $RED "❌ Tests failed"
        exit 1
    fi
    
    # Create backup
    create_backup
    
    # Deploy to platform(s)
    if [ "$DRY_RUN" != "true" ]; then
        if [ "$platform" = "all" ]; then
            local platforms=("huggingface" "railway" "render")
            local failed_platforms=()
            
            for p in "${platforms[@]}"; do
                if ! deploy_platform "$p"; then
                    failed_platforms+=("$p")
                    print_status $YELLOW "⚠️  Deployment to $p failed, continuing with others..."
                fi
            done
            
            if [ ${#failed_platforms[@]} -eq 0 ]; then
                print_status $GREEN "✅ All deployments completed successfully"
            else
                print_status $YELLOW "⚠️  Some deployments failed: ${failed_platforms[*]}"
            fi
        else
            if ! deploy_platform "$platform"; then
                print_status $RED "❌ Deployment to $platform failed"
                exit 1
            fi
            
            print_status $GREEN "✅ Deployment to $platform completed successfully"
        fi
        
        # Monitor deployments
        monitor_deployments
    else
        print_status $BLUE "🔍 DRY RUN: Would deploy to $platform"
    fi
    
    print_status $GREEN "🎉 Deployment process completed!"
    print_status $BLUE "📋 Check $LOG_FILE for detailed logs"
}

# Change to project root
cd "$PROJECT_ROOT"

# Run main function
main "$@"