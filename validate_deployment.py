#!/usr/bin/env python3
"""
Deployment validation script for AI Architectural Search System.
Validates that the deployment is ready and functional.
"""

import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config


def validate_local_files() -> Dict[str, Any]:
    """Validate that all required files exist locally."""
    print("🔍 Validating local files...")
    
    config = get_config()
    validation = {
        "status": "success",
        "checks": {},
        "issues": []
    }
    
    # Required files
    required_files = [
        "src/web/app.py",
        "config.py",
        "requirements.txt",
        "Dockerfile",
        "app.py",  # Hugging Face entry point
        config.metadata_file
    ]
    
    for file_path in required_files:
        exists = Path(file_path).exists()
        validation["checks"][file_path] = exists
        if not exists:
            validation["issues"].append(f"Missing required file: {file_path}")
            validation["status"] = "failed"
    
    # Required directories
    required_dirs = [
        "src/",
        "src/web/",
        "src/models/",
        "src/processors/",
        config.image_directory
    ]
    
    for dir_path in required_dirs:
        exists = Path(dir_path).exists()
        validation["checks"][dir_path] = exists
        if not exists:
            validation["issues"].append(f"Missing required directory: {dir_path}")
            validation["status"] = "failed"
    
    # Check image count
    if Path(config.image_directory).exists():
        image_count = len(list(Path(config.image_directory).rglob("*.jpg")))
        validation["checks"]["image_count"] = image_count
        if image_count == 0:
            validation["issues"].append("No images found in dataset")
            validation["status"] = "failed"
    
    print(f"✅ Local files validation: {validation['status']}")
    return validation


def validate_dependencies() -> Dict[str, Any]:
    """Validate that all Python dependencies are available."""
    print("📦 Validating dependencies...")
    
    validation = {
        "status": "success",
        "checks": {},
        "issues": []
    }
    
    # Core dependencies
    dependencies = [
        ("torch", "PyTorch"),
        ("transformers", "Transformers"),
        ("streamlit", "Streamlit"),
        ("PIL", "Pillow"),
        ("numpy", "NumPy"),
        ("clip", "CLIP")
    ]
    
    for module, name in dependencies:
        try:
            __import__(module)
            validation["checks"][name] = True
        except ImportError as e:
            validation["checks"][name] = False
            validation["issues"].append(f"Missing dependency: {name} ({e})")
            validation["status"] = "failed"
    
    print(f"✅ Dependencies validation: {validation['status']}")
    return validation


def validate_configuration() -> Dict[str, Any]:
    """Validate application configuration."""
    print("⚙️ Validating configuration...")
    
    validation = {
        "status": "success",
        "checks": {},
        "issues": []
    }
    
    try:
        config = get_config()
        
        # Validate configuration values
        checks = {
            "max_results_positive": config.max_results > 0,
            "similarity_threshold_valid": 0 <= config.similarity_threshold <= 1,
            "batch_size_positive": config.batch_size > 0,
            "environment_valid": config.environment in ['development', 'staging', 'production'],
            "log_level_valid": config.log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        }
        
        validation["checks"].update(checks)
        
        for check, passed in checks.items():
            if not passed:
                validation["issues"].append(f"Configuration validation failed: {check}")
                validation["status"] = "failed"
        
        # Additional configuration info
        validation["config_info"] = {
            "environment": config.environment,
            "memory_optimization": config.memory_optimization,
            "cpu_only_mode": config.cpu_only_mode,
            "max_results": config.max_results,
            "batch_size": config.batch_size
        }
        
    except Exception as e:
        validation["status"] = "failed"
        validation["issues"].append(f"Configuration error: {e}")
    
    print(f"✅ Configuration validation: {validation['status']}")
    return validation


