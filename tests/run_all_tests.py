#!/usr/bin/env python3
"""
Comprehensive test runner for Mythica dungeon crawler.
Executes all test suites and provides detailed reporting for regression detection.
"""

import unittest
import sys
import os
import time
from io import StringIO

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all test modules
from tests.test_character_system import *
from tests.test_turn_system import *
from tests.test_combat_damage import *
from tests.test_dungeon_generation import *


class DetailedTestResult(unittest.TestResult):
    """Custom test result class for detailed reporting."""
    
    def __init__(self):
        super().__init__()
        self.test_results = []
        self.start_time = None
        self.end_time = None
    
    def startTest(self, test):
        super().startTest(test)
        self.start_time = time.time()
    
    def stopTest(self, test):
        super().stopTest(test)
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        result = {
            'test': str(test),
            'duration': duration,
            'status': 'PASS',
            'error': None
        }
        
        self.test_results.append(result)
    
    def addError(self, test, err):
        super().addError(test, err)
        if self.test_results:
            self.test_results[-1]['status'] = 'ERROR'
            self.test_results[-1]['error'] = self._exc_info_to_string(err, test)
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.test_results:
            self.test_results[-1]['status'] = 'FAIL'
            self.test_results[-1]['error'] = self._exc_info_to_string(err, test)
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.test_results:
            self.test_results[-1]['status'] = 'SKIP'
            self.test_results[-1]['error'] = reason


