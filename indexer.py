"""
TF-IDF Indexer - FIXED VERSION with proper encoding
Creates inverted index in the exact format specified.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import numpy as np
import uuid
from collections import defaultdict


class Indexer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            min_df=1,
            max_df=0.8,
            ngram_range=(1, 2),
            stop_words='english'
        )
        self.index = None
        self.document_count = 0
        self.document_ids = []  # Store UUIDs
        self.documents_map = {}  # Map UUID to content
        self.inverted_index = {}  # Professor's format

    def build_index(self, documents):
        """Build TF-IDF index and inverted index"""
        if not documents or len(documents) == 0:
            raise ValueError("No documents to index")
        
        documents = [doc.strip() for doc in documents if doc.strip()]
        self.document_count = len(documents)
        
        # Generate UUIDs for each document
        self.document_ids = [str(uuid.uuid4()) for _ in range(self.document_count)]
        self.documents_map = {doc_id: doc for doc_id, doc in zip(self.document_ids, documents)}
        
        # Build TF-IDF matrix
        self.index = self.vectorizer.fit_transform(documents)
        
        # Build inverted index in professor's format
        self._build_inverted_index(documents)
        
        print(f"Index built: {self.document_count} documents")
        print(f"Vocabulary size: {len(self.vectorizer.vocabulary_)}")

    def _build_inverted_index(self, documents):
        """Build inverted index: term -> [(doc_uuid, [positions])]"""
        self.inverted_index = defaultdict(list)
        
        for doc_idx, document in enumerate(documents):
            doc_uuid = self.document_ids[doc_idx]
            
            # Tokenize document - handle encoding properly
            try:
                words = document.lower().split()
            except:
                # If encoding issues, use ASCII only
                words = document.encode('ascii', 'ignore').decode('ascii').lower().split()
            
            # Track word positions
            word_positions = defaultdict(list)
            for pos, word in enumerate(words):
                # Clean word - keep only alphanumeric
                word = ''.join(c for c in word if c.isalnum())
                if word and len(word) > 2:  # Skip short words
                    word_positions[word].append(pos)
            
            # Add to inverted index
            for word, positions in word_positions.items():
                self.inverted_index[word].append((doc_uuid, positions))

    def save_index(self, filename='index.json'):
        """Save index in pure JSON format - FIXED ENCODING"""
        if self.index is None:
            raise ValueError("Index not built yet")
        
        print(f"Saving index...")
        
        # Convert inverted index to serializable format
        index_data = {
            'index': {
                term: [(doc_id, positions) for doc_id, positions in postings]
                for term, postings in self.inverted_index.items()
            }
        }
        
        # Save as PURE JSON with proper UTF-8 encoding
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=4, ensure_ascii=False)
            print(f"✅ Index saved: {filename}")
        except Exception as e:
            print(f"❌ Error saving index: {e}")
            # Fallback: save with ASCII encoding only
            print("Attempting ASCII-only save...")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=4, ensure_ascii=True)
            print(f"✅ Index saved (ASCII): {filename}")
        
        # Save document mapping separately
        try:
            with open('documents_map.json', 'w', encoding='utf-8') as f:
                json.dump(self.documents_map, f, indent=2, ensure_ascii=False)
            print(f"✅ Documents map saved: documents_map.json")
        except Exception as e:
            print(f"❌ Error saving documents map: {e}")
            # Fallback: save with ASCII encoding
            print("Attempting ASCII-only save...")
            with open('documents_map.json', 'w', encoding='utf-8') as f:
                json.dump(self.documents_map, f, indent=2, ensure_ascii=True)
            print(f"✅ Documents map saved (ASCII): documents_map.json")
        
        print(f"   Total terms: {len(self.inverted_index)}")
        print(f"   Total documents: {self.document_count}")

    def load_index(self, filename='index.json'):
        """Load index from pure JSON file"""
        try:
            # Load inverted index with UTF-8 encoding
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.inverted_index = data.get('index', data)
            
            # Load documents map
            with open('documents_map.json', 'r', encoding='utf-8') as f:
                self.documents_map = json.load(f)
            
            self.document_ids = list(self.documents_map.keys())
            self.document_count = len(self.document_ids)
            
            # Rebuild TF-IDF from documents
            documents = [self.documents_map[doc_id] for doc_id in self.document_ids]
            self.index = self.vectorizer.fit_transform(documents)
            
            print(f"✅ Index loaded: {self.document_count} documents")
            print(f"   Total terms: {len(self.inverted_index)}")
            
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Index file not found: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in index file: {e}")
        except Exception as e:
            raise Exception(f"Error loading index: {e}")

    def query_index(self, query, top_k=5):
        """Query the index and return top-K similar documents"""
        if self.index is None:
            raise ValueError("Index not loaded")
        
        # Get document contents in order
        documents = [self.documents_map[doc_id] for doc_id in self.document_ids]
        
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.index)[0]
        
        # Get top-K indices
        top_indices = similarities.argsort()[::-1][:top_k]
        
        # Return document UUIDs instead of indices
        top_doc_ids = [self.document_ids[idx] for idx in top_indices]
        top_scores = similarities[top_indices]
        
        return top_doc_ids, top_scores


def main():
    """Test the indexer"""
    print("="*80)
    print("TF-IDF INDEXER - PROFESSOR'S FORMAT")
    print("="*80)
    print()
    
    indexer = Indexer()
    
    # Load documents
    try:
        with open('natural.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        documents = [doc.strip() for doc in content.split('\n\n') if doc.strip() and len(doc.strip()) > 50]
        
        if not documents:
            print("ERROR: No valid documents found")
            return
        
        print(f"Loaded {len(documents)} documents\n")
        
    except FileNotFoundError:
        print("ERROR: natural.txt not found")
        return
    except Exception as e:
        print(f"ERROR loading documents: {e}")
        return
    
    # Build index
    print("Building index...")
    try:
        indexer.build_index(documents)
    except Exception as e:
        print(f"ERROR building index: {e}")
        return
    
    # Save index
    print("\nSaving index...")
    try:
        indexer.save_index('index.json')
    except Exception as e:
        print(f"ERROR saving index: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test queries
    print("\n" + "="*80)
    print("TESTING QUERIES")
    print("="*80 + "\n")
    
    test_queries = [
        ('information overload', str(uuid.uuid4())),
        ('machine learning', str(uuid.uuid4())),
        ('artificial intelligence', str(uuid.uuid4()))
    ]
    
    # Save queries to CSV
    import csv
    try:
        with open('queries.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['query_id', 'query_text'])
            for query_text, query_id in test_queries:
                writer.writerow([query_id, query_text])
        
        print("Saved queries.csv")
    except Exception as e:
        print(f"Warning: Could not save queries.csv: {e}")
    
    # Process queries and save results
    try:
        with open('results.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['query_id', 'rank', 'document_id'])
            
            for query_text, query_id in test_queries:
                print(f"Query: '{query_text}'")
                print("-" * 40)
                
                doc_ids, scores = indexer.query_index(query_text, top_k=3)
                
                for rank, (doc_id, score) in enumerate(zip(doc_ids, scores), 1):
                    writer.writerow([query_id, rank, doc_id])
                    preview = indexer.documents_map[doc_id][:80]
                    print(f"{rank}. [{score:.4f}] {preview}...")
                print()
        
        print("Saved results.csv")
    except Exception as e:
        print(f"Warning: Could not save results.csv: {e}")
    
    print("\n" + "="*80)
    print("COMPLETED!")
    print("="*80)


if __name__ == "__main__":
    main()