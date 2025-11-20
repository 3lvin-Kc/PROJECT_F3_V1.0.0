#!/usr/bin/env python3
"""
Test runner for persistence tests.
This script runs all persistence-related tests to verify data persistence functionality.
"""

import subprocess
import sys
import os

def run_tests():
    """Run all persistence tests."""
    print("Running Persistence Tests")
    print("=" * 50)
    
    # Change to the backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    # Test files to run
    test_files = [
        "tests/test_persistence.py",
        "tests/test_file_persistence_fix.py",
        "tests/test_frontend_hydration.py"
    ]
    
    results = []
    
    for test_file in test_files:
        print(f"\nRunning {test_file}...")
        print("-" * 30)
        
        try:
            # Run the test file
            result = subprocess.run([
                sys.executable, "-m", "pytest", test_file, "-v"
            ], capture_output=True, text=True)
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            results.append((test_file, result.returncode == 0, result.stdout, result.stderr))
            
        except Exception as e:
            print(f"Error running {test_file}: {e}")
            results.append((test_file, False, "", str(e)))
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_file, success, stdout, stderr in results:
        status = "PASSED" if success else "FAILED"
        print(f"{test_file}: {status}")
        if not success:
            failed += 1
        else:
            passed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print("\nSome tests failed. This is expected before the persistence fix is implemented.")
        print("After implementing the fix, all tests should pass.")
        return 1
    else:
        print("\nAll tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(run_tests())