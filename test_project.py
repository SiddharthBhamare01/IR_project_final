"""
Complete project test script.
"""

import subprocess
import sys
import time
import requests
from pathlib import Path


def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def test_crawler():
    """Test crawler"""
    print_section("TEST 1: CRAWLER")
    
    # Remove old data
    if Path("natural.txt").exists():
        Path("natural.txt").unlink()
        print("✅ Cleaned old natural.txt")
    
    print("🚀 Running crawler...")
    print("   (This will take 2-3 minutes)\n")
    
    result = subprocess.run([sys.executable, "crawler.py"], 
                          capture_output=True, text=True)
    
    if Path("natural.txt").exists():
        size = Path("natural.txt").stat().st_size
        print(f"✅ Crawler completed: natural.txt created ({size:,} bytes)")
        return True
    else:
        print("❌ Crawler failed: natural.txt not created")
        return False


def test_indexer():
    """Test indexer"""
    print_section("TEST 2: INDEXER")
    
    print("🚀 Building TF-IDF index...")
    
    result = subprocess.run([sys.executable, "indexer.py"],
                          capture_output=True, text=True)
    
    if Path("index.json").exists():
        size = Path("index.json").stat().st_size
        print(f"✅ Indexer completed: index.json created ({size:,} bytes)")
        return True
    else:
        print("❌ Indexer failed: index.json not created")
        return False


def test_api():
    """Test Flask API"""
    print_section("TEST 3: FLASK API")
    
    print("⚠️  Please start Flask API in another terminal:")
    print("   python app.py\n")
    
    print("Waiting for API to be ready...")
    
    for i in range(30):
        try:
            response = requests.get("http://127.0.0.1:5000/health", timeout=1)
            if response.status_code == 200:
                print("✅ Flask API is running")
                
                # Test query
                print("\n🧪 Testing query endpoint...")
                query_response = requests.post(
                    "http://127.0.0.1:5000/query",
                    json={"query": "natural language", "top_k": 3}
                )
                
                if query_response.status_code == 200:
                    results = query_response.json()
                    print(f"✅ Query successful: {results['results_count']} results")
                    return True
                else:
                    print(f"❌ Query failed: {query_response.status_code}")
                    return False
        except:
            time.sleep(1)
    
    print("❌ API not responding after 30 seconds")
    print("   Make sure to run: python app.py")
    return False


def main():
    print("="*80)
    print("  COMPLETE PROJECT TEST SUITE")
    print("="*80)
    print("\nThis will test all project components.\n")
    
    results = {}
    
    # Test 1: Crawler
    results['crawler'] = test_crawler()
    
    # Test 2: Indexer
    if results['crawler']:
        results['indexer'] = test_indexer()
    else:
        print("⚠️  Skipping indexer test (crawler failed)")
        results['indexer'] = False
    
    # Test 3: API
    print_section("TEST 3: FLASK API")
    print("⚠️  Manual test required")
    print("   1. Open new terminal")
    print("   2. Run: python app.py")
    print("   3. Test in Postman:")
    print("      POST http://127.0.0.1:5000/query")
    print('      Body: {"query": "language", "top_k": 5}')
    
    # Summary
    print_section("TEST SUMMARY")
    print(f"Crawler:  {'✅ PASS' if results['crawler'] else '❌ FAIL'}")
    print(f"Indexer:  {'✅ PASS' if results['indexer'] else '❌ FAIL'}")
    print(f"Flask API: ⚠️  Manual test required")
    print(f"Web UI:    ⚠️  Manual test required")
    
    if results['crawler'] and results['indexer']:
        print("\n" + "="*80)
        print("✅ ALL AUTOMATED TESTS PASSED!")
        print("="*80)
        print("\nNext steps:")
        print("  1. Terminal 1: python app.py")
        print("  2. Terminal 2: python sendrequest.py")
        print("  3. Browser: http://127.0.0.1:8080")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")


if __name__ == "__main__":
    main()