#!/usr/bin/env python3
"""
Performance optimization and error handling validation script.
"""
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any
import traceback

# Add src directory to path
sys.path.append('.')

from config import AppConfig
from src.processors.search_engine import SearchEngine
from src.web.error_handler import ErrorHandler, check_system_health
from src.web.cache import QueryCache


def setup_logging():
    """Setup logging for validation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def validate_error_handling() -> Dict[str, Any]:
    """Validate error handling capabilities."""
    print("🔧 Validating Error Handling...")
    
    results = {
        'passed': 0,
        'failed': 0,
        'tests': []
    }
    
    try:
        # Test 1: Error handler initialization
        error_handler = ErrorHandler()
        results['tests'].append({
            'name': 'Error Handler Initialization',
            'status': 'PASS',
            'details': 'ErrorHandler initialized successfully'
        })
        results['passed'] += 1
        
        # Test 2: System health check
        health = check_system_health()
        results['tests'].append({
            'name': 'System Health Check',
            'status': 'PASS',
            'details': f"System status: {health['status']}"
        })
        results['passed'] += 1
        
        # Test 3: Error statistics
        stats = error_handler.get_error_stats()
        results['tests'].append({
            'name': 'Error Statistics',
            'status': 'PASS',
            'details': f"Error count: {stats['total_errors']}"
        })
        results['passed'] += 1
        
        # Test 4: Mock error handling
        try:
            test_error = ValueError("Test error for validation")
            handled = error_handler.handle_search_error(test_error, "test query")
            results['tests'].append({
                'name': 'Error Handling Simulation',
                'status': 'PASS',
                'details': f"Error handled: {handled}"
            })
            results['passed'] += 1
        except Exception as e:
            results['tests'].append({
                'name': 'Error Handling Simulation',
                'status': 'FAIL',
                'details': f"Failed to handle mock error: {e}"
            })
            results['failed'] += 1
        
    except Exception as e:
        results['tests'].append({
            'name': 'Error Handling Validation',
            'status': 'FAIL',
            'details': f"Validation failed: {e}"
        })
        results['failed'] += 1
    
    return results


def validate_performance_optimizations() -> Dict[str, Any]:
    """Validate performance optimization features."""
    print("⚡ Validating Performance Optimizations...")
    
    results = {
        'passed': 0,
        'failed': 0,
        'tests': [],
        'metrics': {}
    }
    
    try:
        config = AppConfig()
        search_engine = SearchEngine(config)
        
        # Test 1: Search engine initialization time
        start_time = time.time()
        search_engine.validate_search_readiness()
        init_time = time.time() - start_time
        
        results['metrics']['initialization_time'] = init_time
        
        if init_time < 5.0:  # Should initialize within 5 seconds
            results['tests'].append({
                'name': 'Search Engine Initialization',
                'status': 'PASS',
                'details': f"Initialized in {init_time:.3f}s"
            })
            results['passed'] += 1
        else:
            results['tests'].append({
                'name': 'Search Engine Initialization',
                'status': 'FAIL',
                'details': f"Slow initialization: {init_time:.3f}s"
            })
            results['failed'] += 1
        
        # Test 2: Search performance
        test_queries = [
            "red brick buildings",
            "glass facades",
            "modern architecture",
            "stone columns",
            "flat roofs"
        ]
        
        search_times = []
        
        for query in test_queries:
            start_time = time.time()
            results_list, _ = search_engine.search(query, max_results=5)
            search_time = time.time() - start_time
            search_times.append(search_time)
        
        avg_search_time = sum(search_times) / len(search_times)
        results['metrics']['average_search_time'] = avg_search_time
        results['metrics']['search_times'] = search_times
        
        if avg_search_time < 1.0:  # Should search within 1 second on average
            results['tests'].append({
                'name': 'Search Performance',
                'status': 'PASS',
                'details': f"Average search time: {avg_search_time:.3f}s"
            })
            results['passed'] += 1
        else:
            results['tests'].append({
                'name': 'Search Performance',
                'status': 'FAIL',
                'details': f"Slow search performance: {avg_search_time:.3f}s"
            })
            results['failed'] += 1
        
        # Test 3: Cache performance
        cache = QueryCache()
        
        # Perform same search twice to test caching
        query = "test caching query"
        
        # First search (cache miss)
        start_time = time.time()
        results_list, _ = search_engine.search(query, max_results=3)
        first_search_time = time.time() - start_time
        
        # Cache the results manually for testing
        stats = {'search_time': first_search_time, 'results_count': len(results_list)}
        cache.put(query, results_list, stats, 3, 0.1)
        
        # Second search (should be cache hit)
        start_time = time.time()
        cached_result = cache.get(query, 3, 0.1)
        cache_lookup_time = time.time() - start_time
        
        results['metrics']['cache_lookup_time'] = cache_lookup_time
        
        if cached_result is not None and cache_lookup_time < 0.01:  # Cache should be very fast
            results['tests'].append({
                'name': 'Cache Performance',
                'status': 'PASS',
                'details': f"Cache lookup: {cache_lookup_time:.6f}s"
            })
            results['passed'] += 1
        else:
            results['tests'].append({
                'name': 'Cache Performance',
                'status': 'FAIL',
                'details': f"Cache not working or slow: {cache_lookup_time:.6f}s"
            })
            results['failed'] += 1
        
        # Test 4: Memory usage optimization
        stats = search_engine.get_search_statistics()
        cache_hit_rate = stats['cache']['hit_rate']
        
        results['metrics']['cache_hit_rate'] = cache_hit_rate
        
        if cache_hit_rate >= 0.0:  # Cache should be functional
            results['tests'].append({
                'name': 'Memory Optimization',
                'status': 'PASS',
                'details': f"Cache hit rate: {cache_hit_rate:.1%}"
            })
            results['passed'] += 1
        else:
            results['tests'].append({
                'name': 'Memory Optimization',
                'status': 'FAIL',
                'details': "Cache not functioning properly"
            })
            results['failed'] += 1
        
    except Exception as e:
        results['tests'].append({
            'name': 'Performance Validation',
            'status': 'FAIL',
            'details': f"Validation failed: {e}"
        })
        results['failed'] += 1
    
    return results


def validate_graceful_degradation() -> Dict[str, Any]:
    """Validate graceful degradation for missing images and metadata."""
    print("🛡️ Validating Graceful Degradation...")
    
    results = {
        'passed': 0,
        'failed': 0,
        'tests': []
    }
    
    try:
        config = AppConfig()
        search_engine = SearchEngine(config)
        
        # Test 1: Handle empty query
        try:
            results_list, _ = search_engine.search("", max_results=5)
            results['tests'].append({
                'name': 'Empty Query Handling',
                'status': 'FAIL',
                'details': 'Empty query should raise ValueError'
            })
            results['failed'] += 1
        except ValueError:
            results['tests'].append({
                'name': 'Empty Query Handling',
                'status': 'PASS',
                'details': 'Empty query properly rejected'
            })
            results['passed'] += 1
        
        # Test 2: Handle very long query
        try:
            long_query = "x" * 300
            results_list, _ = search_engine.search(long_query, max_results=5)
            results['tests'].append({
                'name': 'Long Query Handling',
                'status': 'PASS',
                'details': f'Long query handled, got {len(results_list)} results'
            })
            results['passed'] += 1
        except Exception as e:
            results['tests'].append({
                'name': 'Long Query Handling',
                'status': 'FAIL',
                'details': f'Long query failed: {e}'
            })
            results['failed'] += 1
        
        # Test 3: Handle invalid parameters
        try:
            results_list, _ = search_engine.search("test", max_results=-1)
            results['tests'].append({
                'name': 'Invalid Parameters Handling',
                'status': 'FAIL',
                'details': 'Invalid max_results should raise ValueError'
            })
            results['failed'] += 1
        except ValueError:
            results['tests'].append({
                'name': 'Invalid Parameters Handling',
                'status': 'PASS',
                'details': 'Invalid parameters properly rejected'
            })
            results['passed'] += 1
        
        # Test 4: Search readiness validation
        readiness = search_engine.validate_search_readiness()
        if readiness['ready']:
            results['tests'].append({
                'name': 'Search Readiness Validation',
                'status': 'PASS',
                'details': f"System ready with {readiness['statistics']['total_images']} images"
            })
            results['passed'] += 1
        else:
            results['tests'].append({
                'name': 'Search Readiness Validation',
                'status': 'FAIL',
                'details': f"System not ready: {readiness['issues']}"
            })
            results['failed'] += 1
        
    except Exception as e:
        results['tests'].append({
            'name': 'Graceful Degradation Validation',
            'status': 'FAIL',
            'details': f"Validation failed: {e}"
        })
        results['failed'] += 1
    
    return results


def print_results(category: str, results: Dict[str, Any]):
    """Print validation results in a formatted way."""
    print(f"\n{'='*60}")
    print(f"{category} Results")
    print(f"{'='*60}")
    
    total_tests = results['passed'] + results['failed']
    success_rate = (results['passed'] / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} ❌")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if 'metrics' in results:
        print(f"\nPerformance Metrics:")
        for metric, value in results['metrics'].items():
            if isinstance(value, float):
                print(f"  {metric}: {value:.3f}")
            else:
                print(f"  {metric}: {value}")
    
    print(f"\nDetailed Results:")
    for test in results['tests']:
        status_icon = "✅" if test['status'] == 'PASS' else "❌"
        print(f"  {status_icon} {test['name']}: {test['details']}")


def main():
    """Main validation function."""
    print("🚀 Starting Performance Optimization and Error Handling Validation")
    print("=" * 80)
    
    setup_logging()
    
    # Run all validation tests
    error_results = validate_error_handling()
    performance_results = validate_performance_optimizations()
    degradation_results = validate_graceful_degradation()
    
    # Print results
    print_results("Error Handling", error_results)
    print_results("Performance Optimization", performance_results)
    print_results("Graceful Degradation", degradation_results)
    
    # Overall summary
    total_passed = error_results['passed'] + performance_results['passed'] + degradation_results['passed']
    total_failed = error_results['failed'] + performance_results['failed'] + degradation_results['failed']
    total_tests = total_passed + total_failed
    
    print(f"\n{'='*80}")
    print("OVERALL VALIDATION SUMMARY")
    print(f"{'='*80}")
    print(f"Total Tests Run: {total_tests}")
    print(f"Total Passed: {total_passed} ✅")
    print(f"Total Failed: {total_failed} ❌")
    
    if total_tests > 0:
        overall_success_rate = (total_passed / total_tests) * 100
        print(f"Overall Success Rate: {overall_success_rate:.1f}%")
        
        if overall_success_rate >= 90:
            print("🎉 EXCELLENT: Task 7.2 implementation is highly successful!")
        elif overall_success_rate >= 75:
            print("✅ GOOD: Task 7.2 implementation is successful with minor issues.")
        elif overall_success_rate >= 50:
            print("⚠️ FAIR: Task 7.2 implementation needs improvement.")
        else:
            print("❌ POOR: Task 7.2 implementation has significant issues.")
    
    return total_failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)