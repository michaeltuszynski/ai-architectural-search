#!/usr/bin/env python3
"""
Run offline processing on the architectural image dataset.

This script executes the complete offline processing pipeline:
1. Load configuration
2. Initialize processing components
3. Process all images in the dataset
4. Generate embeddings and descriptions
5. Store metadata for search functionality
6. Validate processing results
"""

import sys
import logging
import json
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models.config import AppConfig
from src.processors.offline_processor import OfflineProcessor
from src.storage.metadata_store import MetadataStore


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('offline_processing.log')
        ]
    )
    return logging.getLogger(__name__)


def validate_dataset(image_directory: Path) -> dict:
    """Validate the dataset before processing."""
    validation_report = {
        "directory_exists": image_directory.exists(),
        "categories": {},
        "total_images": 0,
        "supported_formats": 0,
        "validation_passed": False
    }
    
    if not image_directory.exists():
        return validation_report
    
    # Check each category directory
    categories = ["brick_buildings", "glass_steel", "stone_facades", "mixed_materials"]
    supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    
    for category in categories:
        category_path = image_directory / category
        if category_path.exists():
            # Count image files
            image_files = []
            for ext in supported_extensions:
                image_files.extend(category_path.glob(f"*{ext}"))
                image_files.extend(category_path.glob(f"*{ext.upper()}"))
            
            validation_report["categories"][category] = {
                "exists": True,
                "image_count": len(image_files),
                "files": [f.name for f in sorted(image_files)]
            }
            validation_report["total_images"] += len(image_files)
            validation_report["supported_formats"] += len(image_files)
        else:
            validation_report["categories"][category] = {
                "exists": False,
                "image_count": 0,
                "files": []
            }
    
    # Check if validation passed
    validation_report["validation_passed"] = (
        validation_report["total_images"] >= 20 and
        all(cat["exists"] for cat in validation_report["categories"].values())
    )
    
    return validation_report


def run_processing_pipeline(config: AppConfig, logger: logging.Logger) -> dict:
    """Run the complete offline processing pipeline."""
    logger.info("Starting offline processing pipeline")
    
    # Validate dataset first
    image_directory = Path(config.image_directory)
    validation = validate_dataset(image_directory)
    
    logger.info(f"Dataset validation: {validation['validation_passed']}")
    logger.info(f"Total images found: {validation['total_images']}")
    
    if not validation["validation_passed"]:
        logger.error("Dataset validation failed")
        return {
            "success": False,
            "error": "Dataset validation failed",
            "validation": validation
        }
    
    # Initialize processing components
    try:
        logger.info("Initializing processing components...")
        processor = OfflineProcessor(config)
        
        # Get initial status
        initial_status = processor.get_processing_status()
        logger.info(f"Initial storage status: {initial_status['storage']['total_images']} images")
        
    except Exception as e:
        logger.error(f"Failed to initialize processor: {e}")
        return {
            "success": False,
            "error": f"Processor initialization failed: {e}",
            "validation": validation
        }
    
    # Process images
    try:
        logger.info("Starting image processing...")
        start_time = datetime.now()
        
        # Process all images (reprocess to ensure fresh embeddings)
        processed_count = processor.reprocess_all_images()
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        logger.info(f"Processing completed: {processed_count} images in {processing_time:.2f} seconds")
        
        # Get final status
        final_status = processor.get_processing_status()
        
        # Cleanup processor resources
        processor.cleanup()
        
        return {
            "success": True,
            "processed_count": processed_count,
            "processing_time_seconds": processing_time,
            "images_per_second": processed_count / processing_time if processing_time > 0 else 0,
            "initial_status": initial_status,
            "final_status": final_status,
            "validation": validation
        }
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        try:
            processor.cleanup()
        except:
            pass
        
        return {
            "success": False,
            "error": f"Processing failed: {e}",
            "validation": validation
        }


