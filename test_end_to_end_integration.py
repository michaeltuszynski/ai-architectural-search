#!/usr/bin/env python3
"""
End-to-end integration test for AI Architectural Search System.

This script tests the complete workflow from query input to search results,
verifying that all components work together correctly and meet performance requirements.
"""

import sys
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models.config import AppConfig
from src.processors.search_engine import SearchEngine
from src.storage.metadata_store import MetadataStore
from src.processors.model_manager import ModelManager


class EndToEndIntegrationTest:
    """
    Comprehensive end-to-end integration test for the AI Architectural Search System.
    
    Tests:
    - Component initialization and integration
    - Complete search workflow
    - Performance requirements
    - Error handling and edge cases
    - System readiness validation
    """
    
    def __init__(self):
        """Initialize the integration test."""
        self.logger = logging.getLogger(__name__)
        self.config = None
        self.search_engine = None
        self.test_results = {
            'component_tests': {},
            'search_tests': {},
            'performance_tests': {},
            'edge_case_tests': {},
            'overall_status': 'PENDING'
        }
        
        # Test queries for comprehensive validation
        self.test_queries = [
            # Material-based queries
            "red brick buildings",
            "glass and steel structures",
            "stone facades",
            "mixed materials",
            
            # Feature-based queries
            "flat roof structures",
            "large windows",
            "columns and arches",
            "curved architecture",
            
            # Style-based queries
            "modern office buildings",
            "traditional residential",
            "industrial architecture",
            "contemporary design",
            
            # Complex queries
            "red brick residential buildings with large windows",
            "modern glass office towers",
            "stone buildings with classical columns"
        ]
        
        # Performance requirements from specifications
        self.performance_requirements = {
            'max_query_time': 5.0,  # seconds
            'min_accuracy_rate': 0.7,  # 70% accuracy
            'min_results_per_query': 1,
            'max_results_per_query': 10
        }
    
    def setup_test_environment(self) -> bool:
        """
        Set up the test environment and validate prerequisites.
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            self.logger.info("Setting up end-to-end integration test environment...")
            
            # Load configuration
            self.config = AppConfig.load_config()
            
            # Verify image directory exists and has images
            image_dir = Path(self.config.image_directory)
            if not image_dir.exists():
                self.logger.error(f"Image directory not found: {image_dir}")
                return False
            
            # Count images
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
            image_count = 0
            for ext in image_extensions:
                image_count += len(list(image_dir.rglob(f"*{ext}")))
                image_count += len(list(image_dir.rglob(f"*{ext.upper()}")))
            
            if image_count == 0:
                self.logger.error("No images found in image directory")
                return False
            
            self.logger.info(f"Found {image_count} images for testing")
            
            # Verify metadata file exists
            metadata_file = Path(self.config.metadata_file)
            if not metadata_file.exists():
                self.logger.error(f"Metadata file not found: {metadata_file}")
                return False
            
            self.logger.info("Test environment setup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup test environment: {e}")
            return False
    
    def test_component_initialization(self) -> Dict[str, Any]:
        """
        Test initialization of all system components.
        
        Returns:
            dict: Component initialization test results
        """
        results = {
            'config_loading': False,
            'model_manager': False,
            'metadata_store': False,
            'search_engine': False,
            'issues': []
        }
        
        try:
            self.logger.info("Testing component initialization...")
            
            # Test configuration loading
            try:
                config = AppConfig.load_config()
                results['config_loading'] = True
                self.logger.info("✅ Configuration loading successful")
            except Exception as e:
                results['issues'].append(f"Config loading failed: {e}")
                self.logger.error(f"❌ Configuration loading failed: {e}")
            
            # Test model manager initialization
            try:
                model_manager = ModelManager(self.config)
                model_info = model_manager.get_model_info()
                if model_info.get('status') == 'loaded':
                    results['model_manager'] = True
                    self.logger.info("✅ Model manager initialization successful")
                else:
                    results['issues'].append("Model manager not properly loaded")
                    self.logger.error("❌ Model manager initialization failed")
            except Exception as e:
                results['issues'].append(f"Model manager failed: {e}")
                self.logger.error(f"❌ Model manager initialization failed: {e}")
            
            # Test metadata store initialization
            try:
                metadata_store = MetadataStore(self.config)
                stats = metadata_store.get_storage_stats()
                if stats['total_images'] > 0:
                    results['metadata_store'] = True
                    self.logger.info(f"✅ Metadata store initialization successful ({stats['total_images']} images)")
                else:
                    results['issues'].append("No images in metadata store")
                    self.logger.error("❌ Metadata store has no images")
            except Exception as e:
                results['issues'].append(f"Metadata store failed: {e}")
                self.logger.error(f"❌ Metadata store initialization failed: {e}")
            
            # Test search engine initialization
            try:
                self.search_engine = SearchEngine(self.config)
                readiness = self.search_engine.validate_search_readiness()
                if readiness['ready']:
                    results['search_engine'] = True
                    self.logger.info("✅ Search engine initialization successful")
                else:
                    results['issues'].extend(readiness['issues'])
                    self.logger.error(f"❌ Search engine not ready: {readiness['issues']}")
            except Exception as e:
                results['issues'].append(f"Search engine failed: {e}")
                self.logger.error(f"❌ Search engine initialization failed: {e}")
            
        except Exception as e:
            results['issues'].append(f"Component initialization test failed: {e}")
            self.logger.error(f"Component initialization test failed: {e}")
        
        return results
    
    def test_search_functionality(self) -> Dict[str, Any]:
        """
        Test search functionality with various queries.
        
        Returns:
            dict: Search functionality test results
        """
        results = {
            'successful_queries': 0,
            'failed_queries': 0,
            'query_results': {},
            'accuracy_scores': [],
            'issues': []
        }
        
        if not self.search_engine:
            results['issues'].append("Search engine not initialized")
            return results
        
        try:
            self.logger.info(f"Testing search functionality with {len(self.test_queries)} queries...")
            
            for query_text in self.test_queries:
                try:
                    self.logger.info(f"Testing query: '{query_text}'")
                    
                    # Perform search
                    search_results, query_obj = self.search_engine.search(query_text)
                    
                    # Validate results
                    if search_results:
                        results['successful_queries'] += 1
                        
                        # Calculate basic accuracy score based on result relevance
                        accuracy_score = self._calculate_query_accuracy(query_text, search_results)
                        results['accuracy_scores'].append(accuracy_score)
                        
                        # Store detailed results
                        results['query_results'][query_text] = {
                            'result_count': len(search_results),
                            'accuracy_score': accuracy_score,
                            'top_result': {
                                'path': search_results[0].image_path,
                                'confidence': search_results[0].confidence_score,
                                'description': search_results[0].description
                            } if search_results else None
                        }
                        
                        self.logger.info(f"  ✅ Found {len(search_results)} results (accuracy: {accuracy_score:.2f})")
                    else:
                        results['failed_queries'] += 1
                        results['issues'].append(f"No results for query: '{query_text}'")
                        self.logger.warning(f"  ❌ No results found for query: '{query_text}'")
                
                except Exception as e:
                    results['failed_queries'] += 1
                    results['issues'].append(f"Query '{query_text}' failed: {e}")
                    self.logger.error(f"  ❌ Query failed: {e}")
            
            # Calculate overall accuracy
            if results['accuracy_scores']:
                overall_accuracy = sum(results['accuracy_scores']) / len(results['accuracy_scores'])
                results['overall_accuracy'] = overall_accuracy
                self.logger.info(f"Overall search accuracy: {overall_accuracy:.2f}")
            
        except Exception as e:
            results['issues'].append(f"Search functionality test failed: {e}")
            self.logger.error(f"Search functionality test failed: {e}")
        
        return results
    
    def test_performance_requirements(self) -> Dict[str, Any]:
        """
        Test performance requirements including response time.
        
        Returns:
            dict: Performance test results
        """
        results = {
            'response_times': [],
            'avg_response_time': 0.0,
            'max_response_time': 0.0,
            'performance_passed': False,
            'issues': []
        }
        
        if not self.search_engine:
            results['issues'].append("Search engine not initialized")
            return results
        
        try:
            self.logger.info("Testing performance requirements...")
            
            # Test response time with multiple queries
            performance_queries = self.test_queries[:5]  # Use first 5 queries for performance test
            
            for query_text in performance_queries:
                try:
                    start_time = time.time()
                    search_results, _ = self.search_engine.search(query_text)
                    end_time = time.time()
                    
                    response_time = end_time - start_time
                    results['response_times'].append(response_time)
                    
                    self.logger.info(f"Query '{query_text}': {response_time:.3f}s")
                    
                except Exception as e:
                    results['issues'].append(f"Performance test failed for '{query_text}': {e}")
            
            # Calculate performance metrics
            if results['response_times']:
                results['avg_response_time'] = sum(results['response_times']) / len(results['response_times'])
                results['max_response_time'] = max(results['response_times'])
                
                # Check if performance requirements are met
                performance_passed = (
                    results['avg_response_time'] <= self.performance_requirements['max_query_time'] and
                    results['max_response_time'] <= self.performance_requirements['max_query_time']
                )
                results['performance_passed'] = performance_passed
                
                self.logger.info(f"Average response time: {results['avg_response_time']:.3f}s")
                self.logger.info(f"Maximum response time: {results['max_response_time']:.3f}s")
                self.logger.info(f"Performance requirement (≤{self.performance_requirements['max_query_time']}s): {'✅ PASS' if performance_passed else '❌ FAIL'}")
            
        except Exception as e:
            results['issues'].append(f"Performance test failed: {e}")
            self.logger.error(f"Performance test failed: {e}")
        
        return results
    
    def test_edge_cases(self) -> Dict[str, Any]:
        """
        Test edge cases and error handling.
        
        Returns:
            dict: Edge case test results
        """
        results = {
            'edge_cases_tested': 0,
            'edge_cases_passed': 0,
            'test_details': {},
            'issues': []
        }
        
        if not self.search_engine:
            results['issues'].append("Search engine not initialized")
            return results
        
        try:
            self.logger.info("Testing edge cases and error handling...")
            
            edge_cases = [
                # Empty and invalid queries
                ("", "empty_query"),
                ("   ", "whitespace_query"),
                ("a", "too_short_query"),
                ("x" * 300, "too_long_query"),
                
                # Nonsensical queries
                ("asdfghjkl qwertyuiop", "nonsensical_query"),
                ("12345 67890", "numeric_query"),
                ("!@#$%^&*()", "special_characters"),
                
                # Valid but unlikely to match queries
                ("purple elephant architecture", "unlikely_match"),
                ("underwater buildings", "impossible_match")
            ]
            
            for query_text, test_name in edge_cases:
                results['edge_cases_tested'] += 1
                
                try:
                    self.logger.info(f"Testing edge case: {test_name}")
                    
                    if test_name in ["empty_query", "whitespace_query", "too_short_query"]:
                        # These should raise ValueError
                        try:
                            search_results, _ = self.search_engine.search(query_text)
                            results['test_details'][test_name] = {
                                'status': 'FAIL',
                                'reason': 'Should have raised ValueError'
                            }
                            self.logger.warning(f"  ❌ {test_name}: Should have raised ValueError")
                        except ValueError:
                            results['edge_cases_passed'] += 1
                            results['test_details'][test_name] = {
                                'status': 'PASS',
                                'reason': 'Correctly raised ValueError'
                            }
                            self.logger.info(f"  ✅ {test_name}: Correctly handled invalid input")
                    else:
                        # These should return gracefully (possibly with no results)
                        search_results, _ = self.search_engine.search(query_text)
                        results['edge_cases_passed'] += 1
                        results['test_details'][test_name] = {
                            'status': 'PASS',
                            'reason': f'Returned {len(search_results)} results gracefully'
                        }
                        self.logger.info(f"  ✅ {test_name}: Handled gracefully ({len(search_results)} results)")
                
                except Exception as e:
                    if test_name in ["empty_query", "whitespace_query", "too_short_query"] and isinstance(e, ValueError):
                        results['edge_cases_passed'] += 1
                        results['test_details'][test_name] = {
                            'status': 'PASS',
                            'reason': 'Correctly raised ValueError'
                        }
                        self.logger.info(f"  ✅ {test_name}: Correctly handled invalid input")
                    else:
                        results['test_details'][test_name] = {
                            'status': 'FAIL',
                            'reason': f'Unexpected error: {e}'
                        }
                        results['issues'].append(f"Edge case '{test_name}' failed: {e}")
                        self.logger.error(f"  ❌ {test_name}: Unexpected error: {e}")
            
        except Exception as e:
            results['issues'].append(f"Edge case testing failed: {e}")
            self.logger.error(f"Edge case testing failed: {e}")
        
        return results
    
    def _calculate_query_accuracy(self, query_text: str, search_results: List) -> float:
        """
        Calculate a basic accuracy score for query results.
        
        Args:
            query_text: The search query
            search_results: List of search results
            
        Returns:
            float: Accuracy score between 0.0 and 1.0
        """
        if not search_results:
            return 0.0
        
        # Simple heuristic: check if query keywords appear in result descriptions/features
        query_keywords = query_text.lower().split()
        
        total_relevance = 0.0
        for result in search_results:
            relevance = 0.0
            
            # Check description
            description_lower = result.description.lower()
            for keyword in query_keywords:
                if keyword in description_lower:
                    relevance += 0.3
            
            # Check features
            if hasattr(result, 'features') and result.features:
                features_text = ' '.join(result.features).lower()
                for keyword in query_keywords:
                    if keyword in features_text:
                        relevance += 0.4
            
            # Weight by confidence score
            relevance *= result.confidence_score
            total_relevance += min(relevance, 1.0)  # Cap at 1.0 per result
        
        # Average relevance across results
        return min(total_relevance / len(search_results), 1.0)
    
    def run_complete_integration_test(self) -> Dict[str, Any]:
        """
        Run the complete end-to-end integration test suite.
        
        Returns:
            dict: Complete test results
        """
        self.logger.info("🏗️  Starting AI Architectural Search - End-to-End Integration Test")
        self.logger.info("=" * 70)
        
        start_time = time.time()
        
        # Setup test environment
        if not self.setup_test_environment():
            self.test_results['overall_status'] = 'SETUP_FAILED'
            return self.test_results
        
        # Run component tests
        self.logger.info("\n1. Testing Component Initialization...")
        self.test_results['component_tests'] = self.test_component_initialization()
        
        # Run search functionality tests
        self.logger.info("\n2. Testing Search Functionality...")
        self.test_results['search_tests'] = self.test_search_functionality()
        
        # Run performance tests
        self.logger.info("\n3. Testing Performance Requirements...")
        self.test_results['performance_tests'] = self.test_performance_requirements()
        
        # Run edge case tests
        self.logger.info("\n4. Testing Edge Cases...")
        self.test_results['edge_case_tests'] = self.test_edge_cases()
        
        # Calculate overall status
        total_time = time.time() - start_time
        self.test_results['total_test_time'] = total_time
        
        # Determine overall status
        component_success = all([
            self.test_results['component_tests'].get('config_loading', False),
            self.test_results['component_tests'].get('model_manager', False),
            self.test_results['component_tests'].get('metadata_store', False),
            self.test_results['component_tests'].get('search_engine', False)
        ])
        
        search_success = (
            self.test_results['search_tests'].get('successful_queries', 0) > 0 and
            self.test_results['search_tests'].get('overall_accuracy', 0) >= self.performance_requirements['min_accuracy_rate']
        )
        
        performance_success = self.test_results['performance_tests'].get('performance_passed', False)
        
        edge_case_success = (
            self.test_results['edge_case_tests'].get('edge_cases_passed', 0) >= 
            self.test_results['edge_case_tests'].get('edge_cases_tested', 1) * 0.8  # 80% pass rate
        )
        
        if component_success and search_success and performance_success and edge_case_success:
            self.test_results['overall_status'] = 'PASS'
        else:
            self.test_results['overall_status'] = 'FAIL'
        
        # Generate summary
        self._generate_test_summary()
        
        return self.test_results
    
    def _generate_test_summary(self):
        """Generate and log test summary."""
        self.logger.info("\n" + "=" * 70)
        self.logger.info("🏗️  END-TO-END INTEGRATION TEST SUMMARY")
        self.logger.info("=" * 70)
        
        # Component tests summary
        component_tests = self.test_results['component_tests']
        self.logger.info(f"\n📦 Component Initialization:")
        self.logger.info(f"   Config Loading: {'✅ PASS' if component_tests.get('config_loading') else '❌ FAIL'}")
        self.logger.info(f"   Model Manager: {'✅ PASS' if component_tests.get('model_manager') else '❌ FAIL'}")
        self.logger.info(f"   Metadata Store: {'✅ PASS' if component_tests.get('metadata_store') else '❌ FAIL'}")
        self.logger.info(f"   Search Engine: {'✅ PASS' if component_tests.get('search_engine') else '❌ FAIL'}")
        
        # Search tests summary
        search_tests = self.test_results['search_tests']
        self.logger.info(f"\n🔍 Search Functionality:")
        self.logger.info(f"   Successful Queries: {search_tests.get('successful_queries', 0)}")
        self.logger.info(f"   Failed Queries: {search_tests.get('failed_queries', 0)}")
        if 'overall_accuracy' in search_tests:
            self.logger.info(f"   Overall Accuracy: {search_tests['overall_accuracy']:.2f}")
            accuracy_pass = search_tests['overall_accuracy'] >= self.performance_requirements['min_accuracy_rate']
            self.logger.info(f"   Accuracy Requirement (≥{self.performance_requirements['min_accuracy_rate']}): {'✅ PASS' if accuracy_pass else '❌ FAIL'}")
        
        # Performance tests summary
        performance_tests = self.test_results['performance_tests']
        self.logger.info(f"\n⚡ Performance:")
        if 'avg_response_time' in performance_tests:
            self.logger.info(f"   Average Response Time: {performance_tests['avg_response_time']:.3f}s")
            self.logger.info(f"   Maximum Response Time: {performance_tests['max_response_time']:.3f}s")
            self.logger.info(f"   Performance Requirement (≤{self.performance_requirements['max_query_time']}s): {'✅ PASS' if performance_tests.get('performance_passed') else '❌ FAIL'}")
        
        # Edge case tests summary
        edge_tests = self.test_results['edge_case_tests']
        self.logger.info(f"\n🧪 Edge Cases:")
        self.logger.info(f"   Tests Passed: {edge_tests.get('edge_cases_passed', 0)}/{edge_tests.get('edge_cases_tested', 0)}")
        if edge_tests.get('edge_cases_tested', 0) > 0:
            pass_rate = edge_tests.get('edge_cases_passed', 0) / edge_tests.get('edge_cases_tested', 0)
            self.logger.info(f"   Pass Rate: {pass_rate:.1%}")
        
        # Overall status
        self.logger.info(f"\n🎯 OVERALL STATUS: {self.test_results['overall_status']}")
        self.logger.info(f"   Total Test Time: {self.test_results.get('total_test_time', 0):.2f}s")
        
        # Issues summary
        all_issues = []
        for test_category in ['component_tests', 'search_tests', 'performance_tests', 'edge_case_tests']:
            issues = self.test_results.get(test_category, {}).get('issues', [])
            all_issues.extend(issues)
        
        if all_issues:
            self.logger.info(f"\n⚠️  Issues Found ({len(all_issues)}):")
            for i, issue in enumerate(all_issues[:10], 1):  # Show first 10 issues
                self.logger.info(f"   {i}. {issue}")
            if len(all_issues) > 10:
                self.logger.info(f"   ... and {len(all_issues) - 10} more issues")
        else:
            self.logger.info(f"\n✅ No issues found!")
    
    def cleanup(self):
        """Clean up test resources."""
        if self.search_engine:
            self.search_engine.cleanup()
        self.logger.info("Test cleanup completed")


def main():
    """Main function to run the end-to-end integration test."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('integration_test.log')
        ]
    )
    
    # Run the integration test
    test_runner = EndToEndIntegrationTest()
    
    try:
        results = test_runner.run_complete_integration_test()
        
        # Save results to file
        results_file = Path('integration_test_results.json')
        with open(results_file, 'w') as f:
            # Convert numpy arrays to lists for JSON serialization
            json_results = json.loads(json.dumps(results, default=str))
            json.dump(json_results, f, indent=2)
        
        print(f"\n📁 Test results saved to: {results_file}")
        
        # Exit with appropriate code
        if results['overall_status'] == 'PASS':
            print("🎉 All integration tests passed!")
            sys.exit(0)
        else:
            print("❌ Integration tests failed!")
            sys.exit(1)
    
    except Exception as e:
        logging.error(f"Integration test failed with exception: {e}")
        sys.exit(1)
    
    finally:
        test_runner.cleanup()


if __name__ == "__main__":
    main()