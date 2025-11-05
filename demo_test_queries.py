#!/usr/bin/env python3
"""
Demo script to showcase the test queries and validation dataset.

This script demonstrates the test query functionality without requiring
the full search system to be operational.
"""

import json
from test_queries_validation import TestQueryDataset, QueryValidator


def display_query_categories():
    """Display test queries organized by category."""
    
    dataset = TestQueryDataset()
    
    print("🏗️  AI Architectural Search - Test Query Categories")
    print("=" * 60)
    
    # Material queries
    material_queries = dataset.get_material_queries()
    print(f"\n🧱 Material-Based Queries ({len(material_queries)} queries):")
    for query in material_queries:
        priority_icon = "🔥" if query.priority == "high" else "📋" if query.priority == "normal" else "📝"
        print(f"  {priority_icon} \"{query.query_text}\"")
        print(f"     Expected materials: {', '.join(query.expected_materials[:3])}")
        print(f"     Expected results: {query.min_expected_results}-{query.max_expected_results}")
    
    # Feature queries
    feature_queries = dataset.get_feature_queries()
    print(f"\n🏛️  Architectural Feature Queries ({len(feature_queries)} queries):")
    for query in feature_queries:
        priority_icon = "🔥" if query.priority == "high" else "📋" if query.priority == "normal" else "📝"
        print(f"  {priority_icon} \"{query.query_text}\"")
        print(f"     Expected features: {', '.join(query.expected_features[:3])}")
        print(f"     Expected results: {query.min_expected_results}-{query.max_expected_results}")
    
    # Demo queries
    demo_queries = dataset.get_demo_queries()
    print(f"\n🎯 Demo Presentation Queries ({len(demo_queries)} queries):")
    for i, query in enumerate(demo_queries, 1):
        priority_icon = "🔥" if query.priority == "high" else "📋"
        print(f"  {i:2d}. {priority_icon} \"{query.query_text}\"")
        print(f"      {query.description}")


def show_coverage_analysis():
    """Display coverage analysis for the test dataset."""
    
    dataset = TestQueryDataset()
    coverage = dataset.validate_query_coverage()
    
    print("\n📊 Test Coverage Analysis")
    print("=" * 40)
    
    # Material coverage
    materials = coverage['material_coverage']
    print(f"\n🧱 Material Coverage:")
    print(f"   Covered: {len(materials['covered'])} materials")
    print(f"   Required: {len(materials['required'])} materials")
    if materials['missing']:
        print(f"   Missing: {', '.join(materials['missing'])}")
    else:
        print(f"   ✅ Complete material coverage")
    
    # Feature coverage
    features = coverage['feature_coverage']
    print(f"\n🏛️  Feature Coverage:")
    print(f"   Covered: {len(features['covered'])} features")
    print(f"   Required: {len(features['required'])} features")
    if features['missing']:
        print(f"   Missing: {', '.join(features['missing'])}")
    else:
        print(f"   ✅ Complete feature coverage")
    
    # Category coverage
    categories = coverage['category_coverage']
    print(f"\n📁 Image Category Coverage:")
    print(f"   Covered: {len(categories['covered'])} categories")
    print(f"   Required: {len(categories['required'])} categories")
    if categories['missing']:
        print(f"   Missing: {', '.join(categories['missing'])}")
    else:
        print(f"   ✅ Complete category coverage")
    
    # Priority distribution
    print(f"\n⭐ Priority Distribution:")
    for priority, count in coverage['priority_distribution'].items():
        print(f"   {priority.capitalize()}: {count} queries")
    
    # Coverage gaps
    if coverage['coverage_gaps']:
        print(f"\n⚠️  Coverage Gaps:")
        for gap in coverage['coverage_gaps']:
            print(f"   • {gap}")
    else:
        print(f"\n✅ No coverage gaps found")


