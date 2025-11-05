"""
Test Queries and Validation Dataset for AI Architectural Search System

This module defines comprehensive test queries covering different architectural features
and provides validation methods to ensure search accuracy and system reliability.

Requirements covered:
- 5.1: Successfully process predefined test queries with reasonable accuracy
- 1.2: Support queries about building materials (brick, stone, steel, glass)
- 1.3: Support queries about architectural features (roofs, windows, columns)
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from pathlib import Path
import json
from datetime import datetime


@dataclass
class TestQuery:
    """Represents a test query with expected results for validation."""
    
    query_text: str
    description: str
    expected_materials: List[str]
    expected_features: List[str]
    expected_image_categories: List[str]  # brick_buildings, glass_steel, etc.
    min_expected_results: int = 1
    max_expected_results: int = 5
    priority: str = "normal"  # "high", "normal", "low"
    
    def __post_init__(self):
        """Validate test query parameters."""
        if not self.query_text or len(self.query_text.strip()) < 2:
            raise ValueError("Query text must be at least 2 characters")
        if self.min_expected_results < 0 or self.max_expected_results < 1:
            raise ValueError("Invalid expected results range")
        if self.min_expected_results > self.max_expected_results:
            raise ValueError("Min expected results cannot exceed max")


@dataclass
class ValidationResult:
    """Results from validating a test query against actual search results."""
    
    query: TestQuery
    actual_results_count: int
    material_matches: List[str]
    feature_matches: List[str]
    category_matches: List[str]
    accuracy_score: float
    passed: bool
    issues: List[str]
    execution_time: float


class TestQueryDataset:
    """Comprehensive test dataset for architectural search validation."""
    
    def __init__(self):
        """Initialize the test dataset with predefined queries."""
        self.queries = self._create_test_queries()
        self.validation_results: List[ValidationResult] = []
    
    def _create_test_queries(self) -> List[TestQuery]:
        """Create comprehensive test queries covering all architectural features."""
        
        queries = []
        
        # Material-based queries (Requirements 1.2)
        queries.extend([
            TestQuery(
                query_text="red brick buildings",
                description="Search for buildings with red brick facades",
                expected_materials=["red brick", "brick"],
                expected_features=["facade", "residential", "traditional"],
                expected_image_categories=["brick_buildings"],
                min_expected_results=2,
                priority="high"
            ),
            
            TestQuery(
                query_text="stone facades",
                description="Find buildings with stone exterior walls",
                expected_materials=["stone", "limestone", "granite", "sandstone"],
                expected_features=["facade", "classical", "institutional"],
                expected_image_categories=["stone_facades"],
                min_expected_results=2,
                priority="high"
            ),
            
            TestQuery(
                query_text="glass and steel structures",
                description="Modern buildings with glass curtain walls and steel frames",
                expected_materials=["glass", "steel"],
                expected_features=["modern", "commercial", "curtain wall"],
                expected_image_categories=["glass_steel"],
                min_expected_results=2,
                priority="high"
            ),
            
            TestQuery(
                query_text="concrete buildings",
                description="Buildings with concrete construction",
                expected_materials=["concrete"],
                expected_features=["modern", "institutional", "industrial"],
                expected_image_categories=["mixed_materials"],
                min_expected_results=1,
                priority="normal"
            ),
        ])
        
        # Architectural feature queries (Requirements 1.3)
        queries.extend([
            TestQuery(
                query_text="buildings with large windows",
                description="Structures featuring prominent window elements",
                expected_materials=["glass"],
                expected_features=["windows", "large windows", "glazing"],
                expected_image_categories=["glass_steel", "mixed_materials"],
                min_expected_results=2,
                priority="high"
            ),
            
            TestQuery(
                query_text="flat roof buildings",
                description="Modern buildings with flat or low-slope roofs",
                expected_materials=["concrete", "steel", "glass"],
                expected_features=["flat roof", "modern", "commercial"],
                expected_image_categories=["glass_steel", "mixed_materials"],
                min_expected_results=1,
                priority="normal"
            ),
            
            TestQuery(
                query_text="classical columns",
                description="Buildings with traditional columnar architecture",
                expected_materials=["stone", "marble"],
                expected_features=["columns", "classical", "institutional"],
                expected_image_categories=["stone_facades"],
                min_expected_results=1,
                priority="normal"
            ),
            
            TestQuery(
                query_text="curved architectural elements",
                description="Buildings with curved or rounded design features",
                expected_materials=["concrete", "steel", "glass"],
                expected_features=["curved", "modern", "contemporary"],
                expected_image_categories=["mixed_materials", "glass_steel"],
                min_expected_results=1,
                priority="low"
            ),
        ])
        
        # Building type queries
        queries.extend([
            TestQuery(
                query_text="residential houses",
                description="Domestic residential architecture",
                expected_materials=["brick", "wood", "stone"],
                expected_features=["residential", "house", "domestic"],
                expected_image_categories=["brick_buildings", "mixed_materials"],
                min_expected_results=1,
                priority="normal"
            ),
            
            TestQuery(
                query_text="office towers",
                description="Commercial high-rise office buildings",
                expected_materials=["glass", "steel", "concrete"],
                expected_features=["commercial", "tower", "office", "high-rise"],
                expected_image_categories=["glass_steel"],
                min_expected_results=1,
                priority="normal"
            ),
            
            TestQuery(
                query_text="institutional buildings",
                description="Government, educational, or civic architecture",
                expected_materials=["stone", "brick", "concrete"],
                expected_features=["institutional", "civic", "government", "educational"],
                expected_image_categories=["stone_facades", "brick_buildings"],
                min_expected_results=1,
                priority="normal"
            ),
        ])
        
        # Mixed material queries
        queries.extend([
            TestQuery(
                query_text="brick and glass combination",
                description="Buildings combining traditional brick with modern glass",
                expected_materials=["brick", "glass"],
                expected_features=["mixed materials", "contemporary"],
                expected_image_categories=["mixed_materials"],
                min_expected_results=1,
                priority="normal"
            ),
            
            TestQuery(
                query_text="wood and steel architecture",
                description="Contemporary buildings mixing wood and steel elements",
                expected_materials=["wood", "steel"],
                expected_features=["mixed materials", "contemporary", "sustainable"],
                expected_image_categories=["mixed_materials"],
                min_expected_results=1,
                priority="low"
            ),
        ])
        
        # Complex descriptive queries
        queries.extend([
            TestQuery(
                query_text="modern museum with glass facade",
                description="Contemporary cultural buildings with transparent exteriors",
                expected_materials=["glass", "steel", "concrete"],
                expected_features=["modern", "museum", "cultural", "transparent"],
                expected_image_categories=["glass_steel", "mixed_materials"],
                min_expected_results=1,
                priority="high"
            ),
            
            TestQuery(
                query_text="historic brick church",
                description="Traditional religious architecture in brick construction",
                expected_materials=["brick", "stone"],
                expected_features=["historic", "religious", "traditional", "church"],
                expected_image_categories=["brick_buildings", "stone_facades"],
                min_expected_results=1,
                priority="normal"
            ),
        ])
        
        return queries
    
    def get_queries_by_priority(self, priority: str) -> List[TestQuery]:
        """Get test queries filtered by priority level."""
        return [q for q in self.queries if q.priority == priority]
    
    def get_material_queries(self) -> List[TestQuery]:
        """Get queries focused on building materials."""
        material_keywords = ["brick", "stone", "glass", "steel", "concrete", "wood"]
        return [q for q in self.queries 
                if any(material in q.query_text.lower() for material in material_keywords)]
    
    def get_feature_queries(self) -> List[TestQuery]:
        """Get queries focused on architectural features."""
        feature_keywords = ["windows", "roof", "columns", "curved", "facade"]
        return [q for q in self.queries 
                if any(feature in q.query_text.lower() for feature in feature_keywords)]
    
    def get_demo_queries(self) -> List[TestQuery]:
        """Get the most suitable queries for client demonstrations."""
        # High priority queries that showcase system capabilities
        demo_queries = self.get_queries_by_priority("high")
        
        # Add some representative normal priority queries
        normal_queries = self.get_queries_by_priority("normal")
        demo_queries.extend(normal_queries[:3])
        
        return demo_queries
    
    def validate_query_coverage(self) -> Dict[str, any]:
        """Validate that test queries provide comprehensive coverage."""
        
        coverage_report = {
            "total_queries": len(self.queries),
            "material_coverage": {},
            "feature_coverage": {},
            "category_coverage": {},
            "priority_distribution": {},
            "coverage_gaps": []
        }
        
        # Analyze material coverage
        all_materials = set()
        for query in self.queries:
            all_materials.update(query.expected_materials)
        
        required_materials = {"brick", "stone", "glass", "steel", "concrete"}
        coverage_report["material_coverage"] = {
            "covered": list(all_materials),
            "required": list(required_materials),
            "missing": list(required_materials - all_materials)
        }
        
        # Analyze feature coverage
        all_features = set()
        for query in self.queries:
            all_features.update(query.expected_features)
        
        required_features = {"windows", "roof", "columns", "facade", "modern", "traditional"}
        coverage_report["feature_coverage"] = {
            "covered": list(all_features),
            "required": list(required_features),
            "missing": list(required_features - all_features)
        }
        
        # Analyze category coverage
        all_categories = set()
        for query in self.queries:
            all_categories.update(query.expected_image_categories)
        
        required_categories = {"brick_buildings", "glass_steel", "stone_facades", "mixed_materials"}
        coverage_report["category_coverage"] = {
            "covered": list(all_categories),
            "required": list(required_categories),
            "missing": list(required_categories - all_categories)
        }
        
        # Priority distribution
        for priority in ["high", "normal", "low"]:
            coverage_report["priority_distribution"][priority] = len(
                self.get_queries_by_priority(priority)
            )
        
        # Identify coverage gaps
        if coverage_report["material_coverage"]["missing"]:
            coverage_report["coverage_gaps"].append(
                f"Missing material coverage: {coverage_report['material_coverage']['missing']}"
            )
        
        if coverage_report["feature_coverage"]["missing"]:
            coverage_report["coverage_gaps"].append(
                f"Missing feature coverage: {coverage_report['feature_coverage']['missing']}"
            )
        
        if coverage_report["category_coverage"]["missing"]:
            coverage_report["coverage_gaps"].append(
                f"Missing category coverage: {coverage_report['category_coverage']['missing']}"
            )
        
        return coverage_report
    
    def export_queries_for_demo(self, output_path: str = "demo_queries.json") -> None:
        """Export demo-ready queries to JSON file for presentation use."""
        
        demo_queries = self.get_demo_queries()
        
        export_data = {
            "metadata": {
                "created": datetime.now().isoformat(),
                "total_queries": len(demo_queries),
                "description": "Curated test queries for AI architectural search demo"
            },
            "queries": []
        }
        
        for i, query in enumerate(demo_queries, 1):
            export_data["queries"].append({
                "id": i,
                "text": query.query_text,
                "description": query.description,
                "expected_materials": query.expected_materials,
                "expected_features": query.expected_features,
                "priority": query.priority,
                "demo_notes": f"Expected {query.min_expected_results}-{query.max_expected_results} results"
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"Demo queries exported to {output_path}")
        print(f"Total queries: {len(demo_queries)}")
        print(f"High priority: {len([q for q in demo_queries if q.priority == 'high'])}")
        print(f"Normal priority: {len([q for q in demo_queries if q.priority == 'normal'])}")


class QueryValidator:
    """Validates search results against expected outcomes for test queries."""
    
    def __init__(self, image_categories: Dict[str, List[str]] = None):
        """Initialize validator with image category mappings."""
        self.image_categories = image_categories or self._get_default_categories()
    
    def _get_default_categories(self) -> Dict[str, List[str]]:
        """Get default image category mappings based on directory structure."""
        return {
            "brick_buildings": [
                "brick_apartment_07.jpg", "brick_library_09.jpg", "brick_warehouse_05.jpg",
                "brown_brick_office_02.jpg", "colonial_brick_house_10.jpg", 
                "historic_brick_church_03.jpg", "modern_brick_facade_04.jpg",
                "old_brick_factory_08.jpg", "red_brick_house_01.jpg", "red_brick_school_06.jpg"
            ],
            "glass_steel": [
                "contemporary_glass_house_04.jpg", "corporate_headquarters_08.jpg",
                "glass_curtain_wall_02.jpg", "glass_residential_tower_09.jpg",
                "modern_glass_library_10.jpg", "modern_glass_museum_06.jpg",
                "modern_office_tower_01.jpg", "skyscraper_glass_facade_05.jpg",
                "steel_frame_building_03.jpg", "steel_glass_mall_07.jpg"
            ],
            "stone_facades": [
                "granite_bank_building_02.jpg", "granite_memorial_07.jpg",
                "limestone_courthouse_01.jpg", "limestone_hotel_10.jpg",
                "limestone_mansion_06.jpg", "marble_government_04.jpg",
                "sandstone_castle_08.jpg", "sandstone_university_03.jpg",
                "stone_bridge_09.jpg", "stone_cathedral_05.jpg"
            ],
            "mixed_materials": [
                "brick_glass_office_03.jpg", "brick_steel_loft_08.jpg",
                "concrete_glass_museum_01.jpg", "concrete_steel_stadium_04.jpg",
                "concrete_wood_school_09.jpg", "contemporary_mixed_house_12.jpg",
                "eco_mixed_building_15.jpg", "glass_stone_church_10.jpg",
                "industrial_mixed_complex_13.jpg", "metal_concrete_factory_06.jpg",
                "mixed_material_mall_11.jpg", "modern_mixed_apartment_14.jpg",
                "stone_glass_hotel_07.jpg", "wood_glass_pavilion_05.jpg",
                "wood_steel_residence_02.jpg"
            ]
        }
    
    def validate_query_results(self, query: TestQuery, search_results: List[Dict]) -> ValidationResult:
        """Validate search results against expected outcomes for a test query."""
        
        start_time = datetime.now()
        
        # Extract result information
        result_paths = [result.get('image_path', '') for result in search_results]
        result_descriptions = [result.get('description', '') for result in search_results]
        result_features = []
        for result in search_results:
            result_features.extend(result.get('features', []))
        
        # Validate result count
        actual_count = len(search_results)
        count_valid = query.min_expected_results <= actual_count <= query.max_expected_results
        
        # Check material matches
        material_matches = []
        for material in query.expected_materials:
            if any(material.lower() in desc.lower() for desc in result_descriptions) or \
               any(material.lower() in feature.lower() for feature in result_features):
                material_matches.append(material)
        
        # Check feature matches
        feature_matches = []
        for feature in query.expected_features:
            if any(feature.lower() in desc.lower() for desc in result_descriptions) or \
               any(feature.lower() in feat.lower() for feat in result_features):
                feature_matches.append(feature)
        
        # Check category matches
        category_matches = []
        for category in query.expected_image_categories:
            category_images = self.image_categories.get(category, [])
            if any(any(cat_img in path for cat_img in category_images) for path in result_paths):
                category_matches.append(category)
        
        # Calculate accuracy score
        material_score = len(material_matches) / max(len(query.expected_materials), 1)
        feature_score = len(feature_matches) / max(len(query.expected_features), 1)
        category_score = len(category_matches) / max(len(query.expected_image_categories), 1)
        count_score = 1.0 if count_valid else 0.5
        
        accuracy_score = (material_score + feature_score + category_score + count_score) / 4
        
        # Determine if query passed
        passed = (
            count_valid and
            len(material_matches) > 0 and
            len(category_matches) > 0 and
            accuracy_score >= 0.6
        )
        
        # Identify issues
        issues = []
        if not count_valid:
            issues.append(f"Result count {actual_count} outside expected range {query.min_expected_results}-{query.max_expected_results}")
        if len(material_matches) == 0:
            issues.append(f"No expected materials found: {query.expected_materials}")
        if len(category_matches) == 0:
            issues.append(f"No expected categories matched: {query.expected_image_categories}")
        if accuracy_score < 0.6:
            issues.append(f"Low accuracy score: {accuracy_score:.2f}")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return ValidationResult(
            query=query,
            actual_results_count=actual_count,
            material_matches=material_matches,
            feature_matches=feature_matches,
            category_matches=category_matches,
            accuracy_score=accuracy_score,
            passed=passed,
            issues=issues,
            execution_time=execution_time
        )
    
    def generate_validation_report(self, validation_results: List[ValidationResult]) -> Dict[str, any]:
        """Generate comprehensive validation report from test results."""
        
        total_queries = len(validation_results)
        passed_queries = len([r for r in validation_results if r.passed])
        
        report = {
            "summary": {
                "total_queries": total_queries,
                "passed_queries": passed_queries,
                "failed_queries": total_queries - passed_queries,
                "pass_rate": passed_queries / total_queries if total_queries > 0 else 0,
                "avg_accuracy": sum(r.accuracy_score for r in validation_results) / total_queries if total_queries > 0 else 0,
                "avg_execution_time": sum(r.execution_time for r in validation_results) / total_queries if total_queries > 0 else 0
            },
            "by_priority": {},
            "by_category": {},
            "failed_queries": [],
            "recommendations": []
        }
        
        # Analyze by priority
        for priority in ["high", "normal", "low"]:
            priority_results = [r for r in validation_results if r.query.priority == priority]
            if priority_results:
                passed = len([r for r in priority_results if r.passed])
                report["by_priority"][priority] = {
                    "total": len(priority_results),
                    "passed": passed,
                    "pass_rate": passed / len(priority_results)
                }
        
        # Analyze by category
        all_categories = set()
        for result in validation_results:
            all_categories.update(result.query.expected_image_categories)
        
        for category in all_categories:
            category_results = [r for r in validation_results 
                             if category in r.query.expected_image_categories]
            if category_results:
                passed = len([r for r in category_results if r.passed])
                report["by_category"][category] = {
                    "total": len(category_results),
                    "passed": passed,
                    "pass_rate": passed / len(category_results)
                }
        
        # Document failed queries
        for result in validation_results:
            if not result.passed:
                report["failed_queries"].append({
                    "query": result.query.query_text,
                    "accuracy": result.accuracy_score,
                    "issues": result.issues
                })
        
        # Generate recommendations
        if report["summary"]["pass_rate"] < 0.8:
            report["recommendations"].append("Overall pass rate is below 80% - consider improving search algorithm")
        
        if report["by_priority"].get("high", {}).get("pass_rate", 1) < 0.9:
            report["recommendations"].append("High priority queries failing - critical for demo success")
        
        if report["summary"]["avg_execution_time"] > 5.0:
            report["recommendations"].append("Average execution time exceeds 5 seconds - optimize performance")
        
        return report


def main():
    """Main function to demonstrate test query dataset functionality."""
    
    # Create test dataset
    dataset = TestQueryDataset()
    
    print("AI Architectural Search - Test Query Dataset")
    print("=" * 50)
    print(f"Total test queries: {len(dataset.queries)}")
    
    # Show coverage analysis
    coverage = dataset.validate_query_coverage()
    print(f"\nCoverage Analysis:")
    print(f"Materials covered: {len(coverage['material_coverage']['covered'])}")
    print(f"Features covered: {len(coverage['feature_coverage']['covered'])}")
    print(f"Categories covered: {len(coverage['category_coverage']['covered'])}")
    
    if coverage['coverage_gaps']:
        print(f"\nCoverage gaps found:")
        for gap in coverage['coverage_gaps']:
            print(f"  - {gap}")
    else:
        print(f"\n✓ Complete coverage achieved")
    
    # Show priority distribution
    print(f"\nPriority Distribution:")
    for priority, count in coverage['priority_distribution'].items():
        print(f"  {priority.capitalize()}: {count} queries")
    
    # Export demo queries
    dataset.export_queries_for_demo()
    
    # Show sample queries
    print(f"\nSample Demo Queries:")
    demo_queries = dataset.get_demo_queries()[:5]
    for i, query in enumerate(demo_queries, 1):
        print(f"  {i}. \"{query.query_text}\" ({query.priority} priority)")
        print(f"     Expected: {', '.join(query.expected_materials[:2])} materials")


if __name__ == "__main__":
    main()