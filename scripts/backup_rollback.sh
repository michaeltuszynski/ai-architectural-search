#!/bin/bash
# Backup and rollback script for deployments

set -e

# Configuration
BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
MAX_BACKUPS=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Create backup of current deployment
create_backup() {
    local backup_name="${1:-deployment_$TIMESTAMP}"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    print_status $BLUE "📦 Creating backup: $backup_name"
    
    # Create backup directory
    mkdir -p "$backup_path"
    
    # Backup application files
    print_status $BLUE "📋 Backing up application files..."
    
    # Core application files
    cp -r src/ "$backup_path/" 2>/dev/null || true
    cp config.py "$backup_path/" 2>/dev/null || true
    cp requirements.txt "$backup_path/" 2>/dev/null || true
    cp app.py "$backup_path/" 2>/dev/null || true
    
    # Deployment configurations
    cp Dockerfile "$backup_path/" 2>/dev/null || true
    cp docker-compose.yml "$backup_path/" 2>/dev/null || true
    cp railway.json "$backup_path/" 2>/dev/null || true
    cp render.yaml "$backup_path/" 2>/dev/null || true
    
    # Environment configurations
    cp .env.production "$backup_path/" 2>/dev/null || true
    cp .env.example "$backup_path/" 2>/dev/null || true
    
    # Data files (if they exist and are not too large)
    if [ -f "image_metadata.json" ] && [ $(stat -f%z "image_metadata.json" 2>/dev/null || stat -c%s "image_metadata.json" 2>/dev/null || echo 0) -lt 10485760 ]; then
        cp image_metadata.json "$backup_path/" 2>/dev/null || true
    fi
    
    # Create backup manifest
    cat > "$backup_path/backup_manifest.json" << EOF
{
  "backup_name": "$backup_name",
  "timestamp": "$TIMESTAMP",
  "created_by": "$(whoami)",
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "git_branch": "$(git branch --show-current 2>/dev/null || echo 'unknown')",
  "files_backed_up": [
$(find "$backup_path" -type f -not -name "backup_manifest.json" | sed 's/.*/"&"/' | paste -sd, -)
  ]
}
EOF
    
    print_status $GREEN "✅ Backup created: $backup_path"
    
    # Clean up old backups
    cleanup_old_backups
    
    echo "$backup_name"
}

