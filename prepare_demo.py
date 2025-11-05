#!/usr/bin/env python3
"""
Demo preparation script for AI Architectural Search System.

This script helps prepare for client demonstrations by validating
the system and providing pre-demo checklists.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.models.config import AppConfig
    from src.processors.search_engine import SearchEngine
    from test_queries_validation import TestQueryDataset, QueryValidator
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all dependencies are installed and the system is properly set up.")
    sys.exit(1)


class DemoPreparation:
    """
    Demo preparation and validation system.
    """
    
    def __init__(self):
        """Initialize demo preparation."""
        self.config = None
        self.search_engine = None
        self.dataset = TestQueryDataset()
        self.validator = QueryValidator()
        
    def run_system_checks(self) -> Dict[str, Any]:
        """
        Run comprehensive system checks for demo readiness.
        
        Returns:
            Dict containing check results
        """
        print("🔍 Running Demo Readiness Checks...")
        print("=" * 50)
        
        results = {
            'system_ready': True,
            'issues': [],
            'warnings': [],
            'statistics': {}
        }
        
        # Check 1: System requirements
        print("\n1. System Requirements Check")
        print("-" * 30)
        
        # Python version
        if sys.version_info < (3, 8):
            results['system_ready'] = False
            results['issues'].append("Python 3.8+ required")
            print("❌ Python version too old")
        else:
            print(f"✅ Python {sys.version.split()[0]}")
        
        # Required packages
        required_packages = ['streamlit', 'torch', 'transformers', 'clip', 'PIL', 'numpy']
        missing_packages = []
        
        for package in required_packages:
            try:
                if package == 'clip':
                    import clip
                elif package == 'PIL':
                    from PIL import Image
                else:
                    __import__(package)
                print(f"✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package}")
        
        if missing_packages:
            results['system_ready'] = False
            results['issues'].append(f"Missing packages: {', '.join(missing_packages)}")
        
        # Check 2: Data availability
        print("\n2. Data Availability Check")
        print("-" * 30)
        
        # Image directory
        image_dir = Path("images")
        if not image_dir.exists():
            results['system_ready'] = False
            results['issues'].append("Image directory not found")
            print("❌ Image directory missing")
        else:
            # Count images
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
            image_count = 0
            for ext in image_extensions:
                image_count += len(list(image_dir.rglob(f"*{ext}")))
                image_count += len(list(image_dir.rglob(f"*{ext.upper()}")))
            
            results['statistics']['image_count'] = image_count
            
            if image_count == 0:
                results['system_ready'] = False
                results['issues'].append("No images found")
                print("❌ No images found")
            elif image_count < 20:
                results['warnings'].append(f"Only {image_count} images (recommend 20+)")
                print(f"⚠️  Only {image_count} images found")
            else:
                print(f"✅ {image_count} images found")
        
        # Metadata file
        metadata_file = Path("image_metadata.json")
        if not metadata_file.exists():
            results['system_ready'] = False
            results['issues'].append("Image metadata not found - run offline processing")
            print("❌ Image metadata missing")
        else:
            print("✅ Image metadata found")
        
        # Check 3: Search system
        print("\n3. Search System Check")
        print("-" * 30)
        
        try:
            self.config = AppConfig.load_config()
            print("✅ Configuration loaded")
            
            self.search_engine = SearchEngine(self.config)
            readiness = self.search_engine.validate_search_readiness()
            
            if readiness['ready']:
                print("✅ Search engine ready")
                results['statistics'].update(readiness['statistics'])
            else:
                results['system_ready'] = False
                results['issues'].extend(readiness['issues'])
                print("❌ Search engine not ready")
                for issue in readiness['issues']:
                    print(f"   • {issue}")
                    
        except Exception as e:
            results['system_ready'] = False
            results['issues'].append(f"Search system error: {e}")
            print(f"❌ Search system error: {e}")
        
        return results
    
    def test_demo_queries(self) -> Dict[str, Any]:
        """
        Test all demo queries for readiness.
        
        Returns:
            Dict containing test results
        """
        print("\n🧪 Testing Demo Queries...")
        print("=" * 30)
        
        if not self.search_engine:
            print("❌ Search engine not available")
            return {'ready': False, 'error': 'Search engine not initialized'}
        
        demo_queries = self.dataset.get_demo_queries()
        high_priority = [q for q in demo_queries if q.priority == "high"]
        
        results = {
            'ready': True,
            'total_queries': len(demo_queries),
            'high_priority_queries': len(high_priority),
            'passed_queries': 0,
            'failed_queries': [],
            'performance_stats': {
                'avg_response_time': 0,
                'max_response_time': 0,
                'min_response_time': float('inf')
            }
        }
        
        response_times = []
        
        print(f"Testing {len(high_priority)} high-priority queries...")
        
        for i, query in enumerate(high_priority, 1):
            print(f"\n{i}. Testing: \"{query.query_text}\"")
            
            try:
                # Time the query
                start_time = time.time()
                search_results, _ = self.search_engine.search(query.query_text)
                end_time = time.time()
                
                response_time = end_time - start_time
                response_times.append(response_time)
                
                # Validate results
                validation = self.validator.validate_query_results(query, search_results)
                
                if validation.passed:
                    results['passed_queries'] += 1
                    print(f"   ✅ PASSED ({response_time:.2f}s, {len(search_results)} results, {validation.accuracy_score:.2f} accuracy)")
                else:
                    results['failed_queries'].append({
                        'query': query.query_text,
                        'issues': validation.issues,
                        'accuracy': validation.accuracy_score
                    })
                    print(f"   ❌ FAILED ({response_time:.2f}s, {validation.accuracy_score:.2f} accuracy)")
                    for issue in validation.issues:
                        print(f"      • {issue}")
                
            except Exception as e:
                results['failed_queries'].append({
                    'query': query.query_text,
                    'issues': [f"Query execution error: {e}"],
                    'accuracy': 0.0
                })
                print(f"   ❌ ERROR: {e}")
        
        # Calculate performance statistics
        if response_times:
            results['performance_stats']['avg_response_time'] = sum(response_times) / len(response_times)
            results['performance_stats']['max_response_time'] = max(response_times)
            results['performance_stats']['min_response_time'] = min(response_times)
        
        # Determine overall readiness
        pass_rate = results['passed_queries'] / len(high_priority) if high_priority else 0
        avg_response_time = results['performance_stats']['avg_response_time']
        
        if pass_rate < 0.9:  # 90% pass rate required
            results['ready'] = False
        
        if avg_response_time > 5.0:  # 5 second requirement
            results['ready'] = False
        
        return results
    
    def generate_demo_report(self, system_results: Dict, query_results: Dict) -> str:
        """
        Generate a comprehensive demo readiness report.
        
        Args:
            system_results: Results from system checks
            query_results: Results from query testing
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("🎪 DEMO READINESS REPORT")
        report.append("=" * 50)
        
        # Overall status
        overall_ready = system_results['system_ready'] and query_results.get('ready', False)
        status_icon = "✅" if overall_ready else "❌"
        report.append(f"\n{status_icon} OVERALL STATUS: {'READY FOR DEMO' if overall_ready else 'NOT READY'}")
        
        # System status
        report.append(f"\n🔧 SYSTEM STATUS")
        report.append("-" * 20)
        
        if system_results['system_ready']:
            report.append("✅ All system requirements met")
            if 'image_count' in system_results['statistics']:
                report.append(f"✅ {system_results['statistics']['image_count']} images available")
        else:
            report.append("❌ System issues found:")
            for issue in system_results['issues']:
                report.append(f"   • {issue}")
        
        if system_results['warnings']:
            report.append("⚠️  Warnings:")
            for warning in system_results['warnings']:
                report.append(f"   • {warning}")
        
        # Query testing status
        if 'total_queries' in query_results:
            report.append(f"\n🧪 QUERY TESTING STATUS")
            report.append("-" * 25)
            
            passed = query_results['passed_queries']
            total = query_results['high_priority_queries']
            pass_rate = (passed / total * 100) if total > 0 else 0
            
            report.append(f"📊 Pass Rate: {passed}/{total} ({pass_rate:.1f}%)")
            
            perf = query_results['performance_stats']
            report.append(f"⏱️  Avg Response Time: {perf['avg_response_time']:.2f}s")
            report.append(f"⏱️  Max Response Time: {perf['max_response_time']:.2f}s")
            
            if query_results['failed_queries']:
                report.append(f"\n❌ Failed Queries:")
                for failure in query_results['failed_queries']:
                    report.append(f"   • \"{failure['query']}\" (accuracy: {failure['accuracy']:.2f})")
        
        # Recommendations
        report.append(f"\n💡 RECOMMENDATIONS")
        report.append("-" * 20)
        
        if overall_ready:
            report.append("✅ System is ready for demo presentation")
            report.append("✅ All high-priority queries working correctly")
            report.append("✅ Performance meets requirements")
            report.append("\n🎯 Demo Tips:")
            report.append("   • Start with high-priority queries for best results")
            report.append("   • Have backup queries ready for each category")
            report.append("   • Monitor response times during presentation")
        else:
            report.append("❌ Address the following before demo:")
            if not system_results['system_ready']:
                for issue in system_results['issues']:
                    report.append(f"   • Fix: {issue}")
            
            if not query_results.get('ready', True):
                report.append("   • Improve query performance and accuracy")
                report.append("   • Consider reprocessing images if accuracy is low")
        
        return "\n".join(report)
    
    def run_full_preparation(self) -> bool:
        """
        Run complete demo preparation process.
        
        Returns:
            True if demo is ready, False otherwise
        """
        print("🎪 AI Architectural Search - Demo Preparation")
        print("=" * 60)
        
        try:
            # Run system checks
            system_results = self.run_system_checks()
            
            # Test queries if system is ready
            if system_results['system_ready']:
                query_results = self.test_demo_queries()
            else:
                query_results = {'ready': False, 'error': 'System not ready'}
            
            # Generate report
            report = self.generate_demo_report(system_results, query_results)
            print(f"\n{report}")
            
            # Save report to file
            report_file = Path("demo_readiness_report.txt")
            with open(report_file, 'w') as f:
                f.write(report)
            print(f"\n📄 Report saved to: {report_file}")
            
            # Return overall readiness
            return system_results['system_ready'] and query_results.get('ready', False)
            
        except Exception as e:
            print(f"\n❌ Demo preparation failed: {e}")
            return False
        
        finally:
            if self.search_engine:
                self.search_engine.cleanup()


def main():
    """Main demo preparation function."""
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="AI Architectural Search Demo Preparation")
    parser.add_argument("--quick", action="store_true", help="Run quick checks only (skip query testing)")
    
    args = parser.parse_args()
    
    # Create preparation system
    prep = DemoPreparation()
    
    try:
        if args.quick:
            # Quick system checks only
            print("🎪 AI Architectural Search - Quick Demo Check")
            print("=" * 50)
            
            system_results = prep.run_system_checks()
            
            if system_results['system_ready']:
                print("\n✅ Quick check passed! System appears ready.")
                print("💡 Run without --quick flag for full query testing.")
            else:
                print("\n❌ Quick check failed! Address issues before demo.")
                for issue in system_results['issues']:
                    print(f"   • {issue}")
        else:
            # Full preparation
            ready = prep.run_full_preparation()
            
            if ready:
                print("\n🎉 Demo preparation complete! System is ready for presentation.")
                print("\n🚀 To start demo: python demo_startup.py")
            else:
                print("\n❌ Demo preparation failed! Address issues before presentation.")
        
    except KeyboardInterrupt:
        print("\n🛑 Demo preparation interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        if prep.search_engine:
            prep.search_engine.cleanup()


if __name__ == "__main__":
    main()