def validate_model_loading() -> Dict[str, Any]:
    """Validate that AI models can be loaded."""
    print("🤖 Validating model loading...")
    
    validation = {
        "status": "success",
        "checks": {},
        "issues": []
    }
    
    try:
        # Test CLIP model import
        import clip
        import torch
        
        validation["checks"]["clip_import"] = True
        validation["checks"]["torch_available"] = True
        validation["checks"]["cuda_available"] = torch.cuda.is_available()
        
        # Test model loading (lightweight check)
        try:
            available_models = clip.available_models()
            validation["checks"]["clip_models_available"] = len(available_models) > 0
            validation["model_info"] = {
                "available_models": available_models,
                "cuda_available": torch.cuda.is_available(),
                "torch_version": torch.__version__
            }
        except Exception as e:
            validation["checks"]["clip_models_available"] = False
            validation["issues"].append(f"CLIP model availability check failed: {e}")
            validation["status"] = "failed"
        
    except ImportError as e:
        validation["status"] = "failed"
        validation["issues"].append(f"Model import failed: {e}")
        validation["checks"]["clip_import"] = False
        validation["checks"]["torch_available"] = False
    
    print(f"✅ Model validation: {validation['status']}")
    return validation


def validate_deployment_files() -> Dict[str, Any]:
    """Validate deployment-specific files."""
    print("🚀 Validating deployment files...")
    
    validation = {
        "status": "success",
        "checks": {},
        "issues": []
    }
    
    # Deployment files
    deployment_files = {
        "Dockerfile": "Docker containerization",
        "docker-compose.yml": "Docker Compose configuration",
        "railway.json": "Railway deployment config",
        "render.yaml": "Render deployment config",
        ".env.production": "Production environment config",
        "app.py": "Hugging Face Spaces entry point"
    }
    
    for file_path, description in deployment_files.items():
        exists = Path(file_path).exists()
        validation["checks"][file_path] = exists
        if not exists:
            validation["issues"].append(f"Missing deployment file: {file_path} ({description})")
            # Don't fail for missing deployment files, just warn
    
    # Deployment scripts
    script_files = [
        "scripts/deploy.sh",
        "scripts/deploy_huggingface.sh",
        "scripts/deploy_railway.sh",
        "scripts/deploy_render.sh",
        "scripts/monitor_deployment.sh",
        "scripts/backup_rollback.sh"
    ]
    
    for script_path in script_files:
        exists = Path(script_path).exists()
        executable = exists and Path(script_path).stat().st_mode & 0o111
        validation["checks"][f"{script_path}_exists"] = exists
        validation["checks"][f"{script_path}_executable"] = executable
        
        if not exists:
            validation["issues"].append(f"Missing deployment script: {script_path}")
        elif not executable:
            validation["issues"].append(f"Deployment script not executable: {script_path}")
    
    print(f"✅ Deployment files validation: {validation['status']}")
    return validation


def test_url_accessibility(url: str, timeout: int = 10) -> Dict[str, Any]:
    """Test if a deployment URL is accessible."""
    print(f"🌐 Testing URL accessibility: {url}")
    
    validation = {
        "status": "success",
        "url": url,
        "checks": {},
        "issues": [],
        "response_time": None
    }
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        response_time = time.time() - start_time
        
        validation["response_time"] = response_time
        validation["checks"]["url_accessible"] = response.status_code == 200
        validation["checks"]["response_time_acceptable"] = response_time < 30  # 30 seconds for initial load
        
        if response.status_code != 200:
            validation["status"] = "failed"
            validation["issues"].append(f"HTTP {response.status_code}: {response.reason}")
        
        if response_time > 30:
            validation["issues"].append(f"Slow response time: {response_time:.2f}s")
        
        # Test health endpoint if available
        try:
            health_url = f"{url.rstrip('/')}/_stcore/health"
            health_response = requests.get(health_url, timeout=5)
            validation["checks"]["health_endpoint"] = health_response.status_code == 200
        except:
            validation["checks"]["health_endpoint"] = False
        
    except requests.exceptions.Timeout:
        validation["status"] = "failed"
        validation["issues"].append("Request timeout")
        validation["checks"]["url_accessible"] = False
    except requests.exceptions.ConnectionError:
        validation["status"] = "failed"
        validation["issues"].append("Connection error")
        validation["checks"]["url_accessible"] = False
    except Exception as e:
        validation["status"] = "failed"
        validation["issues"].append(f"Request error: {e}")
        validation["checks"]["url_accessible"] = False
    
    print(f"✅ URL accessibility: {validation['status']}")
    return validation


