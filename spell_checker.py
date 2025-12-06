"""
Spell Checker Module - NLTK-based Query Correction
Provides spelling correction and suggestions for search queries
"""

import nltk
from nltk.corpus import words
from nltk.metrics.distance import edit_distance
import string
import os

class SpellChecker:
    def __init__(self):
        """Initialize spell checker with NLTK data"""
        self.word_list = None
        self.max_suggestions = 3
        self.max_distance = 2
        
        # Download required NLTK data
        self._download_nltk_data()
        
        # Load vocabulary
        self._load_vocabulary()
    
    def _download_nltk_data(self):
        """Download required NLTK datasets"""
        try:
            # Check if already downloaded
            try:
                nltk.data.find('corpora/words.zip')
                print("✅ NLTK words corpus already available")
            except LookupError:
                print("📥 Downloading NLTK words corpus...")
                nltk.download('words', quiet=True)
                print("✅ NLTK words corpus downloaded")
        except Exception as e:
            print(f"⚠️ Warning: Could not download NLTK data: {e}")
    
    def _load_vocabulary(self):
        """Load English words vocabulary"""
        try:
            self.word_list = set(w.lower() for w in words.words())
            print(f"✅ Loaded {len(self.word_list)} English words")
        except Exception as e:
            print(f"⚠️ Warning: Could not load NLTK words: {e}")
            # Fallback to basic vocabulary
            self.word_list = set(['machine', 'learning', 'artificial', 'intelligence', 
                                  'natural', 'language', 'processing', 'neural', 'network',
                                  'deep', 'computer', 'science', 'algorithm', 'data'])
            print(f"⚠️ Using fallback vocabulary ({len(self.word_list)} words)")
    
    def add_custom_vocabulary(self, custom_words):
        """Add custom words to vocabulary (e.g., from indexed documents)"""
        if custom_words:
            self.word_list.update(w.lower() for w in custom_words if w)
            print(f"✅ Added {len(custom_words)} custom words to vocabulary")
    
    def is_correct(self, word):
        """Check if a word is spelled correctly"""
        if not word or not self.word_list:
            return True
        return word.lower() in self.word_list
    
    def get_suggestions(self, word, max_suggestions=None):
        """Get spelling suggestions for a word"""
        if not word or not self.word_list:
            return []
        
        word = word.lower()
        
        # If word is correct, no suggestions needed
        if word in self.word_list:
            return []
        
        max_suggestions = max_suggestions or self.max_suggestions
        suggestions = []
        
        # Find words with small edit distance
        for vocab_word in self.word_list:
            # Only consider words of similar length
            if abs(len(vocab_word) - len(word)) > 2:
                continue
            
            distance = edit_distance(word, vocab_word)
            if distance <= self.max_distance:
                suggestions.append((vocab_word, distance))
        
        # Sort by edit distance and return top suggestions
        suggestions.sort(key=lambda x: x[1])
        return [word for word, dist in suggestions[:max_suggestions]]
    
    def correct_word(self, word):
        """Get best correction for a single word"""
        suggestions = self.get_suggestions(word, max_suggestions=1)
        return suggestions[0] if suggestions else word
    
    def check_query(self, query):
        """
        Check entire query and return correction info
        Returns: {
            'original': str,
            'corrected': str,
            'has_errors': bool,
            'suggestions': dict,
            'misspelled_words': list
        }
        """
        if not query:
            return {
                'original': '',
                'corrected': '',
                'has_errors': False,
                'suggestions': {},
                'misspelled_words': []
            }
        
        # Clean and tokenize query
        words = query.lower().split()
        corrected_words = []
        suggestions = {}
        misspelled = []
        has_errors = False
        
        for word in words:
            # Remove punctuation
            clean_word = word.strip(string.punctuation)
            
            if not clean_word:
                corrected_words.append(word)
                continue
            
            # Check spelling
            if self.is_correct(clean_word):
                corrected_words.append(word)
            else:
                # Get suggestions
                word_suggestions = self.get_suggestions(clean_word)
                
                if word_suggestions:
                    has_errors = True
                    misspelled.append(clean_word)
                    suggestions[clean_word] = word_suggestions
                    # Use best suggestion for correction
                    corrected_words.append(word_suggestions[0])
                else:
                    # No suggestions found, keep original
                    corrected_words.append(word)
        
        return {
            'original': query,
            'corrected': ' '.join(corrected_words),
            'has_errors': has_errors,
            'suggestions': suggestions,
            'misspelled_words': misspelled
        }
    
    def correct_query(self, query):
        """Simply correct the query and return corrected version"""
        result = self.check_query(query)
        return result['corrected']


def test_spell_checker():
    """Test the spell checker"""
    print("="*80)
    print("SPELL CHECKER TEST")
    print("="*80)
    
    checker = SpellChecker()
    
    test_queries = [
        "machne lerning",
        "artifical inteligence",
        "natural languag procesing",
        "deep lerning algoritm",
        "machine learning",  # correct
        "nueral network",
        "informaton retrival"
    ]
    
    print("\nTesting queries:\n")
    for query in test_queries:
        result = checker.check_query(query)
        print(f"Original:  '{result['original']}'")
        print(f"Corrected: '{result['corrected']}'")
        if result['has_errors']:
            print(f"Errors:    {result['misspelled_words']}")
            for word, suggestions in result['suggestions'].items():
                print(f"  '{word}' → {suggestions}")
        print("-" * 40)
    
    print("\n" + "="*80)


if __name__ == "__main__":
    test_spell_checker()