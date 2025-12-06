# Document Similarity Search System

## Project Overview
Information Retrieval system using TF-IDF indexing, cosine similarity, and NLTK spell checking.

---

## Features Implemented

### Core Requirements ✅
1. **Web Crawler** (Scrapy)
   - Configurable seed URL, max pages, max depth
   - Extracts text content from HTML pages
   - Outputs to `natural.txt`

2. **Indexer** (Scikit-learn)
   - TF-IDF vectorization
   - Cosine similarity search
   - Inverted index in JSON format
   - Document UUIDs

3. **Query Processor** (Flask API)
   - Query validation and error handling
   - Top-K ranked results
   - CSV and JSON output formats
   - Generates `queries.csv` and `results.csv`

### Optional Feature ✅
- **Spell Checking** (NLTK)
  - Edit distance-based correction
  - Query suggestions
  - Auto-correction option

---

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Download NLTK Data
```bash
python -c "import nltk; nltk.download('words')"
```

---

## Usage

### Step 1: Crawl Data
```bash
python crawler.py [seed_url] [max_pages] [max_depth]

# Example:
python crawler.py https://en.wikipedia.org/wiki/Natural_language_processing 50 4
```

**Output:** `natural.txt` with extracted text content

### Step 2: Build Index
```bash
python indexer.py
```

**Output:** `index.json`, `documents_map.json`, `queries.csv`, `results.csv`

### Step 3: Start API Server
```bash
python app.py
```

Server runs on: `http://127.0.0.1:5000`

### Step 4: Start Web UI (Optional)
```bash
python sendrequest.py
```

Web interface: `http://127.0.0.1:8080`

---

## API Endpoints

### POST /query
Search documents with optional spell checking.

**Request:**
```json
{
  "query": "machine learning",
  "top_k": 5,
  "auto_correct": true
}
```

**Response (JSON):**
```json
{
  "query_id": "uuid",
  "query": "machne lerning",
  "search_query": "machine learning",
  "results": [
    {
      "rank": 1,
      "document_id": "uuid",
      "similarity_score": 0.8532,
      "content_preview": "..."
    }
  ],
  "spell_check": {
    "corrected_query": "machine learning",
    "misspelled_words": ["machne", "lerning"]
  }
}
```

**Response (CSV):** Use `?format=csv` query parameter

### POST /spell_check
Check spelling without searching.

**Request:**
```json
{
  "query": "artifical inteligence"
}
```

### GET /health
System health check.

---

## File Formats

### queries.csv
```csv
query_id,query_text
uuid1,machine learning
uuid2,artificial intelligence
```

### results.csv
```csv
query_id,rank,document_id
uuid1,1,doc_uuid1
uuid1,2,doc_uuid2
```

### index.json
```json
{
  "index": {
    "term": [
      ["doc_uuid", [positions]]
    ]
  }
}
```

---

## Testing

### Test Crawler
```bash
python crawler.py
```

### Test Indexer
```bash
python indexer.py
```

### Test Spell Checker
```bash
python spell_checker.py
```

### Test API
```bash
# Start server first
python app.py

# In another terminal:
curl -X POST http://127.0.0.1:5000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"machine learning","top_k":5}'
```

---

## Requirements

- Python 3.9+
- Flask 3.0.0
- Scrapy 2.11.0
- Scikit-learn 1.3.2
- NLTK 3.8.1
- NumPy 1.24.3
- Pandas 2.0.3

See `requirements.txt` for complete list.

---

## Project Structure

```
.
├── crawler.py           # Web crawler
├── indexer.py           # TF-IDF indexer
├── app.py               # Flask API
├── sendrequest.py       # Web UI
├── spell_checker.py     # NLTK spell checker
├── requirements.txt     # Dependencies
├── natural.txt          # Crawled data (generated)
├── index.json           # Inverted index (generated)
├── queries.csv          # Query log (generated)
└── results.csv          # Search results (generated)
```

---

## Technologies Used

- **Scrapy**: Web crawling framework
- **Scikit-learn**: TF-IDF vectorization and cosine similarity
- **Flask**: REST API server
- **NLTK**: Natural language processing and spell checking
- **NumPy**: Numerical computations
- **FAISS**: (Optional) Fast similarity search

---

## Author

[Your Name]
[Course]: CS-429 Information Retrieval
[Semester]: Fall 2024
[University]: IIT Chicago