def validate_processing_results(config: AppConfig, logger: logging.Logger) -> dict:
    """Validate the results of offline processing."""
    logger.info("Validating processing results...")
    
    try:
        # Initialize metadata store
        metadata_store = MetadataStore(config)
        
        # Load all metadata
        all_metadata = metadata_store.load_all_metadata()
        
        # Get storage statistics
        storage_stats = metadata_store.get_storage_stats()
        
        # Validate metadata completeness
        validation_results = {
            "total_metadata_entries": len(all_metadata),
            "storage_stats": storage_stats,
            "sample_metadata": {},
            "validation_passed": True,
            "issues": []
        }
        
        # Check each metadata entry
        missing_embeddings = 0
        missing_descriptions = 0
        missing_features = 0
        
        # Sample a few entries for detailed validation
        sample_paths = list(all_metadata.keys())[:5]
        
        for path, metadata in all_metadata.items():
            # Check for missing data
            if metadata.embedding is None or len(metadata.embedding) == 0:
                missing_embeddings += 1
            
            if not metadata.description or metadata.description.strip() == "":
                missing_descriptions += 1
            
            if not metadata.features or len(metadata.features) == 0:
                missing_features += 1
            
            # Add to sample if in sample paths
            if path in sample_paths:
                validation_results["sample_metadata"][path] = {
                    "description": metadata.description,
                    "features": metadata.features,
                    "embedding_size": len(metadata.embedding) if metadata.embedding is not None else 0,
                    "file_size": metadata.file_size,
                    "dimensions": metadata.dimensions
                }
        
        # Record issues
        if missing_embeddings > 0:
            validation_results["issues"].append(f"{missing_embeddings} entries missing embeddings")
        
        if missing_descriptions > 0:
            validation_results["issues"].append(f"{missing_descriptions} entries missing descriptions")
        
        if missing_features > 0:
            validation_results["issues"].append(f"{missing_features} entries missing features")
        
        # Overall validation
        validation_results["validation_passed"] = (
            len(validation_results["issues"]) == 0 and
            len(all_metadata) >= 20
        )
        
        validation_results["completeness"] = {
            "embeddings": (len(all_metadata) - missing_embeddings) / len(all_metadata) * 100 if all_metadata else 0,
            "descriptions": (len(all_metadata) - missing_descriptions) / len(all_metadata) * 100 if all_metadata else 0,
            "features": (len(all_metadata) - missing_features) / len(all_metadata) * 100 if all_metadata else 0
        }
        
        logger.info(f"Validation completed: {validation_results['validation_passed']}")
        logger.info(f"Completeness - Embeddings: {validation_results['completeness']['embeddings']:.1f}%")
        logger.info(f"Completeness - Descriptions: {validation_results['completeness']['descriptions']:.1f}%")
        logger.info(f"Completeness - Features: {validation_results['completeness']['features']:.1f}%")
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return {
            "validation_passed": False,
            "error": f"Validation failed: {e}"
        }


def generate_processing_report(processing_results: dict, validation_results: dict) -> dict:
    """Generate comprehensive processing report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "processing": processing_results,
        "validation": validation_results,
        "summary": {
            "overall_success": processing_results.get("success", False) and validation_results.get("validation_passed", False),
            "total_images_processed": processing_results.get("processed_count", 0),
            "processing_time": processing_results.get("processing_time_seconds", 0),
            "metadata_entries": validation_results.get("total_metadata_entries", 0),
            "ready_for_search": False
        }
    }
    
    # Determine if system is ready for search
    report["summary"]["ready_for_search"] = (
        report["summary"]["overall_success"] and
        report["summary"]["total_images_processed"] >= 20 and
        report["summary"]["metadata_entries"] >= 20
    )
    
    return report


def main():
    """Main execution function."""
    print("AI Architectural Search - Offline Processing")
    print("=" * 50)
    
    # Setup logging
    logger = setup_logging()
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = AppConfig.load_config()
        
        # Ensure directories exist
        config.ensure_directories_exist()
        
        logger.info(f"Configuration loaded:")
        logger.info(f"  Image directory: {config.image_directory}")
        logger.info(f"  Metadata file: {config.metadata_file}")
        logger.info(f"  CLIP model: {config.clip_model_name}")
        logger.info(f"  Batch size: {config.batch_size}")
        
        # Run processing pipeline
        processing_results = run_processing_pipeline(config, logger)
        
        # Validate results if processing succeeded
        if processing_results.get("success", False):
            validation_results = validate_processing_results(config, logger)
        else:
            validation_results = {"validation_passed": False, "error": "Processing failed"}
        
        # Generate comprehensive report
        report = generate_processing_report(processing_results, validation_results)
        
        # Save report
        report_file = "offline_processing_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print(f"\nProcessing Summary:")
        print(f"  Overall Success: {report['summary']['overall_success']}")
        print(f"  Images Processed: {report['summary']['total_images_processed']}")
        print(f"  Processing Time: {report['summary']['processing_time']:.2f} seconds")
        print(f"  Metadata Entries: {report['summary']['metadata_entries']}")
        print(f"  Ready for Search: {report['summary']['ready_for_search']}")
        
        if report['summary']['ready_for_search']:
            print(f"\n✅ Offline processing completed successfully!")
            print(f"   The system is ready for search functionality.")
        else:
            print(f"\n❌ Processing completed with issues.")
            if processing_results.get("error"):
                print(f"   Processing Error: {processing_results['error']}")
            if validation_results.get("error"):
                print(f"   Validation Error: {validation_results['error']}")
        
        print(f"\nDetailed report saved to: {report_file}")
        print(f"Processing log saved to: offline_processing.log")
        
        # Return appropriate exit code
        return 0 if report['summary']['overall_success'] else 1
        
    except Exception as e:
        logger.error(f"Offline processing failed: {e}")
        print(f"\n❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)