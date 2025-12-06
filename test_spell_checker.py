"""
Test Cases for Spell Checker Feature
Demonstrates NLTK-based query spelling correction
"""

import requests
import json

API_URL = "http://127.0.0.1:5000"

def print_separator():
    print("\n" + "="*80 + "\n")

def test_spell_check_endpoint():
    """Test the dedicated spell check endpoint"""
    print_separator()
    print("TEST 1: Spell Check Endpoint")
    print_separator()
    
    test_queries = [
        "machne lerning",
        "artifical inteligence", 
        "natural languag procesing",
        "deep lerning algoritm",
        "machine learning",  # correct
        "nueral network",
        "informaton retrival"
    ]
    
    for query in test_queries:
        try:
            response = requests.post(
                f"{API_URL}/spell_check",
                json={"query": query},
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Original:  '{result['original']}'")
                print(f"Corrected: '{result['corrected']}'")
                
                if result['has_errors']:
                    print(f"Errors:    {result['misspelled_words']}")
                    for word, suggestions in result['suggestions'].items():
                        print(f"  '{word}' → {suggestions}")
                else:
                    print("Status:    ✅ No spelling errors")
                print("-" * 80)
            else:
                print(f"❌ Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Exception: {e}")


def test_query_with_spelling():
    """Test search with automatic spell correction"""
    print_separator()
    print("TEST 2: Search with Auto-Correction")
    print_separator()
    
    # Intentionally misspelled queries
    test_queries = [
        "machne lerning algoritm",
        "artifical inteligence",
        "nueral network deep lerning"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Searching: '{query}'")
        print("-" * 80)
        
        try:
            response = requests.post(
                f"{API_URL}/query",
                json={
                    "query": query,
                    "top_k": 3,
                    "auto_correct": True
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Display spell check info
                if 'spell_check' in result:
                    spell = result['spell_check']
                    print(f"\n✏️ SPELL CHECK:")
                    print(f"   Original:  {spell['original_query']}")
                    print(f"   Corrected: {spell['corrected_query']}")
                    print(f"   Misspelled: {spell['misspelled_words']}")
                    if spell['suggestions']:
                        print(f"   Suggestions:")
                        for word, suggestions in spell['suggestions'].items():
                            print(f"     '{word}' → {suggestions}")
                
                # Display search results
                print(f"\n📊 RESULTS ({result['results_count']} found):")
                for res in result['results'][:3]:
                    print(f"   Rank {res['rank']}: Score {res['similarity_score']:.4f}")
                    print(f"   {res['content_preview'][:100]}...")
                    print()
            else:
                print(f"❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")


def test_query_without_correction():
    """Test search without auto-correction"""
    print_separator()
    print("TEST 3: Search WITHOUT Auto-Correction")
    print_separator()
    
    query = "machne lerning"
    
    print(f"🔍 Searching: '{query}' (auto_correct=False)")
    print("-" * 80)
    
    try:
        response = requests.post(
            f"{API_URL}/query",
            json={
                "query": query,
                "top_k": 3,
                "auto_correct": False
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\nOriginal Query: {result['query']}")
            print(f"Search Query:   {result['search_query']}")
            print(f"Results Found:  {result['results_count']}")
            
            if 'spell_check' in result:
                print(f"\n⚠️ Spelling errors detected but not auto-corrected")
                print(f"Suggested correction: {result['spell_check']['corrected_query']}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")


def test_health_check():
    """Test health endpoint with spell checker status"""
    print_separator()
    print("TEST 4: Health Check (Spell Checker Status)")
    print_separator()
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        
        if response.status_code == 200:
            health = response.json()
            print("System Status:")
            print(f"  Server:        {health['status']}")
            print(f"  Documents:     {health['documents_loaded']}")
            print(f"  Index:         {'✅ Ready' if health['index_ready'] else '❌ Not Ready'}")
            print(f"  Spell Checker: {'✅ Ready' if health['spell_checker_ready'] else '❌ Not Ready'}")
            print(f"  Vocabulary:    {health['vocabulary_size']:,} words")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("  SPELL CHECKER FEATURE - TEST SUITE")
    print("  Optional Feature #2: Query Spelling Correction (NLTK)")
    print("="*80)
    
    # Check if server is running
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code != 200:
            print("\n❌ ERROR: API server not responding correctly")
            print("   Please make sure app.py is running on port 5000")
            return
    except:
        print("\n❌ ERROR: Cannot connect to API server")
        print("   Please start the server: python app.py")
        return
    
    # Run tests
    test_health_check()
    test_spell_check_endpoint()
    test_query_with_spelling()
    test_query_without_correction()
    
    print_separator()
    print("✅ ALL TESTS COMPLETED!")
    print_separator()


if __name__ == "__main__":
    main()