def run_comprehensive_validation(deployment_urls: List[str] = None) -> Dict[str, Any]:
    """Run comprehensive deployment validation."""
    print("🔍 Running comprehensive deployment validation...")
    print("=" * 60)
    
    results = {
        "timestamp": time.time(),
        "overall_status": "success",
        "validations": {},
        "summary": {},
        "recommendations": []
    }
    
    # Local validations
    validations = [
        ("local_files", validate_local_files),
        ("dependencies", validate_dependencies),
        ("configuration", validate_configuration),
        ("model_loading", validate_model_loading),
        ("deployment_files", validate_deployment_files)
    ]
    
    failed_validations = []
    
    for name, validator in validations:
        try:
            result = validator()
            results["validations"][name] = result
            if result["status"] != "success":
                failed_validations.append(name)
        except Exception as e:
            results["validations"][name] = {
                "status": "error",
                "error": str(e)
            }
            failed_validations.append(name)
    
    # URL validations (if provided)
    if deployment_urls:
        results["validations"]["url_tests"] = {}
        for url in deployment_urls:
            url_result = test_url_accessibility(url)
            results["validations"]["url_tests"][url] = url_result
            if url_result["status"] != "success":
                failed_validations.append(f"url_{url}")
    
    # Overall status
    if failed_validations:
        results["overall_status"] = "failed"
        results["failed_validations"] = failed_validations
    
    # Generate summary
    results["summary"] = {
        "total_validations": len(validations) + (len(deployment_urls) if deployment_urls else 0),
        "passed_validations": len(validations) + (len(deployment_urls) if deployment_urls else 0) - len(failed_validations),
        "failed_validations": len(failed_validations),
        "success_rate": ((len(validations) + (len(deployment_urls) if deployment_urls else 0) - len(failed_validations)) / (len(validations) + (len(deployment_urls) if deployment_urls else 0))) * 100
    }
    
    # Generate recommendations
    if failed_validations:
        results["recommendations"] = generate_recommendations(results["validations"])
    
    return results


def generate_recommendations(validations: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on validation results."""
    recommendations = []
    
    # Check for common issues
    if "local_files" in validations and validations["local_files"]["status"] != "success":
        recommendations.append("Run 'python run_offline_processing.py' to generate missing metadata files")
        recommendations.append("Ensure all source files are present before deployment")
    
    if "dependencies" in validations and validations["dependencies"]["status"] != "success":
        recommendations.append("Run 'pip install -r requirements.txt' to install missing dependencies")
        recommendations.append("Consider using a virtual environment for clean dependency management")
    
    if "model_loading" in validations and validations["model_loading"]["status"] != "success":
        recommendations.append("Verify PyTorch and CLIP installations")
        recommendations.append("Check internet connectivity for model downloads")
    
    if "deployment_files" in validations:
        deployment_result = validations["deployment_files"]
        if any("executable" in check and not result for check, result in deployment_result["checks"].items()):
            recommendations.append("Run 'chmod +x scripts/*.sh' to make deployment scripts executable")
    
    return recommendations


def main():
    """Main validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate AI Architectural Search deployment")
    parser.add_argument("--urls", nargs="*", help="Deployment URLs to test")
    parser.add_argument("--output", help="Output file for validation results (JSON)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Run validation
    results = run_comprehensive_validation(args.urls)
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"📄 Results saved to: {args.output}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    summary = results["summary"]
    print(f"Overall Status: {'✅ PASSED' if results['overall_status'] == 'success' else '❌ FAILED'}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Validations: {summary['passed_validations']}/{summary['total_validations']} passed")
    
    if results["overall_status"] != "success":
        print(f"\n❌ Failed Validations: {', '.join(results.get('failed_validations', []))}")
        
        if results.get("recommendations"):
            print("\n💡 Recommendations:")
            for rec in results["recommendations"]:
                print(f"  • {rec}")
    
    # Verbose output
    if args.verbose:
        print(f"\n📋 Detailed Results:")
        print(json.dumps(results, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_status"] == "success" else 1)


if __name__ == "__main__":
    main()