def demonstrate_validation_logic():
    """Demonstrate the validation logic with mock results."""
    
    print("\n🧪 Validation Logic Demonstration")
    print("=" * 40)
    
    dataset = TestQueryDataset()
    validator = QueryValidator()
    
    # Get a sample query
    sample_query = dataset.get_demo_queries()[0]  # "red brick buildings"
    
    print(f"\nSample Query: \"{sample_query.query_text}\"")
    print(f"Expected materials: {sample_query.expected_materials}")
    print(f"Expected features: {sample_query.expected_features}")
    print(f"Expected categories: {sample_query.expected_image_categories}")
    
    # Create mock search results
    mock_results = [
        {
            'image_path': 'images/brick_buildings/red_brick_house_01.jpg',
            'description': 'Traditional red brick residential house with white window frames',
            'features': ['red brick', 'residential', 'traditional', 'windows'],
            'confidence_score': 0.85,
            'similarity_score': 0.78
        },
        {
            'image_path': 'images/brick_buildings/brick_apartment_07.jpg', 
            'description': 'Modern brown brick apartment building with large windows',
            'features': ['brown brick', 'brick facade', 'residential', 'modern'],
            'confidence_score': 0.72,
            'similarity_score': 0.65
        },
        {
            'image_path': 'images/mixed_materials/brick_glass_office_03.jpg',
            'description': 'Contemporary office building combining brick and glass elements',
            'features': ['brick', 'glass', 'mixed materials', 'commercial'],
            'confidence_score': 0.68,
            'similarity_score': 0.61
        }
    ]
    
    print(f"\nMock Search Results ({len(mock_results)} results):")
    for i, result in enumerate(mock_results, 1):
        print(f"  {i}. {result['image_path']}")
        print(f"     Description: {result['description']}")
        print(f"     Confidence: {result['confidence_score']:.2f}")
    
    # Validate results
    validation = validator.validate_query_results(sample_query, mock_results)
    
    print(f"\n📋 Validation Results:")
    print(f"   Result count: {validation.actual_results_count} (expected {sample_query.min_expected_results}-{sample_query.max_expected_results})")
    print(f"   Material matches: {validation.material_matches}")
    print(f"   Feature matches: {validation.feature_matches[:5]}...")  # Show first 5
    print(f"   Category matches: {validation.category_matches}")
    print(f"   Accuracy score: {validation.accuracy_score:.2f}")
    print(f"   Passed: {'✅ YES' if validation.passed else '❌ NO'}")
    
    if validation.issues:
        print(f"   Issues: {', '.join(validation.issues)}")


def show_demo_preparation_guide():
    """Show guidance for demo preparation."""
    
    print("\n🎯 Demo Preparation Guide")
    print("=" * 30)
    
    dataset = TestQueryDataset()
    demo_queries = dataset.get_demo_queries()
    
    print(f"\n📝 Recommended Demo Flow:")
    print(f"   1. Start with high-priority material queries")
    print(f"   2. Demonstrate feature recognition capabilities") 
    print(f"   3. Show complex natural language understanding")
    print(f"   4. Highlight system performance and accuracy")
    
    print(f"\n🔥 Critical Demo Queries (Must Work Perfectly):")
    high_priority = [q for q in demo_queries if q.priority == "high"]
    for i, query in enumerate(high_priority, 1):
        print(f"   {i}. \"{query.query_text}\"")
        print(f"      Why critical: {query.description}")
    
    print(f"\n📋 Supporting Demo Queries:")
    normal_priority = [q for q in demo_queries if q.priority == "normal"]
    for i, query in enumerate(normal_priority, 1):
        print(f"   {i}. \"{query.query_text}\"")
    
    print(f"\n⚠️  Demo Success Criteria:")
    print(f"   • All high-priority queries must pass (≥90% accuracy)")
    print(f"   • Query response time must be ≤5 seconds")
    print(f"   • Results must be visually relevant and diverse")
    print(f"   • System must handle edge cases gracefully")
    
    print(f"\n🛠️  Pre-Demo Checklist:")
    print(f"   □ Run full validation suite")
    print(f"   □ Verify all images are accessible")
    print(f"   □ Test system performance under load")
    print(f"   □ Prepare backup queries for different scenarios")
    print(f"   □ Have troubleshooting steps ready")


def main():
    """Main demo function."""
    
    # Display query categories
    display_query_categories()
    
    # Show coverage analysis
    show_coverage_analysis()
    
    # Demonstrate validation logic
    demonstrate_validation_logic()
    
    # Show demo preparation guide
    show_demo_preparation_guide()
    
    print(f"\n✅ Test query dataset demonstration complete!")
    print(f"   📁 Files created:")
    print(f"   • test_queries_validation.py - Main dataset and validation classes")
    print(f"   • demo_queries.json - Curated queries for presentation")
    print(f"   • TEST_QUERIES_DOCUMENTATION.md - Comprehensive documentation")
    print(f"   • validate_test_queries.py - Integration validation script")


if __name__ == "__main__":
    main()