# List available backups
list_backups() {
    print_status $BLUE "📋 Available backups:"
    
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A $BACKUP_DIR 2>/dev/null)" ]; then
        print_status $YELLOW "⚠️  No backups found"
        return 1
    fi
    
    echo ""
    printf "%-25s %-20s %-15s %s\n" "BACKUP NAME" "TIMESTAMP" "GIT COMMIT" "FILES"
    printf "%-25s %-20s %-15s %s\n" "----------" "---------" "----------" "-----"
    
    for backup in "$BACKUP_DIR"/*; do
        if [ -d "$backup" ] && [ -f "$backup/backup_manifest.json" ]; then
            local name=$(basename "$backup")
            local timestamp=$(jq -r '.timestamp // "unknown"' "$backup/backup_manifest.json" 2>/dev/null || echo "unknown")
            local commit=$(jq -r '.git_commit // "unknown"' "$backup/backup_manifest.json" 2>/dev/null | cut -c1-8)
            local file_count=$(jq -r '.files_backed_up | length' "$backup/backup_manifest.json" 2>/dev/null || echo "?")
            
            printf "%-25s %-20s %-15s %s\n" "$name" "$timestamp" "$commit" "$file_count files"
        fi
    done
    
    echo ""
}

# Restore from backup
restore_backup() {
    local backup_name="$1"
    
    if [ -z "$backup_name" ]; then
        print_status $RED "❌ Error: Backup name required"
        list_backups
        return 1
    fi
    
    local backup_path="$BACKUP_DIR/$backup_name"
    
    if [ ! -d "$backup_path" ]; then
        print_status $RED "❌ Error: Backup not found: $backup_name"
        list_backups
        return 1
    fi
    
    print_status $YELLOW "⚠️  WARNING: This will overwrite current files!"
    print_status $BLUE "📦 Restoring from backup: $backup_name"
    
    # Create a backup of current state before restoring
    current_backup=$(create_backup "pre_restore_$TIMESTAMP")
    print_status $BLUE "💾 Current state backed up as: $current_backup"
    
    # Restore files
    print_status $BLUE "📋 Restoring files..."
    
    # Restore application files
    [ -d "$backup_path/src" ] && cp -r "$backup_path/src/" . 2>/dev/null || true
    [ -f "$backup_path/config.py" ] && cp "$backup_path/config.py" . 2>/dev/null || true
    [ -f "$backup_path/requirements.txt" ] && cp "$backup_path/requirements.txt" . 2>/dev/null || true
    [ -f "$backup_path/app.py" ] && cp "$backup_path/app.py" . 2>/dev/null || true
    
    # Restore deployment configurations
    [ -f "$backup_path/Dockerfile" ] && cp "$backup_path/Dockerfile" . 2>/dev/null || true
    [ -f "$backup_path/docker-compose.yml" ] && cp "$backup_path/docker-compose.yml" . 2>/dev/null || true
    [ -f "$backup_path/railway.json" ] && cp "$backup_path/railway.json" . 2>/dev/null || true
    [ -f "$backup_path/render.yaml" ] && cp "$backup_path/render.yaml" . 2>/dev/null || true
    
    # Restore environment configurations
    [ -f "$backup_path/.env.production" ] && cp "$backup_path/.env.production" . 2>/dev/null || true
    
    # Restore data files
    [ -f "$backup_path/image_metadata.json" ] && cp "$backup_path/image_metadata.json" . 2>/dev/null || true
    
    print_status $GREEN "✅ Backup restored successfully"
    print_status $BLUE "💡 To rollback this restore, use backup: $current_backup"
}

# Clean up old backups
cleanup_old_backups() {
    if [ ! -d "$BACKUP_DIR" ]; then
        return 0
    fi
    
    local backup_count=$(ls -1 "$BACKUP_DIR" | wc -l)
    
    if [ "$backup_count" -gt "$MAX_BACKUPS" ]; then
        print_status $BLUE "🧹 Cleaning up old backups (keeping $MAX_BACKUPS most recent)"
        
        # Remove oldest backups
        ls -1t "$BACKUP_DIR" | tail -n +$((MAX_BACKUPS + 1)) | while read old_backup; do
            rm -rf "$BACKUP_DIR/$old_backup"
            print_status $BLUE "🗑️  Removed old backup: $old_backup"
        done
    fi
}

# Rollback to previous deployment
rollback_deployment() {
    print_status $BLUE "🔄 Rolling back to previous deployment"
    
    # Find the most recent backup (excluding pre_restore backups)
    local latest_backup=$(ls -1t "$BACKUP_DIR" 2>/dev/null | grep -v "pre_restore" | head -n1)
    
    if [ -z "$latest_backup" ]; then
        print_status $RED "❌ Error: No backup available for rollback"
        return 1
    fi
    
    print_status $BLUE "📦 Rolling back to: $latest_backup"
    restore_backup "$latest_backup"
    
    print_status $GREEN "✅ Rollback completed"
}

# Main function
main() {
    case "${1:-help}" in
        "backup")
            create_backup "$2"
            ;;
        "list")
            list_backups
            ;;
        "restore")
            restore_backup "$2"
            ;;
        "rollback")
            rollback_deployment
            ;;
        "cleanup")
            cleanup_old_backups
            ;;
        "help"|*)
            print_status $BLUE "🔧 AI Architectural Search - Backup & Rollback Tool"
            echo ""
            echo "Usage: $0 <command> [options]"
            echo ""
            echo "Commands:"
            echo "  backup [name]    - Create backup of current deployment"
            echo "  list            - List available backups"
            echo "  restore <name>  - Restore from specific backup"
            echo "  rollback        - Rollback to most recent backup"
            echo "  cleanup         - Remove old backups (keep $MAX_BACKUPS most recent)"
            echo "  help            - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 backup                    # Create backup with timestamp"
            echo "  $0 backup stable_v1         # Create named backup"
            echo "  $0 list                     # Show available backups"
            echo "  $0 restore stable_v1        # Restore specific backup"
            echo "  $0 rollback                 # Quick rollback to previous"
            ;;
    esac
}

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Run main function
main "$@"