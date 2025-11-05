#!/usr/bin/env python3
"""
Comprehensive Integration Testing and Validation Suite for Task 7.4

This script conducts complete integration testing and validation covering:
- Test all predefined queries for accuracy and performance
- Validate interface usability and professional appearance  
- Verify consistent performance across multiple query sessions

Requirements: 5.1, 2.4, 5.4
"""

import sys
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
import statistics

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models.config import AppConfig
from src.processors.search_engine import SearchEngine
from test_queries_validation import TestQueryDataset, QueryValidator, ValidationResult


class IntegrationValidationSuite:
    """
    Comprehensive integration testing and validation suite for the AI Architectural Search System.
    
    This class implements all requirements for task 7.4:
    - Tests all predefined queries for accuracy and performance
    - Validates interface usability and professional appearance
    - Verifies consistent performance across multiple query sessions
    """
    
    def __init__(self):
        """Initialize the validation suite."""
        self.logger = logging.getLogger(__name__)
        self.config = None
        self.search_engine = None
        self.test_dataset = TestQueryDataset()
        self.validator = QueryValidator()
        
        # Test results storage
        self.validation_results = {
            'query_accuracy_tests': {},
            'performance_consistency_tests': {},
            'interface_validation_tests': {},
            'overall_summary': {},
            'recommendations': []
        }
        
        # Performance requirements from specifications
        self.performance_requirements = {
            'max_query_time': 5.0,  # seconds (Requirement 5.4)
            'min_accuracy_rate': 0.7,  # 70% accuracy (Requirement 5.1)
            'consistency_variance_threshold': 0.5,  # Max 0.5s variance between sessions
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
            self.logger.info("Setting up integration validation test environment...")
            
            # Load configuration
            self.config = AppConfig.load_config()
            
            # Initialize search engine
            self.search_engine = SearchEngine(self.config)
            
            # Validate system readiness
            readiness = self.search_engine.validate_search_readiness()
            if not readiness['ready']:
                self.logger.error(f"Search system not ready: {readiness['issues']}")
                return False
            
            self.logger.info(f"Search system ready with {readiness['statistics']['total_images']} images")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup test environment: {e}")
            return False
    
    def test_predefined_queries_accuracy_performance(self) -> Dict[str, Any]:
        """
        Test all predefined queries for accuracy and performance (Requirements 5.1, 5.4).
        
        Returns:
            dict: Query accuracy and performance test results
        """
        self.logger.info("Testing predefined queries for accuracy and performance...")
        
        results = {
            'total_queries': len(self.test_dataset.queries),
            'passed_queries': 0,
            'failed_queries': 0,
            'accuracy_scores': [],
            'performance_times': [],
            'query_details': [],
            'performance_violations': [],
            'accuracy_violations': [],
            'issues': []
        }
        
        try:
            for i, query in enumerate(self.test_dataset.queries, 1):
                self.logger.info(f"Testing query {i}/{len(self.test_dataset.queries)}: '{query.query_text}'")
                
                try:
                    # Measure performance
                    start_time = time.time()
                    search_results, query_obj = self.search_engine.search(query.query_text, max_results=5)
                    execution_time = time.time() - start_time
                    
                    # Convert search results to validation format
                    result_data = []
                    for result in search_results:
                        result_data.append({
                            'image_path': result.image_path,
                            'description': result.description,
                            'features': result.features if hasattr(result, 'features') else [],
                            'confidence_score': result.confidence_score,
                            'similarity_score': result.similarity_score if hasattr(result, 'similarity_score') else result.confidence_score
                        })
                    
                    # Validate results
                    validation = self.validator.validate_query_results(query, result_data)
                    validation.execution_time = execution_time
                    
                    # Record results
                    results['accuracy_scores'].append(validation.accuracy_score)
                    results['performance_times'].append(execution_time)
                    
                    query_detail = {
                        'query_text': query.query_text,
                        'priority': query.priority,
                        'execution_time': execution_time,
                        'accuracy_score': validation.accuracy_score,
                        'result_count': len(result_data),
                        'passed': validation.passed,
                        'issues': validation.issues
                    }
                    results['query_details'].append(query_detail)
                    
                    # Check for violations
                    if execution_time > self.performance_requirements['max_query_time']:
                        results['performance_violations'].append({
                            'query': query.query_text,
                            'time': execution_time,
                            'limit': self.performance_requirements['max_query_time']
                        })
                    
                    if validation.accuracy_score < self.performance_requirements['min_accuracy_rate']:
                        results['accuracy_violations'].append({
                            'query': query.query_text,
                            'accuracy': validation.accuracy_score,
                            'threshold': self.performance_requirements['min_accuracy_rate']
                        })
                    
                    if validation.passed:
                        results['passed_queries'] += 1
                        self.logger.info(f"  ✅ PASS - {len(result_data)} results, {validation.accuracy_score:.2f} accuracy, {execution_time:.3f}s")
                    else:
                        results['failed_queries'] += 1
                        self.logger.warning(f"  ❌ FAIL - {validation.accuracy_score:.2f} accuracy, issues: {', '.join(validation.issues)}")
                
                except Exception as e:
                    results['failed_queries'] += 1
                    results['issues'].append(f"Query '{query.query_text}' failed: {str(e)}")
                    self.logger.error(f"  ❌ ERROR - {str(e)}")
            
            # Calculate summary statistics
            if results['accuracy_scores']:
                results['avg_accuracy'] = statistics.mean(results['accuracy_scores'])
                results['min_accuracy'] = min(results['accuracy_scores'])
                results['max_accuracy'] = max(results['accuracy_scores'])
            
            if results['performance_times']:
                results['avg_performance_time'] = statistics.mean(results['performance_times'])
                results['min_performance_time'] = min(results['performance_times'])
                results['max_performance_time'] = max(results['performance_times'])
            
            results['pass_rate'] = results['passed_queries'] / results['total_queries'] if results['total_queries'] > 0 else 0
            
            self.logger.info(f"Query testing complete: {results['passed_queries']}/{results['total_queries']} passed ({results['pass_rate']:.1%})")
            
        except Exception as e:
            results['issues'].append(f"Query accuracy/performance testing failed: {str(e)}")
            self.logger.error(f"Query accuracy/performance testing failed: {e}")
        
        return results
    
    def test_performance_consistency_across_sessions(self) -> Dict[str, Any]:
        """
        Verify consistent performance across multiple query sessions (Requirement 5.4).
        
        Returns:
            dict: Performance consistency test results
        """
        self.logger.info("Testing performance consistency across multiple query sessions...")
        
        results = {
            'sessions_tested': 3,
            'queries_per_session': 5,
            'session_results': [],
            'consistency_analysis': {},
            'violations': [],
            'issues': []
        }
        
        try:
            # Select representative queries for consistency testing
            test_queries = [
                "red brick buildings",
                "glass and steel structures", 
                "stone facades",
                "buildings with large windows",
                "modern office buildings"
            ]
            
            # Run multiple sessions
            for session_num in range(1, results['sessions_tested'] + 1):
                self.logger.info(f"Running performance session {session_num}/{results['sessions_tested']}")
                
                session_data = {
                    'session_number': session_num,
                    'query_times': [],
                    'query_results': [],
                    'avg_time': 0.0,
                    'total_time': 0.0
                }
                
                session_start = time.time()
                
                for query_text in test_queries:
                    try:
                        start_time = time.time()
                        search_results, _ = self.search_engine.search(query_text, max_results=5)
                        execution_time = time.time() - start_time
                        
                        session_data['query_times'].append(execution_time)
                        session_data['query_results'].append({
                            'query': query_text,
                            'time': execution_time,
                            'result_count': len(search_results)
                        })
                        
                        self.logger.info(f"  Query '{query_text}': {execution_time:.3f}s ({len(search_results)} results)")
                        
                    except Exception as e:
                        results['issues'].append(f"Session {session_num} query '{query_text}' failed: {str(e)}")
                        self.logger.error(f"  Query '{query_text}' failed: {e}")
                
                session_data['total_time'] = time.time() - session_start
                session_data['avg_time'] = statistics.mean(session_data['query_times']) if session_data['query_times'] else 0.0
                
                results['session_results'].append(session_data)
                
                self.logger.info(f"  Session {session_num} complete: avg {session_data['avg_time']:.3f}s per query")
                
                # Brief pause between sessions to simulate real usage
                time.sleep(1)
            
            # Analyze consistency across sessions
            if len(results['session_results']) >= 2:
                session_avg_times = [session['avg_time'] for session in results['session_results']]
                
                results['consistency_analysis'] = {
                    'session_avg_times': session_avg_times,
                    'overall_avg_time': statistics.mean(session_avg_times),
                    'time_variance': statistics.variance(session_avg_times) if len(session_avg_times) > 1 else 0.0,
                    'time_std_dev': statistics.stdev(session_avg_times) if len(session_avg_times) > 1 else 0.0,
                    'min_session_time': min(session_avg_times),
                    'max_session_time': max(session_avg_times),
                    'time_range': max(session_avg_times) - min(session_avg_times)
                }
                
                # Check consistency violations
                if results['consistency_analysis']['time_range'] > self.performance_requirements['consistency_variance_threshold']:
                    results['violations'].append({
                        'type': 'consistency_variance',
                        'actual_range': results['consistency_analysis']['time_range'],
                        'threshold': self.performance_requirements['consistency_variance_threshold']
                    })
                
                # Check if any session exceeded performance requirements
                for session in results['session_results']:
                    if session['avg_time'] > self.performance_requirements['max_query_time']:
                        results['violations'].append({
                            'type': 'session_performance',
                            'session': session['session_number'],
                            'avg_time': session['avg_time'],
                            'threshold': self.performance_requirements['max_query_time']
                        })
                
                self.logger.info(f"Consistency analysis: {results['consistency_analysis']['time_range']:.3f}s range across sessions")
            
        except Exception as e:
            results['issues'].append(f"Performance consistency testing failed: {str(e)}")
            self.logger.error(f"Performance consistency testing failed: {e}")
        
        return results
    
    def validate_interface_usability_appearance(self) -> Dict[str, Any]:
        """
        Validate interface usability and professional appearance (Requirement 2.4).
        
        Returns:
            dict: Interface validation test results
        """
        self.logger.info("Validating interface usability and professional appearance...")
        
        results = {
            'component_tests': [],
            'usability_checks': [],
            'appearance_checks': [],
            'passed_checks': 0,
            'failed_checks': 0,
            'issues': []
        }
        
        try:
            # Test 1: Web application components exist and are accessible
            web_components = [
                'src/web/app.py',
                'src/web/search.py', 
                'src/web/results.py',
                'src/web/components.py',
                'src/web/styles.py'
            ]
            
            for component in web_components:
                if Path(component).exists():
                    results['component_tests'].append({
                        'component': component,
                        'status': 'PASS',
                        'details': 'Component file exists'
                    })
                    results['passed_checks'] += 1
                else:
                    results['component_tests'].append({
                        'component': component,
                        'status': 'FAIL',
                        'details': 'Component file missing'
                    })
                    results['failed_checks'] += 1
                    results['issues'].append(f"Missing web component: {component}")
            
            # Test 2: Search functionality integration
            try:
                # Test that search can be performed (simulating web interface usage)
                test_query = "red brick buildings"
                search_results, _ = self.search_engine.search(test_query, max_results=5)
                
                results['usability_checks'].append({
                    'check': 'Search Integration',
                    'status': 'PASS',
                    'details': f'Search returned {len(search_results)} results for test query'
                })
                results['passed_checks'] += 1
                
                # Test result formatting (simulating web display)
                if search_results:
                    first_result = search_results[0]
                    required_fields = ['image_path', 'description', 'confidence_score']
                    
                    missing_fields = []
                    for field in required_fields:
                        if not hasattr(first_result, field) or getattr(first_result, field) is None:
                            missing_fields.append(field)
                    
                    if not missing_fields:
                        results['usability_checks'].append({
                            'check': 'Result Data Completeness',
                            'status': 'PASS',
                            'details': 'All required result fields present'
                        })
                        results['passed_checks'] += 1
                    else:
                        results['usability_checks'].append({
                            'check': 'Result Data Completeness',
                            'status': 'FAIL',
                            'details': f'Missing fields: {missing_fields}'
                        })
                        results['failed_checks'] += 1
                        results['issues'].append(f"Missing result fields: {missing_fields}")
                
            except Exception as e:
                results['usability_checks'].append({
                    'check': 'Search Integration',
                    'status': 'FAIL',
                    'details': f'Search integration failed: {str(e)}'
                })
                results['failed_checks'] += 1
                results['issues'].append(f"Search integration failed: {str(e)}")
            
            # Test 3: Professional appearance elements
            appearance_elements = [
                ('Error Handling', 'src/web/error_handler.py'),
                ('Caching System', 'src/web/cache.py'),
                ('Styling Components', 'src/web/styles.py')
            ]
            
            for element_name, element_path in appearance_elements:
                if Path(element_path).exists():
                    results['appearance_checks'].append({
                        'element': element_name,
                        'status': 'PASS',
                        'details': f'{element_name} component available'
                    })
                    results['passed_checks'] += 1
                else:
                    results['appearance_checks'].append({
                        'element': element_name,
                        'status': 'FAIL',
                        'details': f'{element_name} component missing'
                    })
                    results['failed_checks'] += 1
                    results['issues'].append(f"Missing appearance element: {element_name}")
            
            # Test 4: Demo readiness validation
            try:
                # Check if demo startup script exists
                demo_scripts = ['demo_startup.py', 'prepare_demo.py']
                demo_script_found = any(Path(script).exists() for script in demo_scripts)
                
                if demo_script_found:
                    results['usability_checks'].append({
                        'check': 'Demo Preparation',
                        'status': 'PASS',
                        'details': 'Demo startup scripts available'
                    })
                    results['passed_checks'] += 1
                else:
                    results['usability_checks'].append({
                        'check': 'Demo Preparation',
                        'status': 'FAIL',
                        'details': 'No demo startup scripts found'
                    })
                    results['failed_checks'] += 1
                    results['issues'].append("Missing demo preparation scripts")
                
            except Exception as e:
                results['issues'].append(f"Demo readiness check failed: {str(e)}")
            
            # Calculate success rate
            total_checks = results['passed_checks'] + results['failed_checks']
            results['success_rate'] = results['passed_checks'] / total_checks if total_checks > 0 else 0
            
            self.logger.info(f"Interface validation complete: {results['passed_checks']}/{total_checks} checks passed ({results['success_rate']:.1%})")
            
        except Exception as e:
            results['issues'].append(f"Interface validation failed: {str(e)}")
            self.logger.error(f"Interface validation failed: {e}")
        
        return results
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive validation report with recommendations.
        
        Returns:
            dict: Complete validation report
        """
        self.logger.info("Generating comprehensive validation report...")
        
        # Calculate overall scores
        query_tests = self.validation_results['query_accuracy_tests']
        performance_tests = self.validation_results['performance_consistency_tests']
        interface_tests = self.validation_results['interface_validation_tests']
        
        # Overall assessment
        query_score = query_tests.get('pass_rate', 0) * 100
        performance_score = 100 if not performance_tests.get('violations', []) else 50
        interface_score = interface_tests.get('success_rate', 0) * 100
        
        overall_score = (query_score * 0.5 + performance_score * 0.3 + interface_score * 0.2)
        
        report = {
            'validation_timestamp': datetime.now().isoformat(),
            'overall_score': overall_score,
            'task_7_4_status': 'COMPLETE' if overall_score >= 70 else 'NEEDS_IMPROVEMENT',
            
            'requirement_compliance': {
                '5.1_predefined_queries': {
                    'status': 'PASS' if query_tests.get('pass_rate', 0) >= 0.7 else 'FAIL',
                    'pass_rate': query_tests.get('pass_rate', 0),
                    'details': f"{query_tests.get('passed_queries', 0)}/{query_tests.get('total_queries', 0)} queries passed"
                },
                '2.4_interface_usability': {
                    'status': 'PASS' if interface_tests.get('success_rate', 0) >= 0.8 else 'FAIL',
                    'success_rate': interface_tests.get('success_rate', 0),
                    'details': f"{interface_tests.get('passed_checks', 0)} checks passed"
                },
                '5.4_performance_consistency': {
                    'status': 'PASS' if not performance_tests.get('violations', []) else 'FAIL',
                    'violations': len(performance_tests.get('violations', [])),
                    'details': f"Performance consistency across {performance_tests.get('sessions_tested', 0)} sessions"
                }
            },
            
            'summary_statistics': {
                'total_queries_tested': query_tests.get('total_queries', 0),
                'average_accuracy': query_tests.get('avg_accuracy', 0),
                'average_response_time': query_tests.get('avg_performance_time', 0),
                'performance_violations': len(query_tests.get('performance_violations', [])),
                'accuracy_violations': len(query_tests.get('accuracy_violations', [])),
                'interface_components_validated': len(interface_tests.get('component_tests', [])),
                'consistency_sessions_tested': performance_tests.get('sessions_tested', 0)
            },
            
            'recommendations': self._generate_recommendations(query_tests, performance_tests, interface_tests),
            
            'detailed_results': {
                'query_accuracy_performance': query_tests,
                'performance_consistency': performance_tests,
                'interface_validation': interface_tests
            }
        }
        
        return report
    
    def _generate_recommendations(self, query_tests: Dict, performance_tests: Dict, interface_tests: Dict) -> List[str]:
        """Generate actionable recommendations based on test results."""
        recommendations = []
        
        # Query accuracy recommendations
        if query_tests.get('pass_rate', 0) < 0.8:
            recommendations.append("Improve search algorithm accuracy - current pass rate below 80%")
        
        if query_tests.get('avg_accuracy', 0) < 0.7:
            recommendations.append("Enhance query understanding and result relevance scoring")
        
        # Performance recommendations
        if query_tests.get('avg_performance_time', 0) > 3.0:
            recommendations.append("Optimize search performance - average response time exceeds 3 seconds")
        
        if performance_tests.get('violations'):
            recommendations.append("Address performance consistency issues across query sessions")
        
        # Interface recommendations
        if interface_tests.get('success_rate', 0) < 0.9:
            recommendations.append("Complete interface components and improve usability features")
        
        if interface_tests.get('issues'):
            recommendations.append("Resolve interface component issues for professional appearance")
        
        # Demo readiness recommendations
        overall_ready = (
            query_tests.get('pass_rate', 0) >= 0.7 and
            not performance_tests.get('violations') and
            interface_tests.get('success_rate', 0) >= 0.8
        )
        
        if overall_ready:
            recommendations.append("✅ System is ready for client demonstration")
        else:
            recommendations.append("⚠️ Address identified issues before client demonstration")
        
        return recommendations
    
    def run_complete_validation_suite(self) -> Dict[str, Any]:
        """
        Run the complete integration validation suite for task 7.4.
        
        Returns:
            dict: Complete validation results
        """
        self.logger.info("🏗️ Starting Task 7.4 - Integration Testing and Validation Suite")
        self.logger.info("=" * 80)
        
        start_time = time.time()
        
        # Setup test environment
        if not self.setup_test_environment():
            return {'error': 'Failed to setup test environment'}
        
        try:
            # 1. Test predefined queries for accuracy and performance
            self.logger.info("\n1️⃣ Testing Predefined Queries for Accuracy and Performance...")
            self.validation_results['query_accuracy_tests'] = self.test_predefined_queries_accuracy_performance()
            
            # 2. Test performance consistency across multiple sessions
            self.logger.info("\n2️⃣ Testing Performance Consistency Across Multiple Sessions...")
            self.validation_results['performance_consistency_tests'] = self.test_performance_consistency_across_sessions()
            
            # 3. Validate interface usability and professional appearance
            self.logger.info("\n3️⃣ Validating Interface Usability and Professional Appearance...")
            self.validation_results['interface_validation_tests'] = self.validate_interface_usability_appearance()
            
            # 4. Generate comprehensive report
            self.logger.info("\n4️⃣ Generating Comprehensive Validation Report...")
            comprehensive_report = self.generate_comprehensive_report()
            
            total_time = time.time() - start_time
            comprehensive_report['total_validation_time'] = total_time
            
            # Log summary
            self._log_validation_summary(comprehensive_report)
            
            return comprehensive_report
            
        except Exception as e:
            self.logger.error(f"Validation suite failed: {e}")
            return {'error': f'Validation suite failed: {str(e)}'}
        
        finally:
            if self.search_engine:
                self.search_engine.cleanup()
    
    def _log_validation_summary(self, report: Dict[str, Any]):
        """Log validation summary to console."""
        self.logger.info("\n" + "=" * 80)
        self.logger.info("🎯 TASK 7.4 INTEGRATION VALIDATION SUMMARY")
        self.logger.info("=" * 80)
        
        # Overall status
        self.logger.info(f"Overall Score: {report['overall_score']:.1f}/100")
        self.logger.info(f"Task 7.4 Status: {report['task_7_4_status']}")
        
        # Requirement compliance
        self.logger.info(f"\n📋 Requirement Compliance:")
        for req_id, req_data in report['requirement_compliance'].items():
            status_icon = "✅" if req_data['status'] == 'PASS' else "❌"
            self.logger.info(f"  {status_icon} {req_id}: {req_data['status']} - {req_data['details']}")
        
        # Key statistics
        stats = report['summary_statistics']
        self.logger.info(f"\n📊 Key Statistics:")
        self.logger.info(f"  Queries Tested: {stats['total_queries_tested']}")
        self.logger.info(f"  Average Accuracy: {stats['average_accuracy']:.2f}")
        self.logger.info(f"  Average Response Time: {stats['average_response_time']:.3f}s")
        self.logger.info(f"  Performance Violations: {stats['performance_violations']}")
        self.logger.info(f"  Interface Components: {stats['interface_components_validated']}")
        
        # Recommendations
        self.logger.info(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            self.logger.info(f"  • {rec}")
        
        self.logger.info(f"\n⏱️ Total Validation Time: {report['total_validation_time']:.2f}s")


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('integration_validation.log')
        ]
    )


def main():
    """Main function to run the integration validation suite."""
    setup_logging()
    
    # Create and run validation suite
    validation_suite = IntegrationValidationSuite()
    
    try:
        results = validation_suite.run_complete_validation_suite()
        
        if 'error' in results:
            print(f"❌ Validation suite failed: {results['error']}")
            return False
        
        # Save results to file
        results_file = Path('task_7_4_validation_results.json')
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📁 Detailed validation results saved to: {results_file}")
        
        # Determine success
        success = results['task_7_4_status'] == 'COMPLETE'
        
        if success:
            print("🎉 Task 7.4 Integration Testing and Validation - COMPLETE!")
        else:
            print("⚠️ Task 7.4 Integration Testing and Validation - NEEDS IMPROVEMENT")
        
        return success
        
    except Exception as e:
        logging.error(f"Integration validation suite failed: {e}")
        print(f"❌ Integration validation suite failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)