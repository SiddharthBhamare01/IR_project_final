"""
Flask API Server - FINAL WORKING VERSION
With Spell Checking (NLTK) - Optional Feature
"""

from flask import Flask, request, jsonify, Response
from indexer import Indexer
from spell_checker import SpellChecker
import os
import csv
from io import StringIO
import uuid

app = Flask(__name__)

# Initialize indexer and spell checker
indexer = Indexer()
spell_checker = SpellChecker()

# Load documents
file_path = os.path.join(os.path.dirname(__file__), 'natural.txt')

try:
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    documents = [doc.strip() for doc in content.split('\n\n') if doc.strip() and len(doc.strip()) > 50]
    
    if documents:
        indexer.build_index(documents)
        print(f"✅ Loaded and indexed {len(documents)} documents")
        
        # Add vocabulary from indexed documents to spell checker
        if indexer.vectorizer.vocabulary_:
            spell_checker.add_custom_vocabulary(indexer.vectorizer.vocabulary_.keys())
            print(f"✅ Enhanced spell checker with document vocabulary")
    else:
        print("⚠️ WARNING: No documents found")
        
except FileNotFoundError:
    print("❌ ERROR: natural.txt not found")


def validate_query(query):
    """Validate query input"""
    if query is None:
        return False, 'Query parameter is missing'
    if not isinstance(query, str):
        return False, 'Query must be a string'
    if not query or not query.strip():
        return False, 'Query is empty'
    if len(query.strip()) < 2:
        return False, 'Query too short'
    if len(query) > 1000:
        return False, 'Query too long'
    return True, None


@app.route('/query', methods=['POST'])
def query():
    """Handle search queries with spell checking"""
    try:
        # Parse JSON
        query_data = request.json
        if not query_data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        query_text = query_data.get('query')
        k = query_data.get('top_k', 5)
        auto_correct = query_data.get('auto_correct', True)
        
        # Validate query
        is_valid, error_message = validate_query(query_text)
        if not is_valid:
            return jsonify({'error': error_message}), 400
        
        # Validate top_k
        try:
            k = int(k)
            if k < 1 or k > 100:
                return jsonify({'error': 'top_k must be between 1 and 100'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'top_k must be an integer'}), 400
        
        # Check if index is ready
        if indexer.index is None:
            return jsonify({
                'error': 'Index not loaded. Please rebuild the index first.',
                'documents_loaded': 0,
                'status': 'index_not_ready'
            }), 503
        
        if indexer.document_count == 0:
            return jsonify({
                'error': 'No documents indexed. Please crawl data and rebuild index.',
                'documents_loaded': 0,
                'status': 'no_documents'
            }), 503
        
        # SPELL CHECKING (Optional Feature)
        spell_check_result = spell_checker.check_query(query_text)
        corrected_query = spell_check_result['corrected'] if auto_correct else query_text
        
        # Use corrected query for search if auto_correct is enabled
        search_query = corrected_query if spell_check_result['has_errors'] and auto_correct else query_text
        
        # Execute query
        try:
            doc_ids, scores = indexer.query_index(search_query, top_k=k)
        except Exception as e:
            return jsonify({
                'error': f'Query execution failed: {str(e)}',
                'query': query_text
            }), 500
        
        # Generate query UUID
        query_id = str(uuid.uuid4())
        
        # Save query to CSV
        try:
            query_exists = os.path.exists('queries.csv')
            with open('queries.csv', 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not query_exists:
                    writer.writerow(['query_id', 'query_text'])
                writer.writerow([query_id, query_text])
        except Exception as e:
            print(f"⚠️ Warning: Failed to save query to CSV: {e}")
        
        # Save results to CSV
        try:
            results_exist = os.path.exists('results.csv')
            with open('results.csv', 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not results_exist:
                    writer.writerow(['query_id', 'rank', 'document_id'])
                for rank, doc_id in enumerate(doc_ids, 1):
                    writer.writerow([query_id, rank, doc_id])
        except Exception as e:
            print(f"⚠️ Warning: Failed to save results to CSV: {e}")
        
        # Check output format
        format_param = request.args.get('format', 'json').lower()
        
        if format_param == 'csv':
            # Return CSV format
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['query_id', 'rank', 'document_id', 'similarity_score'])
            
            for rank, (doc_id, score) in enumerate(zip(doc_ids, scores), 1):
                writer.writerow([query_id, rank, doc_id, f"{score:.4f}"])
            
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=results.csv'}
            )
        else:
            # Return JSON format with spell check info
            results = []
            for rank, (doc_id, score) in enumerate(zip(doc_ids, scores), 1):
                doc_content = indexer.documents_map.get(doc_id, "")
                content_preview = doc_content[:200] if doc_content else "Content not available"
                
                results.append({
                    'rank': rank,
                    'document_id': doc_id,
                    'similarity_score': float(score),
                    'content_preview': content_preview
                })
            
            response_data = {
                'query_id': query_id,
                'query': query_text,
                'search_query': search_query,
                'top_k': k,
                'results_count': len(results),
                'results': results,
                'status': 'success'
            }
            
            # Add spell check information
            if spell_check_result['has_errors']:
                response_data['spell_check'] = {
                    'original_query': spell_check_result['original'],
                    'corrected_query': spell_check_result['corrected'],
                    'has_spelling_errors': True,
                    'misspelled_words': spell_check_result['misspelled_words'],
                    'suggestions': spell_check_result['suggestions'],
                    'auto_corrected': auto_correct
                }
            
            return jsonify(response_data), 200
    
    except Exception as e:
        print(f"❌ ERROR in /query: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Server error: {str(e)}',
            'status': 'server_error'
        }), 500


@app.route('/spell_check', methods=['POST'])
def spell_check_endpoint():
    """Dedicated endpoint for spell checking"""
    try:
        data = request.json
        if not data or 'query' not in data:
            return jsonify({'error': 'Query parameter required'}), 400
        
        query = data['query']
        result = spell_checker.check_query(query)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'documents_loaded': indexer.document_count,
        'index_ready': indexer.index is not None,
        'spell_checker_ready': spell_checker.word_list is not None,
        'vocabulary_size': len(spell_checker.word_list) if spell_checker.word_list else 0
    }), 200


if __name__ == "__main__":
    print("\n" + "="*80)
    print("  FLASK API SERVER - FINAL VERSION")
    print("="*80)
    print(f"  Documents: {indexer.document_count}")
    print(f"  Index: {'Ready' if indexer.index is not None else 'Not Ready'}")
    print(f"  Spell Checker: {'Ready' if spell_checker.word_list else 'Not Ready'}")
    print(f"  Vocabulary: {len(spell_checker.word_list) if spell_checker.word_list else 0} words")
    print(f"  Server: http://127.0.0.1:5000")
    print("="*80)
    print("\n  Features:")
    print("    ✅ TF-IDF Search (Core Requirement)")
    print("    ✅ Spell Checking (Optional Feature - NLTK)")
    print("\n  Endpoints:")
    print("    POST /query - Search with spell checking")
    print("    POST /spell_check - Check spelling only")
    print("    GET  /health - Health check")
    print("="*80 + "\n")
    
    app.run(debug=True)