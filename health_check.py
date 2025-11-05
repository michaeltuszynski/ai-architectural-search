#!/usr/bin/env python3
"""
Health check script for deployment monitoring.
Can be used by load balancers and monitoring systems.
"""

import sys
import json
import time
import psutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config


def check_system_health():
    """Perform comprehensive system health check."""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {},
        "metrics": {}
    }
    
    try:
        config = get_config()
        
        # Check file system
        health_status["checks"]["filesystem"] = check_filesystem(config)
        
        # Check system resources
        health_status["checks"]["resources"] = check_resources()
        
        # Check model availability
        health_status["checks"]["model"] = check_model_availability()
        
        # Collect metrics
        health_status["metrics"] = collect_metrics()
        
        # Determine overall status
        failed_checks = [name for name, result in health_status["checks"].items() if not result["healthy"]]
        
        if failed_checks:
            health_status["status"] = "unhealthy"
            health_status["failed_checks"] = failed_checks
        
    except Exception as e:
        health_status["status"] = "error"
        health_status["error"] = str(e)
    
    return health_status


def check_filesystem(config):
    """Check if required files and directories exist."""
    try:
        checks = {
            "images_directory": Path(config.image_directory).exists(),
            "metadata_file": Path(config.metadata_file).exists(),
        }
        
        # Count images
        if checks["images_directory"]:
            image_count = len(list(Path(config.image_directory).rglob("*.jpg")))
            checks["image_count"] = image_count
            checks["has_images"] = image_count > 0
        else:
            checks["image_count"] = 0
            checks["has_images"] = False
        
        healthy = all([
            checks["images_directory"],
            checks["metadata_file"],
            checks["has_images"]
        ])
        
        return {
            "healthy": healthy,
            "details": checks
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e)
        }


def check_resources():
    """Check system resource availability."""
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        # Define minimum requirements
        min_memory_gb = 1.0  # 1GB minimum
        min_disk_gb = 0.5    # 500MB minimum
        
        memory_ok = memory.available > min_memory_gb * 1024**3
        disk_ok = disk.free > min_disk_gb * 1024**3
        
        return {
            "healthy": memory_ok and disk_ok,
            "details": {
                "memory_available_gb": round(memory.available / 1024**3, 2),
                "memory_ok": memory_ok,
                "disk_free_gb": round(disk.free / 1024**3, 2),
                "disk_ok": disk_ok,
                "cpu_count": psutil.cpu_count()
            }
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e)
        }


def check_model_availability():
    """Check if CLIP model can be loaded."""
    try:
        # Try to import required modules
        import torch
        import clip
        
        # Basic availability check (don't actually load the model for speed)
        model_available = True
        
        return {
            "healthy": model_available,
            "details": {
                "torch_available": True,
                "clip_available": True,
                "cuda_available": torch.cuda.is_available()
            }
        }
        
    except ImportError as e:
        return {
            "healthy": False,
            "error": f"Import error: {e}"
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e)
        }


def collect_metrics():
    """Collect system metrics for monitoring."""
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            "memory_usage_percent": memory.percent,
            "memory_available_gb": round(memory.available / 1024**3, 2),
            "disk_usage_percent": round((disk.used / disk.total) * 100, 2),
            "disk_free_gb": round(disk.free / 1024**3, 2),
            "cpu_usage_percent": cpu_percent,
            "uptime_seconds": time.time() - psutil.boot_time()
        }
        
    except Exception as e:
        return {"error": str(e)}


def main():
    """Main health check function."""
    health_status = check_system_health()
    
    # Output JSON for programmatic use
    print(json.dumps(health_status, indent=2))
    
    # Exit with appropriate code
    if health_status["status"] == "healthy":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()