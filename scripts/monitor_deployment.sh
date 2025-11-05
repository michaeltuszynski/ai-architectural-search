#!/bin/bash
# Monitoring script for deployed applications

set -e

# Configuration
HEALTH_CHECK_INTERVAL=30  # seconds
MAX_RETRIES=5
TIMEOUT=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check URL health
check_url_health() {
    local url=$1
    local name=$2
    
    print_status $BLUE "🔍 Checking $name at $url"
    
    # Check if URL is reachable
    if curl -s --max-time $TIMEOUT "$url" > /dev/null; then
        print_status $GREEN "✅ $name is reachable"
        
        # Check health endpoint if available
        health_url="${url}/_stcore/health"
        if curl -s --max-time $TIMEOUT "$health_url" > /dev/null; then
            print_status $GREEN "✅ $name health check passed"
            return 0
        else
            print_status $YELLOW "⚠️  $name health endpoint not available"
            return 1
        fi
    else
        print_status $RED "❌ $name is not reachable"
        return 1
    fi
}

# Function to run performance test
run_performance_test() {
    local url=$1
    local name=$2
    
    print_status $BLUE "⚡ Running performance test for $name"
    
    # Simple response time test
    response_time=$(curl -o /dev/null -s -w '%{time_total}' --max-time 30 "$url" || echo "timeout")
    
    if [ "$response_time" != "timeout" ]; then
        # Convert to milliseconds
        response_ms=$(echo "$response_time * 1000" | bc -l 2>/dev/null || echo "unknown")
        print_status $GREEN "📊 Response time: ${response_ms}ms"
        
        # Check if response time is acceptable (< 5 seconds)
        if (( $(echo "$response_time < 5.0" | bc -l 2>/dev/null || echo "0") )); then
            print_status $GREEN "✅ Performance test passed"
            return 0
        else
            print_status $YELLOW "⚠️  Slow response time: ${response_time}s"
            return 1
        fi
    else
        print_status $RED "❌ Performance test failed (timeout)"
        return 1
    fi
}

# Function to monitor deployment
monitor_deployment() {
    local url=$1
    local name=$2
    local retries=0
    
    print_status $BLUE "🚀 Starting monitoring for $name"
    print_status $BLUE "📍 URL: $url"
    
    while [ $retries -lt $MAX_RETRIES ]; do
        echo ""
        print_status $BLUE "📊 Health check #$((retries + 1))"
        
        if check_url_health "$url" "$name"; then
            print_status $GREEN "✅ $name is healthy!"
            
            # Run performance test
            run_performance_test "$url" "$name"
            
            print_status $GREEN "🎉 Monitoring completed successfully for $name"
            return 0
        else
            retries=$((retries + 1))
            if [ $retries -lt $MAX_RETRIES ]; then
                print_status $YELLOW "⏳ Retrying in $HEALTH_CHECK_INTERVAL seconds... ($retries/$MAX_RETRIES)"
                sleep $HEALTH_CHECK_INTERVAL
            fi
        fi
    done
    
    print_status $RED "❌ $name failed health checks after $MAX_RETRIES attempts"
    return 1
}

# Function to get deployment URLs
get_deployment_urls() {
    local urls=()
    
    # Check for Hugging Face Spaces URL
    if [ -n "$HF_USERNAME" ] && [ -n "$HF_SPACE_NAME" ]; then
        urls+=("https://huggingface.co/spaces/$HF_USERNAME/$HF_SPACE_NAME" "Hugging Face Spaces")
    fi
    
    # Check for Railway URL
    if command -v railway &> /dev/null && railway status &> /dev/null; then
        railway_url=$(railway domain 2>/dev/null || echo "")
        if [ -n "$railway_url" ]; then
            urls+=("https://$railway_url" "Railway")
        fi
    fi
    
    # Check for custom URLs from environment
    if [ -n "$DEPLOYMENT_URL" ]; then
        urls+=("$DEPLOYMENT_URL" "Custom Deployment")
    fi
    
    echo "${urls[@]}"
}

# Main monitoring function
main() {
    print_status $BLUE "🔍 AI Architectural Search - Deployment Monitor"
    echo ""
    
    # Get URLs to monitor
    urls=($(get_deployment_urls))
    
    if [ ${#urls[@]} -eq 0 ]; then
        print_status $YELLOW "⚠️  No deployment URLs found"
        print_status $BLUE "💡 Set environment variables:"
        echo "   - HF_USERNAME and HF_SPACE_NAME for Hugging Face Spaces"
        echo "   - DEPLOYMENT_URL for custom deployments"
        echo "   - Or run from a Railway project directory"
        exit 1
    fi
    
    # Monitor each deployment
    local all_healthy=true
    
    for ((i=0; i<${#urls[@]}; i+=2)); do
        url="${urls[i]}"
        name="${urls[i+1]}"
        
        if ! monitor_deployment "$url" "$name"; then
            all_healthy=false
        fi
        
        echo ""
        echo "----------------------------------------"
    done
    
    # Final status
    if $all_healthy; then
        print_status $GREEN "🎉 All deployments are healthy!"
        exit 0
    else
        print_status $RED "❌ Some deployments have issues"
        exit 1
    fi
}

# Handle command line arguments
case "${1:-monitor}" in
    "monitor")
        main
        ;;
    "check")
        if [ -z "$2" ]; then
            echo "Usage: $0 check <url>"
            exit 1
        fi
        check_url_health "$2" "Custom URL"
        ;;
    "performance")
        if [ -z "$2" ]; then
            echo "Usage: $0 performance <url>"
            exit 1
        fi
        run_performance_test "$2" "Custom URL"
        ;;
    *)
        echo "Usage: $0 [monitor|check|performance] [url]"
        echo ""
        echo "Commands:"
        echo "  monitor      - Monitor all known deployments (default)"
        echo "  check <url>  - Check health of specific URL"
        echo "  performance <url> - Run performance test on specific URL"
        exit 1
        ;;
esac