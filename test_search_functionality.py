#!/usr/bin/env python3
"""
Test search functionality with the processed architectural dataset.

This script validates that the offline processing results work correctly
with the search system by running sample queries.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models.config import AppConfig
from src.processors.search_engine import SearchEngine


def test_search_queries():
    """Test various search queries against the processed dataset."""
    
    print("AI Architectural Search - Search Functionality Test")
    print("=" * 55)
    
    # Load configuration
    config = AppConfig.load_config()
    
    # Initialize search engine
    search_engine = SearchEngine(config)
    
    # Test queries covering different architectural features
    test_queries = [
        "red brick buildings",
        "glass and steel structures", 
        "stone facades",
        "mixed materials",
        "modern office buildings",
        "residential houses",
        "contemporary architecture",
        "brick facade",
        "glass curtain wall",
        "limestone buildings"
    ]
    
    print(f"Testing {len(test_queries)} search queries...\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"{i}. Query: '{query}'")
        
        try:
            # Perform search (returns tuple of results and query)
            results, query_obj = search_engine.search(query)
            
            if results:
                print(f"   Found {len(results)} results:")
                for j, result in enumerate(results[:3], 1):  # Show top 3
                    print(f"     {j}. {Path(result.image_path).name} (score: {result.confidence_score:.3f})")
                    print(f"        {result.description}")
            else:
                print("   No results found")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        print()
    
    # Test performance
    print("Performance Test:")
    print("-" * 20)
    
    import time
    
    performance_query = "brick buildings with windows"
    start_time = time.time()
    
    for _ in range(5):
        results, _ = search_engine.search(performance_query)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 5
    
    print(f"Average query time: {avg_time:.3f} seconds")
    print(f"Performance target: < 5.0 seconds")
    print(f"Performance status: {'✅ PASS' if avg_time < 5.0 else '❌ FAIL'}")
    
    # Cleanup
    search_engine.cleanup()
    
    print(f"\nSearch functionality test completed!")


if __name__ == "__main__":
    test_search_queries()