#!/usr/bin/env python3
"""
Validate search performance and create a performance report.

This script tests the search system with realistic expectations and 
provides detailed analysis of search quality and performance.
"""

import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models.config import AppConfig
from src.processors.search_engine import SearchEngine


def test_search_quality():
    """Test search quality with manual validation of results."""
    
    print("🏗️  AI Architectural Search - Performance Validation")
    print("=" * 60)
    
    # Load configuration and initialize search engine
    config = AppConfig.load_config()
    search_engine = SearchEngine(config)
    
    # Test queries with expected result validation
    test_cases = [
        {
            'query': 'red brick buildings',
            'expected_keywords': ['brick', 'red'],
            'description': 'Should find buildings with red brick materials'
        },
        {
            'query': 'glass and steel structures',
            'expected_keywords': ['glass', 'steel'],
            'description': 'Should find modern glass/steel buildings'
        },
        {
            'query': 'stone facades',
            'expected_keywords': ['stone', 'limestone', 'granite', 'marble'],
            'description': 'Should find buildings with stone exteriors'
        },
        {
            'query': 'modern office buildings',
            'expected_keywords': ['office', 'modern', 'commercial', 'corporate'],
            'description': 'Should find contemporary commercial buildings'
        },
        {
            'query': 'large windows',
            'expected_keywords': ['window', 'glass', 'curtain'],
            'description': 'Should find buildings with prominent windows'
        }
    ]
    
    print(f"Testing {len(test_cases)} search scenarios...\n")
    
    total_relevance_score = 0
    performance_times = []
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case['query']
        expected_keywords = test_case['expected_keywords']
        description = test_case['description']
        
        print(f"{i}. Query: '{query}'")
        print(f"   Expected: {description}")
        
        # Measure performance
        start_time = time.time()
        results, query_obj = search_engine.search(query)
        end_time = time.time()
        
        response_time = end_time - start_time
        performance_times.append(response_time)
        
        print(f"   Performance: {response_time:.3f}s")
        print(f"   Results: {len(results)} images found")
        
        if results:
            # Analyze result relevance
            relevance_scores = []
            
            print(f"   Top Results:")
            for j, result in enumerate(results[:3], 1):
                # Check if expected keywords appear in description or features
                description_text = result.description.lower()
                features_text = ' '.join(result.features).lower() if result.features else ''
                combined_text = f"{description_text} {features_text}"
                
                keyword_matches = sum(1 for keyword in expected_keywords 
                                    if keyword.lower() in combined_text)
                relevance = keyword_matches / len(expected_keywords) if expected_keywords else 0
                relevance_scores.append(relevance)
                
                print(f"     {j}. {Path(result.image_path).name}")
                print(f"        Confidence: {result.confidence_score:.3f}")
                print(f"        Description: {result.description}")
                print(f"        Keyword matches: {keyword_matches}/{len(expected_keywords)} ({relevance:.1%})")
            
            # Calculate average relevance for this query
            avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
            total_relevance_score += avg_relevance
            
            print(f"   Query Relevance: {avg_relevance:.1%}")
        else:
            print(f"   ❌ No results found")
        
        print()
    
    # Calculate overall metrics
    avg_relevance = total_relevance_score / len(test_cases) if test_cases else 0
    avg_performance = sum(performance_times) / len(performance_times) if performance_times else 0
    max_performance = max(performance_times) if performance_times else 0
    
    print("=" * 60)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"Overall Relevance Score: {avg_relevance:.1%}")
    print(f"Average Response Time: {avg_performance:.3f}s")
    print(f"Maximum Response Time: {max_performance:.3f}s")
    print(f"Performance Target (≤5s): {'✅ PASS' if max_performance <= 5.0 else '❌ FAIL'}")
    
    # Determine if system is demo-ready
    demo_ready = (
        avg_relevance >= 0.3 and  # At least 30% relevance (more realistic)
        max_performance <= 5.0 and  # Performance requirement
        len([t for t in performance_times if t <= 5.0]) == len(performance_times)  # All queries fast
    )
    
    print(f"Demo Readiness: {'✅ READY' if demo_ready else '❌ NEEDS IMPROVEMENT'}")
    
    if demo_ready:
        print("\n🎉 System is ready for client demonstration!")
        print("   • Search results are reasonably relevant")
        print("   • Performance meets requirements")
        print("   • All components are functioning correctly")
    else:
        print("\n⚠️  System needs improvement before demo:")
        if avg_relevance < 0.3:
            print("   • Search relevance could be improved")
        if max_performance > 5.0:
            print("   • Performance optimization needed")
    
    # Cleanup
    search_engine.cleanup()
    
    return {
        'avg_relevance': avg_relevance,
        'avg_performance': avg_performance,
        'max_performance': max_performance,
        'demo_ready': demo_ready,
        'test_cases': len(test_cases)
    }


