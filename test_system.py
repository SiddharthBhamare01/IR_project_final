"""
Test Suite for CS-429 Information Retrieval Project
Automated tests for all system components

Usage:
    1. Start API server: python app.py
    2. Run tests: python test_system.py

Requirements:
    - Server must be running on http://127.0.0.1:5000
    - Index must be built (run indexer.py first)
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:5000"

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, passed, message=""):
    """Print test result with color"""
    if passed:
        print(f"{Colors.GREEN}✅ PASS{Colors.END}: {name}")
    else:
        print(f"{Colors.RED}❌ FAIL{Colors.END}: {name}")
        if message:
            print(f"  → {message}")

def test_health_check():
    """Test 1: System Health Check"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            passed = (
                data.get('status') == 'healthy' and
                data.get('index_ready') == True and
                data.get('spell_checker_ready') == True
            )
            print_test("Health Check", passed, 
                      f"Documents: {data.get('documents_loaded', 0)}")
            return passed
        else:
            print_test("Health Check", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_test("Health Check", False, str(e))
        return False

def test_basic_search():
    """Test 2: Basic Search Functionality"""
    try:
        data = {"query": "machine learning", "top_k": 5}
        response = requests.post(f"{BASE_URL}/query", json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            passed = (
                'results' in result and
                len(result['results']) > 0 and
                result['status'] == 'success'
            )
            print_test("Basic Search", passed, 
                      f"Found {result.get('results_count', 0)} results")
            return passed
        else:
            print_test("Basic Search", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_test("Basic Search", False, str(e))
        return False

def test_spell_checking():
    """Test 3: Spell Checking Feature (NLTK)"""
    try:
        data = {"query": "machne lerning", "top_k": 3, "auto_correct": True}
        response = requests.post(f"{BASE_URL}/query", json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            passed = (
                'spell_check' in result and
                result['spell_check']['has_spelling_errors'] == True and
                result['search_query'] != result['query']
            )
            corrected = result.get('search_query', 'N/A')
            print_test("Spell Checking", passed, 
                      f"Corrected: '{result.get('query')}' → '{corrected}'")
            return passed
        else:
            print_test("Spell Checking", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_test("Spell Checking", False, str(e))
        return False

def test_csv_output():
    """Test 4: CSV Output Format"""
    try:
        data = {"query": "artificial intelligence", "top_k": 3}
        response = requests.post(f"{BASE_URL}/query?format=csv", json=data, timeout=10)
        
        if response.status_code == 200:
            passed = (
                'text/csv' in response.headers.get('Content-Type', '') and
                'query_id' in response.text and
                'rank' in response.text
            )
            print_test("CSV Output", passed, "Valid CSV format")
            return passed
        else:
            print_test("CSV Output", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_test("CSV Output", False, str(e))
        return False

def test_spell_check_endpoint():
    """Test 5: Standalone Spell Check Endpoint"""
    try:
        data = {"query": "artifical inteligence"}
        response = requests.post(f"{BASE_URL}/spell_check", json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            passed = (
                'has_errors' in result and
                result['has_errors'] == True and
                'suggestions' in result
            )
            print_test("Spell Check Endpoint", passed, 
                      f"Corrected: '{result.get('corrected', 'N/A')}'")
            return passed
        else:
            print_test("Spell Check Endpoint", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_test("Spell Check Endpoint", False, str(e))
        return False

def test_query_validation_empty():
    """Test 6: Query Validation - Empty Query"""
    try:
        data = {"query": "", "top_k": 5}
        response = requests.post(f"{BASE_URL}/query", json=data, timeout=5)
        
        passed = response.status_code == 400
        print_test("Empty Query Validation", passed, 
                  "Correctly rejected empty query")
        return passed
    except Exception as e:
        print_test("Empty Query Validation", False, str(e))
        return False

def test_query_validation_topk():
    """Test 7: Query Validation - Invalid top_k"""
    try:
        data = {"query": "test", "top_k": 500}
        response = requests.post(f"{BASE_URL}/query", json=data, timeout=5)
        
        passed = response.status_code == 400
        print_test("Invalid top_k Validation", passed, 
                  "Correctly rejected top_k > 100")
        return passed
    except Exception as e:
        print_test("Invalid top_k Validation", False, str(e))
        return False

def test_no_auto_correct():
    """Test 8: Search Without Auto-Correction"""
    try:
        data = {"query": "machne lerning", "top_k": 3, "auto_correct": False}
        response = requests.post(f"{BASE_URL}/query", json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            passed = (
                'spell_check' in result and
                result['spell_check']['auto_corrected'] == False and
                result['search_query'] == result['query']
            )
            print_test("No Auto-Correction", passed, 
                      "Query not corrected as expected")
            return passed
        else:
            print_test("No Auto-Correction", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_test("No Auto-Correction", False, str(e))
        return False

def check_server_running():
    """Check if server is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def main():
    """Run all tests and display results"""
    print("\n" + "="*80)
    print(f"{Colors.BLUE}CS-429 INFORMATION RETRIEVAL PROJECT - TEST SUITE{Colors.END}")
    print("="*80)
    
    # Check if server is running
    print(f"\n{Colors.YELLOW}Checking server status...{Colors.END}")
    if not check_server_running():
        print(f"{Colors.RED}❌ ERROR: Cannot connect to server{Colors.END}")
        print(f"\n{Colors.YELLOW}Please start the server first:{Colors.END}")
        print("  1. python app.py")
        print("  2. Wait for 'Running on http://127.0.0.1:5000'")
        print("  3. Run this test again")
        sys.exit(1)
    
    print(f"{Colors.GREEN}✓ Server is running{Colors.END}\n")
    
    # Run all tests
    print(f"{Colors.BLUE}Running tests...{Colors.END}\n")
    
    tests = [
        ("Core Features", [
            test_health_check,
            test_basic_search,
            test_csv_output,
        ]),
        ("Optional Feature - Spell Checking (NLTK)", [
            test_spell_checking,
            test_spell_check_endpoint,
            test_no_auto_correct,
        ]),
        ("Query Validation", [
            test_query_validation_empty,
            test_query_validation_topk,
        ])
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for category, test_functions in tests:
        print(f"\n{Colors.BLUE}{category}:{Colors.END}")
        print("-" * 80)
        
        for test_func in test_functions:
            total_tests += 1
            if test_func():
                passed_tests += 1
    
    # Summary
    print("\n" + "="*80)
    print(f"{Colors.BLUE}TEST SUMMARY{Colors.END}")
    print("="*80)
    print(f"Total Tests:  {total_tests}")
    print(f"Passed:       {Colors.GREEN}{passed_tests}{Colors.END}")
    print(f"Failed:       {Colors.RED}{total_tests - passed_tests}{Colors.END}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print(f"\n{Colors.GREEN}🎉 ALL TESTS PASSED! System is working correctly.{Colors.END}\n")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}⚠️ Some tests failed. Please check the errors above.{Colors.END}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()