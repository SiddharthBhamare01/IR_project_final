"""
Semantic Search Module - Word2Vec + FAISS
Provides neural/semantic similarity search using vector embeddings
"""

import numpy as np
import faiss
from gensim.models import Word2Vec
from gensim.utils import simple_preprocess
import pickle
import os


class SemanticSearchEngine:
    def __init__(self, vector_size=100, min_count=1, workers=4):
        """Initialize semantic search engine"""
        self.vector_size = vector_size
        self.min_count = min_count
        self.workers = workers
        
        self.word2vec_model = None
        self.document_vectors = None
        self.faiss_index = None
        self.document_ids = []
        
        print(f"✅ Semantic Search Engine initialized (vector_size={vector_size})")
    
    def _preprocess_text(self, text):
        """Tokenize and preprocess text"""
        return simple_preprocess(text, deacc=True)
    
    def _document_to_vector(self, tokens):
        """Convert document tokens to vector using Word2Vec"""
        vectors = []
        for token in tokens:
            if token in self.word2vec_model.wv:
                vectors.append(self.word2vec_model.wv[token])
        
        if vectors:
            # Average of word vectors
            return np.mean(vectors, axis=0)
        else:
            # Return zero vector if no words found
            return np.zeros(self.vector_size)
    
    def train(self, documents, document_ids):
        """Train Word2Vec model and build FAISS index"""
        if not documents:
            raise ValueError("No documents to train on")
        
        print(f"\n{'='*80}")
        print("TRAINING SEMANTIC SEARCH ENGINE")
        print(f"{'='*80}")
        
        # Preprocess documents
        print("Preprocessing documents...")
        tokenized_docs = [self._preprocess_text(doc) for doc in documents]
        
        # Train Word2Vec
        print(f"Training Word2Vec model (vector_size={self.vector_size})...")
        self.word2vec_model = Word2Vec(
            sentences=tokenized_docs,
            vector_size=self.vector_size,
            window=5,
            min_count=self.min_count,
            workers=self.workers,
            epochs=10,
            sg=1  # Skip-gram model
        )
        
        vocab_size = len(self.word2vec_model.wv)
        print(f"✅ Word2Vec trained: {vocab_size} words in vocabulary")
        
        # Convert documents to vectors
        print("Converting documents to vectors...")
        self.document_vectors = np.array([
            self._document_to_vector(tokens) 
            for tokens in tokenized_docs
        ]).astype('float32')
        
        self.document_ids = document_ids
        
        # Build FAISS index
        print(f"Building FAISS index ({len(documents)} documents)...")
        dimension = self.document_vectors.shape[1]
        
        # Use L2 (Euclidean) distance
        self.faiss_index = faiss.IndexFlatL2(dimension)
        self.faiss_index.add(self.document_vectors)
        
        print(f"✅ FAISS index built: {self.faiss_index.ntotal} vectors indexed")
        print(f"{'='*80}\n")
    
    def search(self, query, top_k=5):
        """Search using semantic similarity"""
        if self.faiss_index is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Preprocess and vectorize query
        query_tokens = self._preprocess_text(query)
        query_vector = self._document_to_vector(query_tokens).reshape(1, -1).astype('float32')
        
        # Search in FAISS
        distances, indices = self.faiss_index.search(query_vector, top_k)
        
        # Convert distances to similarity scores (inverse)
        # Lower distance = higher similarity
        similarities = 1.0 / (1.0 + distances[0])
        
        # Get document IDs
        doc_ids = [self.document_ids[idx] for idx in indices[0]]
        
        return doc_ids, similarities
    
    def get_word_similarity(self, word1, word2):
        """Get similarity between two words"""
        if self.word2vec_model is None:
            return 0.0
        
        try:
            return self.word2vec_model.wv.similarity(word1, word2)
        except KeyError:
            return 0.0
    
    def get_similar_words(self, word, top_n=5):
        """Get similar words using Word2Vec"""
        if self.word2vec_model is None:
            return []
        
        try:
            similar = self.word2vec_model.wv.most_similar(word, topn=top_n)
            return [(w, float(score)) for w, score in similar]
        except KeyError:
            return []
    
    def save_model(self, directory='semantic_models'):
        """Save Word2Vec model and FAISS index"""
        os.makedirs(directory, exist_ok=True)
        
        # Save Word2Vec
        w2v_path = os.path.join(directory, 'word2vec.model')
        self.word2vec_model.save(w2v_path)
        
        # Save FAISS index
        faiss_path = os.path.join(directory, 'faiss.index')
        faiss.write_index(self.faiss_index, faiss_path)
        
        # Save document IDs and vectors
        metadata_path = os.path.join(directory, 'metadata.pkl')
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'document_ids': self.document_ids,
                'document_vectors': self.document_vectors,
                'vector_size': self.vector_size
            }, f)
        
        print(f"✅ Model saved to: {directory}/")
    
    def load_model(self, directory='semantic_models'):
        """Load Word2Vec model and FAISS index"""
        # Load Word2Vec
        w2v_path = os.path.join(directory, 'word2vec.model')
        self.word2vec_model = Word2Vec.load(w2v_path)
        
        # Load FAISS index
        faiss_path = os.path.join(directory, 'faiss.index')
        self.faiss_index = faiss.read_index(faiss_path)
        
        # Load metadata
        metadata_path = os.path.join(directory, 'metadata.pkl')
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
            self.document_ids = metadata['document_ids']
            self.document_vectors = metadata['document_vectors']
            self.vector_size = metadata['vector_size']
        
        print(f"✅ Model loaded from: {directory}/")
        print(f"   Vocabulary: {len(self.word2vec_model.wv)} words")
        print(f"   Documents: {self.faiss_index.ntotal} vectors")


def test_semantic_search():
    """Test the semantic search engine"""
    print("\n" + "="*80)
    print("SEMANTIC SEARCH ENGINE TEST")
    print("="*80 + "\n")
    
    # Sample documents
    documents = [
        "Machine learning is a subset of artificial intelligence",
        "Deep learning uses neural networks with multiple layers",
        "Natural language processing helps computers understand text",
        "Computer vision enables machines to interpret images",
        "Reinforcement learning trains agents through rewards",
        "Supervised learning requires labeled training data",
        "Unsupervised learning finds patterns without labels",
        "Neural networks are inspired by biological neurons"
    ]
    
    doc_ids = [f"doc_{i}" for i in range(len(documents))]
    
    # Initialize and train
    engine = SemanticSearchEngine(vector_size=50)
    engine.train(documents, doc_ids)
    
    # Test queries
    test_queries = [
        "artificial intelligence algorithms",
        "image recognition systems",
        "training AI models"
    ]
    
    print("\nTest Queries:\n")
    for query in test_queries:
        print(f"Query: '{query}'")
        print("-" * 60)
        
        doc_ids_result, scores = engine.search(query, top_k=3)
        
        for rank, (doc_id, score) in enumerate(zip(doc_ids_result, scores), 1):
            doc_idx = int(doc_id.split('_')[1])
            print(f"{rank}. [{score:.4f}] {documents[doc_idx]}")
        print()
    
    # Test word similarity
    print("\nWord Similarity Tests:\n")
    word_pairs = [
        ("machine", "learning"),
        ("neural", "network"),
        ("supervised", "unsupervised")
    ]
    
    for word1, word2 in word_pairs:
        similarity = engine.get_word_similarity(word1, word2)
        print(f"'{word1}' <-> '{word2}': {similarity:.4f}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    test_semantic_search()