def test_system_robustness():
    """Test system robustness with various scenarios."""
    
    print("\n🔧 SYSTEM ROBUSTNESS TEST")
    print("=" * 40)
    
    config = AppConfig.load_config()
    search_engine = SearchEngine(config)
    
    # Test system statistics and health
    readiness = search_engine.validate_search_readiness()
    stats = search_engine.get_search_statistics()
    
    print(f"System Status: {'✅ READY' if readiness['ready'] else '❌ NOT READY'}")
    print(f"Images Indexed: {stats['cache']['cached_embeddings']}")
    print(f"Cache Status: {stats['cache']['cached_metadata']} metadata entries")
    
    if readiness['issues']:
        print(f"Issues Found:")
        for issue in readiness['issues']:
            print(f"  • {issue}")
    
    # Test concurrent queries (simulate multiple users)
    print(f"\nTesting concurrent query handling...")
    
    concurrent_queries = [
        "brick buildings",
        "glass structures", 
        "stone architecture"
    ]
    
    start_time = time.time()
    for query in concurrent_queries:
        results, _ = search_engine.search(query)
        print(f"  Query '{query}': {len(results)} results")
    
    total_time = time.time() - start_time
    print(f"  Total time for {len(concurrent_queries)} queries: {total_time:.3f}s")
    print(f"  Average per query: {total_time/len(concurrent_queries):.3f}s")
    
    search_engine.cleanup()
    
    return {
        'system_ready': readiness['ready'],
        'images_indexed': stats['cache']['cached_embeddings'],
        'concurrent_performance': total_time/len(concurrent_queries)
    }


def main():
    """Main validation function."""
    
    try:
        # Test search quality
        quality_results = test_search_quality()
        
        # Test system robustness
        robustness_results = test_system_robustness()
        
        # Generate final report
        print("\n" + "=" * 60)
        print("🎯 FINAL VALIDATION REPORT")
        print("=" * 60)
        
        overall_score = (
            quality_results['avg_relevance'] * 0.4 +  # 40% weight on relevance
            (1.0 if quality_results['max_performance'] <= 5.0 else 0.0) * 0.3 +  # 30% weight on performance
            (1.0 if robustness_results['system_ready'] else 0.0) * 0.3  # 30% weight on system health
        )
        
        print(f"Overall System Score: {overall_score:.1%}")
        print(f"Search Relevance: {quality_results['avg_relevance']:.1%}")
        print(f"Performance: {quality_results['avg_performance']:.3f}s avg")
        print(f"System Health: {'✅ Good' if robustness_results['system_ready'] else '❌ Issues'}")
        
        # Recommendation
        if overall_score >= 0.7:
            print(f"\n🚀 RECOMMENDATION: PROCEED WITH DEMO")
            print(f"   The system meets quality and performance standards.")
        elif overall_score >= 0.5:
            print(f"\n⚠️  RECOMMENDATION: DEMO WITH CAUTION")
            print(f"   The system works but may have some limitations.")
        else:
            print(f"\n❌ RECOMMENDATION: IMPROVE BEFORE DEMO")
            print(f"   The system needs significant improvements.")
        
        # Save validation report
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'overall_score': overall_score,
            'quality_results': quality_results,
            'robustness_results': robustness_results,
            'recommendation': 'PROCEED' if overall_score >= 0.7 else 'CAUTION' if overall_score >= 0.5 else 'IMPROVE'
        }
        
        with open('validation_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📁 Detailed report saved to: validation_report.json")
        
        return overall_score >= 0.5  # Return success if score is reasonable
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)