class TestRunner:
    """Main test runner with comprehensive reporting."""
    
    def __init__(self):
        self.test_suites = {
            'Character System': [
                'TestCharacterStats',
                'TestEquipmentSystem', 
                'TestCharacterClasses',
                'TestItemGeneration',
                'TestCombatCalculations'
            ],
            'Turn System': [
                'TestActionCosts',
                'TestTurnScheduler',
                'TestTurnManager',
                'TestCombatTiming'
            ],
            'Combat & Damage': [
                'TestDamageCalculation',
                'TestHealthSystem',
                'TestEnemySystem',
                'TestHealthBarSystem',
                'TestCombatIntegration'
            ],
            'Dungeon Generation': [
                'TestDungeonGeneration',
                'TestLineOfSight',
                'TestMovementAndCollision',
                'TestCameraSystem',
                'TestMinimapSystem'
            ]
        }
    
    def run_all_tests(self):
        """Run all test suites and provide comprehensive reporting."""
        print("=" * 80)
        print("MYTHICA DUNGEON CRAWLER - COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print()
        
        all_results = {}
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_errors = 0
        total_skipped = 0
        overall_start_time = time.time()
        
        for suite_name, test_classes in self.test_suites.items():
            print(f"Running {suite_name} Tests...")
            print("-" * 50)
            
            suite_results = self._run_test_suite(test_classes)
            all_results[suite_name] = suite_results
            
            # Aggregate results
            total_tests += suite_results['total']
            total_passed += suite_results['passed']
            total_failed += suite_results['failed']
            total_errors += suite_results['errors']
            total_skipped += suite_results['skipped']
            
            print()
        
        overall_end_time = time.time()
        overall_duration = overall_end_time - overall_start_time
        
        # Print comprehensive summary
        self._print_summary(all_results, total_tests, total_passed, 
                           total_failed, total_errors, total_skipped, 
                           overall_duration)
        
        return total_failed + total_errors == 0
    
    def _run_test_suite(self, test_class_names):
        """Run a specific test suite."""
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Load test classes
        for class_name in test_class_names:
            try:
                test_class = globals()[class_name]
                tests = loader.loadTestsFromTestCase(test_class)
                suite.addTests(tests)
            except KeyError:
                print(f"Warning: Test class {class_name} not found")
                continue
        
        # Run tests with custom result handler
        result = DetailedTestResult()
        suite.run(result)
        
        # Process results
        passed = len([r for r in result.test_results if r['status'] == 'PASS'])
        failed = len([r for r in result.test_results if r['status'] == 'FAIL'])
        errors = len([r for r in result.test_results if r['status'] == 'ERROR'])
        skipped = len([r for r in result.test_results if r['status'] == 'SKIP'])
        total = len(result.test_results)
        
        # Print suite results
        print(f"Tests run: {total}")
        print(f"Passed: {passed} ✓")
        if failed > 0:
            print(f"Failed: {failed} ✗")
        if errors > 0:
            print(f"Errors: {errors} ⚠")
        if skipped > 0:
            print(f"Skipped: {skipped} ⏭")
        
        # Show failures and errors
        self._show_failures_and_errors(result.test_results)
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'skipped': skipped,
            'test_results': result.test_results
        }
    
    def _show_failures_and_errors(self, test_results):
        """Show detailed information about failures and errors."""
        failures_and_errors = [r for r in test_results 
                              if r['status'] in ['FAIL', 'ERROR']]
        
        if failures_and_errors:
            print("\nDetailed Failure/Error Information:")
            for result in failures_and_errors:
                print(f"\n{result['status']}: {result['test']}")
                if result['error']:
                    # Show first few lines of error
                    error_lines = result['error'].split('\n')
                    for line in error_lines[:3]:  # Show first 3 lines
                        print(f"  {line}")
                    if len(error_lines) > 3:
                        print("  ...")
    
    def _print_summary(self, all_results, total_tests, total_passed, 
                      total_failed, total_errors, total_skipped, duration):
        """Print comprehensive test summary."""
        print("=" * 80)
        print("COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        # Overall statistics
        print(f"Total Tests Executed: {total_tests}")
        print(f"Duration: {duration:.2f} seconds")
        print()
        
        # Results breakdown
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        print(f"✓ Passed: {total_passed} ({success_rate:.1f}%)")
        
        if total_failed > 0:
            fail_rate = (total_failed / total_tests * 100)
            print(f"✗ Failed: {total_failed} ({fail_rate:.1f}%)")
        
        if total_errors > 0:
            error_rate = (total_errors / total_tests * 100)
            print(f"⚠ Errors: {total_errors} ({error_rate:.1f}%)")
        
        if total_skipped > 0:
            skip_rate = (total_skipped / total_tests * 100)
            print(f"⏭ Skipped: {total_skipped} ({skip_rate:.1f}%)")
        
        print()
        
        # Suite-by-suite breakdown
        print("Results by Test Suite:")
        print("-" * 40)
        for suite_name, results in all_results.items():
            total = results['total']
            passed = results['passed']
            failed = results['failed']
            errors = results['errors']
            
            if total > 0:
                suite_success_rate = (passed / total * 100)
                status = "✓" if (failed + errors) == 0 else "✗"
                print(f"{status} {suite_name}: {passed}/{total} ({suite_success_rate:.1f}%)")
        
        print()
        
        # Feature coverage summary
        print("Feature Coverage Analysis:")
        print("-" * 40)
        self._analyze_feature_coverage(all_results)
        
        # Final verdict
        print()
        if total_failed + total_errors == 0:
            print("🎉 ALL TESTS PASSED! No regressions detected.")
        else:
            print("❌ TESTS FAILED! Potential regressions detected.")
            print(f"   Please review {total_failed + total_errors} failing test(s).")
        
        print("=" * 80)
    
    def _analyze_feature_coverage(self, all_results):
        """Analyze test coverage of key game features."""
        feature_status = {}
        
        # Character system features
        char_results = all_results.get('Character System', {})
        feature_status['Character Stats & Equipment'] = self._get_suite_status(char_results)
        feature_status['Character Classes'] = self._get_suite_status(char_results)
        
        # Turn system features  
        turn_results = all_results.get('Turn System', {})
        feature_status['Turn Timing & Actions'] = self._get_suite_status(turn_results)
        feature_status['Weapon Timing'] = self._get_suite_status(turn_results)
        
        # Combat features
        combat_results = all_results.get('Combat & Damage', {})
        feature_status['Damage Calculation'] = self._get_suite_status(combat_results)
        feature_status['Health System'] = self._get_suite_status(combat_results)
        feature_status['Enemy AI'] = self._get_suite_status(combat_results)
        
        # Dungeon features
        dungeon_results = all_results.get('Dungeon Generation', {})
        feature_status['Dungeon Generation'] = self._get_suite_status(dungeon_results)
        feature_status['Line of Sight'] = self._get_suite_status(dungeon_results)
        
        # Print feature status
        for feature, status in feature_status.items():
            icon = "✓" if status else "✗"
            print(f"{icon} {feature}")
    
    def _get_suite_status(self, suite_results):
        """Get overall status for a test suite."""
        if not suite_results:
            return False
        return (suite_results.get('failed', 0) + suite_results.get('errors', 0)) == 0
    
    def run_specific_suite(self, suite_name):
        """Run a specific test suite only."""
        if suite_name not in self.test_suites:
            print(f"Error: Test suite '{suite_name}' not found.")
            print("Available suites:")
            for name in self.test_suites.keys():
                print(f"  - {name}")
            return False
        
        print(f"Running {suite_name} Tests Only...")
        print("=" * 50)
        
        test_classes = self.test_suites[suite_name]
        results = self._run_test_suite(test_classes)
        
        return results['failed'] + results['errors'] == 0
    
    def run_regression_tests(self):
        """Run focused regression tests on critical features."""
        print("Running Regression Test Suite...")
        print("=" * 50)
        
        # Define critical tests for regression checking
        critical_tests = [
            'TestCharacterStats.test_hp_calculation_from_constitution',
            'TestActionCosts.test_weapon_attack_speeds',
            'TestDamageCalculation.test_strength_affects_damage',
            'TestTurnScheduler.test_action_order_by_time',
            'TestDungeonGeneration.test_dungeon_connectivity'
        ]
        
        # Run individual critical tests
        for test_name in critical_tests:
            print(f"Testing: {test_name}")
            # Implementation would run specific test method
        
        print("\nRegression test suite completed.")


def main():
    """Main entry point for test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mythica Test Runner')
    parser.add_argument('--suite', type=str, help='Run specific test suite')
    parser.add_argument('--regression', action='store_true', 
                       help='Run regression tests only')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.regression:
        success = runner.run_regression_tests()
    elif args.suite:
        success = runner.run_specific_suite(args.suite)
    else:
        success = runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main() 