#!/usr/bin/env python3
"""
Integration test script to validate test queries against the actual search system.

This script runs the predefined test queries through the search system and validates
the results to ensure the system meets accuracy requirements for demo presentation.
"""

import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.append('src')

from test_queries_validation import TestQueryDataset, QueryValidator, ValidationResult
from src.processors.search_engine import SearchEngine
from src.models.config import AppConfig


def load_search_system() -> SearchEngine:
    """Load and initialize the search system."""
    try:
        config = AppConfig()
        search_engine = SearchEngine(config)
        
        # Validate system readiness
        readiness = search_engine.validate_search_readiness()
        if not readiness['ready']:
            print("❌ Search system not ready:")
            for issue in readiness['issues']:
                print(f"   - {issue}")
            return None
        
        print("✅ Search system loaded and ready")
        print(f"   - Total images: {readiness['statistics']['total_images']}")
        print(f"   - Model status: {readiness['statistics']['model_status']}")
        return search_engine
        
    except Exception as e:
        print(f"❌ Failed to load search system: {e}")
        return None


def run_query_validation(search_engine: SearchEngine, dataset: TestQueryDataset) -> List[ValidationResult]:
    """Run all test queries and validate results."""
    
    validator = QueryValidator()
    validation_results = []
    
    print(f"\n🔍 Running {len(dataset.queries)} test queries...")
    print("=" * 60)
    
    for i, query in enumerate(dataset.queries, 1):
        print(f"{i:2d}. Testing: \"{query.query_text}\" ({query.priority} priority)")
        
        try:
            # Execute search
            start_time = time.time()
            search_results = search_engine.search(query.query_text, max_results=5)
            execution_time = time.time() - start_time
            
            # Convert search results to validation format
            result_data = []
            for result in search_results:
                result_data.append({
                    'image_path': result.image_path,
                    'description': result.description,
                    'features': result.features,
                    'confidence_score': result.confidence_score,
                    'similarity_score': result.similarity_score
                })
            
            # Validate results
            validation = validator.validate_query_results(query, result_data)
            validation.execution_time = execution_time  # Override with actual search time
            validation_results.append(validation)
            
            # Print immediate feedback
            status = "✅ PASS" if validation.passed else "❌ FAIL"
            print(f"    {status} - {len(result_data)} results, {validation.accuracy_score:.2f} accuracy, {execution_time:.2f}s")
            
            if not validation.passed:
                print(f"    Issues: {', '.join(validation.issues)}")
            
        except Exception as e:
            print(f"    ❌ ERROR - {str(e)}")
            # Create failed validation result
            failed_validation = ValidationResult(
                query=query,
                actual_results_count=0,
                material_matches=[],
                feature_matches=[],
                category_matches=[],
                accuracy_score=0.0,
                passed=False,
                issues=[f"Query execution failed: {str(e)}"],
                execution_time=0.0
            )
            validation_results.append(failed_validation)
    
    return validation_results


def generate_validation_summary(validation_results: List[ValidationResult]) -> Dict[str, Any]:
    """Generate and display validation summary."""
    
    validator = QueryValidator()
    report = validator.generate_validation_report(validation_results)
    
    print("\n📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    # Overall results
    summary = report['summary']
    print(f"Total Queries:     {summary['total_queries']}")
    print(f"Passed:           {summary['passed_queries']} ({summary['pass_rate']:.1%})")
    print(f"Failed:           {summary['failed_queries']}")
    print(f"Average Accuracy: {summary['avg_accuracy']:.2f}")
    print(f"Average Time:     {summary['avg_execution_time']:.2f}s")
    
    # Performance assessment
    if summary['pass_rate'] >= 0.9:
        print("🎉 EXCELLENT - System ready for demo!")
    elif summary['pass_rate'] >= 0.8:
        print("✅ GOOD - System meets requirements")
    elif summary['pass_rate'] >= 0.6:
        print("⚠️  ACCEPTABLE - Some issues need attention")
    else:
        print("❌ POOR - System needs significant improvement")
    
    # Priority breakdown
    if report['by_priority']:
        print(f"\n📈 Results by Priority:")
        for priority, stats in report['by_priority'].items():
            print(f"  {priority.capitalize():8}: {stats['passed']}/{stats['total']} ({stats['pass_rate']:.1%})")
    
    # Category breakdown
    if report['by_category']:
        print(f"\n🏗️  Results by Category:")
        for category, stats in report['by_category'].items():
            print(f"  {category:15}: {stats['passed']}/{stats['total']} ({stats['pass_rate']:.1%})")
    
    # Failed queries
    if report['failed_queries']:
        print(f"\n❌ Failed Queries:")
        for failure in report['failed_queries'][:5]:  # Show first 5 failures
            print(f"  \"{failure['query']}\" - {failure['accuracy']:.2f} accuracy")
            for issue in failure['issues'][:2]:  # Show first 2 issues
                print(f"    • {issue}")
    
    # Recommendations
    if report['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
    
    return report


def save_validation_report(validation_results: List[ValidationResult], output_file: str = "validation_report.json"):
    """Save detailed validation report to JSON file."""
    
    validator = QueryValidator()
    report = validator.generate_validation_report(validation_results)
    
    # Add detailed results
    report['detailed_results'] = []
    for result in validation_results:
        report['detailed_results'].append({
            'query_text': result.query.query_text,
            'query_priority': result.query.priority,
            'passed': result.passed,
            'accuracy_score': result.accuracy_score,
            'execution_time': result.execution_time,
            'actual_results_count': result.actual_results_count,
            'material_matches': result.material_matches,
            'feature_matches': result.feature_matches,
            'category_matches': result.category_matches,
            'issues': result.issues
        })
    
    # Add timestamp
    from datetime import datetime
    report['validation_timestamp'] = datetime.now().isoformat()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed report saved to {output_file}")


def main():
    """Main validation function."""
    
    print("🏗️  AI Architectural Search - Test Query Validation")
    print("=" * 60)
    
    # Load test dataset
    print("📋 Loading test dataset...")
    dataset = TestQueryDataset()
    
    # Show dataset info
    coverage = dataset.validate_query_coverage()
    print(f"   - {len(dataset.queries)} test queries loaded")
    print(f"   - {len(coverage['material_coverage']['covered'])} materials covered")
    print(f"   - {len(coverage['category_coverage']['covered'])} categories covered")
    
    # Load search system
    print("\n🔧 Initializing search system...")
    search_engine = load_search_system()
    
    if not search_engine:
        print("❌ Cannot proceed without working search system")
        return False
    
    # Run validation
    validation_results = run_query_validation(search_engine, dataset)
    
    # Generate summary
    report = generate_validation_summary(validation_results)
    
    # Save detailed report
    save_validation_report(validation_results)
    
    # Return success status
    return report['summary']['pass_rate'] >= 0.8


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)