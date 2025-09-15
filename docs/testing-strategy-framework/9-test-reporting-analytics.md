# **9. Test Reporting & Analytics**

## **9.1 Test Result Analysis**

```python
# scripts/analyze_test_results.py
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List
import matplotlib.pyplot as plt
import pandas as pd

class TestResultAnalyzer:
    """Analyze and report test results"""
    
    def __init__(self, results_dir: str = "test_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
    
    def analyze_junit_results(self, junit_file: str) -> Dict:
        """Analyze JUnit XML test results"""
        tree = ET.parse(junit_file)
        root = tree.getroot()
        
        results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "execution_time": 0.0,
            "test_suites": []
        }
        
        for testsuite in root.findall("testsuite"):
            suite_info = {
                "name": testsuite.get("name"),
                "tests": int(testsuite.get("tests", 0)),
                "failures": int(testsuite.get("failures", 0)),
                "errors": int(testsuite.get("errors", 0)),
                "skipped": int(testsuite.get("skipped", 0)),
                "time": float(testsuite.get("time", 0.0))
            }
            
            results["test_suites"].append(suite_info)
            results["total_tests"] += suite_info["tests"]
            results["failed_tests"] += suite_info["failures"] + suite_info["errors"]
            results["skipped_tests"] += suite_info["skipped"]
            results["execution_time"] += suite_info["time"]
        
        results["passed_tests"] = results["total_tests"] - results["failed_tests"] - results["skipped_tests"]
        
        return results
    
    def analyze_coverage_results(self, coverage_file: str) -> Dict:
        """Analyze code coverage results"""
        # Parse coverage.xml file
        tree = ET.parse(coverage_file)
        root = tree.getroot()
        
        coverage_data = {
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "packages": []
        }
        
        # Extract coverage metrics
        for package in root.findall(".//package"):
            package_info = {
                "name": package.get("name"),
                "line_rate": float(package.get("line-rate", 0.0)),
                "branch_rate": float(package.get("branch-rate", 0.0))
            }
            coverage_data["packages"].append(package_info)
        
        # Calculate overall coverage
        if coverage_data["packages"]:
            coverage_data["line_coverage"] = sum(p["line_rate"] for p in coverage_data["packages"]) / len(coverage_data["packages"])
            coverage_data["branch_coverage"] = sum(p["branch_rate"] for p in coverage_data["packages"]) / len(coverage_data["packages"])
        
        return coverage_data
    
    def generate_test_report(self, junit_file: str, coverage_file: str) -> str:
        """Generate comprehensive test report"""
        test_results = self.analyze_junit_results(junit_file)
        coverage_results = self.analyze_coverage_results(coverage_file)
        
        # Calculate success rate
        success_rate = (test_results["passed_tests"] / test_results["total_tests"]) * 100 if test_results["total_tests"] > 0 else 0
        
        report = f"""
# Test Execution Report

# Summary
- **Total Tests**: {test_results['total_tests']}
- **Passed**: {test_results['passed_tests']} ({success_rate:.1f}%)
- **Failed**: {test_results['failed_tests']}
- **Skipped**: {test_results['skipped_tests']}
- **Execution Time**: {test_results['execution_time']:.2f} seconds

# Coverage
- **Line Coverage**: {coverage_results['line_coverage']:.1%}
- **Branch Coverage**: {coverage_results['branch_coverage']:.1%}

# Test Suites
"""
        
        for suite in test_results["test_suites"]:
            suite_success_rate = ((suite["tests"] - suite["failures"] - suite["errors"]) / suite["tests"]) * 100 if suite["tests"] > 0 else 0
            report += f"""
## {suite['name']}
- Tests: {suite['tests']}
- Success Rate: {suite_success_rate:.1f}%
- Execution Time: {suite['time']:.2f}s
"""
        
        # Save report
        report_file = self.results_dir / "test_report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        return str(report_file)
    
    def create_trend_analysis(self, historical_data: List[Dict]):
        """Create test trend analysis charts"""
        df = pd.DataFrame(historical_data)
        
        # Create trend charts
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Success rate trend
        ax1.plot(df['date'], df['success_rate'])
        ax1.set_title('Test Success Rate Trend')
        ax1.set_ylabel('Success Rate (%)')
        ax1.grid(True)
        
        # Coverage trend
        ax2.plot(df['date'], df['line_coverage'], label='Line Coverage')
        ax2.plot(df['date'], df['branch_coverage'], label='Branch Coverage')
        ax2.set_title('Code Coverage Trend')
        ax2.set_ylabel('Coverage (%)')
        ax2.legend()
        ax2.grid(True)
        
        # Execution time trend
        ax3.plot(df['date'], df['execution_time'])
        ax3.set_title('Test Execution Time Trend')
        ax3.set_ylabel('Time (seconds)')
        ax3.grid(True)
        
        # Test count trend
        ax4.plot(df['date'], df['total_tests'])
        ax4.set_title('Total Tests Trend')
        ax4.set_ylabel('Number of Tests')
        ax4.grid(True)
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'test_trends.png', dpi=300, bbox_inches='tight')
        plt.close()
```

---
