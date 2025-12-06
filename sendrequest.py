from flask import Flask, request, render_template_string
import requests
import subprocess
import sys
import os

app = Flask(__name__)

HTML_TEMPLATE = '''
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Similarity Analysis - With Spell Check</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); padding: 40px; }
        h1 { text-align: center; color: #667eea; margin-bottom: 30px; font-size: 2.5em; }
        h2 { color: #667eea; margin-top: 30px; margin-bottom: 20px; }
        .search-box { margin-bottom: 20px; }
        input[type="text"] { width: 100%; padding: 15px; border: 2px solid #e0e0e0; border-radius: 10px; font-size: 16px; transition: all 0.3s; }
        input[type="text"]:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }
        .button-group { display: grid; grid-template-columns: 1fr; gap: 15px; margin-bottom: 30px; }
        .button-row { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        button, input[type="submit"] { padding: 15px 30px; border: none; border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; transition: all 0.3s; text-transform: uppercase; letter-spacing: 1px; }
        .btn-search { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .btn-search:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3); }
        .btn-crawl { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; }
        .btn-crawl:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(245, 87, 108, 0.3); }
        .btn-index { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; }
        .btn-index:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(79, 172, 254, 0.3); }
        
        /* Spell check notification */
        .spell-check-notice { background: #fff3cd; border-left: 5px solid #ffc107; padding: 15px 20px; border-radius: 10px; margin-bottom: 20px; }
        .spell-check-notice strong { color: #856404; }
        .corrected-query { color: #28a745; font-weight: bold; font-size: 1.1em; margin: 10px 0; }
        .misspelled-word { background: #ffebee; color: #c62828; padding: 2px 6px; border-radius: 4px; margin: 0 2px; }
        .suggestion { background: #e8f5e9; color: #2e7d32; padding: 2px 6px; border-radius: 4px; margin: 0 2px; }
        
        .results { margin-top: 30px; }
        .result-item { background: #f8f9fa; padding: 20px; margin-bottom: 15px; border-radius: 10px; border-left: 5px solid #667eea; transition: all 0.3s; }
        .result-item:hover { transform: translateX(5px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .result-rank { display: inline-block; background: #667eea; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; margin-right: 10px; }
        .result-score { display: inline-block; background: #4facfe; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
        .result-doc-id { display: inline-block; background: #95a5a6; color: white; padding: 3px 10px; border-radius: 15px; font-size: 11px; margin-left: 10px; font-family: monospace; }
        .result-content { margin-top: 15px; line-height: 1.6; color: #333; }
        .error { background: #fee; border-left: 5px solid #f44; padding: 20px; border-radius: 10px; color: #c33; margin-top: 20px; font-weight: 500; }
        .success { background: #efe; border-left: 5px solid #4a4; padding: 20px; border-radius: 10px; color: #363; margin-top: 20px; font-weight: 500; }
        .warning { background: #ffeaa7; border-left: 5px solid #fdcb6e; padding: 20px; border-radius: 10px; color: #6c5ce7; margin-top: 20px; font-weight: 500; }
        .stats { color: #666; margin: 10px 0 20px 0; font-size: 14px; }
        pre { background: #2d3436; color: #dfe6e9; padding: 15px; border-radius: 5px; overflow-x: auto; margin-top: 10px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Document Similarity Analysis</h1>
        <p style="text-align: center; color: #666; margin-bottom: 20px;">✨ Now with AI-powered spell checking!</p>
        
        <form method="post" action="/">
            <div class="button-group">
                <div class="search-box">
                    <input type="text" name="query" placeholder="Enter your search query (e.g., machine learning, artificial intelligence)..." value="{{ query or '' }}" required>
                </div>
                <input type="submit" value="🔎 Search" class="btn-search">
                <div class="button-row">
                    <button type="submit" formaction="/crawl_data" class="btn-crawl">📥 Crawl New Data</button>
                    <button type="submit" formaction="/index_data" class="btn-index">🔨 Rebuild Index</button>
                </div>
            </div>
        </form>
        
        {% if message %}
            <div class="{{ message_type or 'success' }}">{{ message|safe }}</div>
        {% endif %}
        
        <!-- Spell Check Notice -->
        {% if response_content and response_content.get('spell_check') %}
            <div class="spell-check-notice">
                <strong>✏️ Spell Check:</strong> We detected potential spelling errors in your query.<br>
                <div style="margin-top: 10px;">
                    <strong>Original:</strong> 
                    {% for word in response_content['spell_check']['misspelled_words'] %}
                        <span class="misspelled-word">{{ word }}</span>
                    {% endfor %}
                    <br>
                    <strong>Auto-corrected to:</strong>
                    <div class="corrected-query">{{ response_content['spell_check']['corrected_query'] }}</div>
                    
                    {% if response_content['spell_check']['suggestions'] %}
                        <div style="margin-top: 10px; font-size: 13px;">
                            <strong>Suggestions:</strong><br>
                            {% for word, suggestions in response_content['spell_check']['suggestions'].items() %}
                                <span class="misspelled-word">{{ word }}</span> → 
                                {% for suggestion in suggestions %}
                                    <span class="suggestion">{{ suggestion }}</span>
                                {% endfor %}
                                <br>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
            </div>
        {% endif %}
        
        {% if response_content and response_content.get('results') %}
            <div class="results">
                <h2>📊 Search Results for: "{{ response_content.get('search_query', query) }}"</h2>
                <p class="stats">Found {{ response_content.get('results_count', 0) }} results (Top {{ response_content.get('top_k', 5) }})</p>
                {% for result in response_content['results'] %}
                    <div class="result-item">
                        <div>
                            <span class="result-rank">Rank {{ result['rank'] }}</span>
                            <span class="result-score">Score: {{ "%.4f"|format(result['similarity_score']) }}</span>
                            <span class="result-doc-id">ID: {{ result['document_id'][:8] }}...</span>
                        </div>
                        <div class="result-content">
                            {{ result['content_preview'] }}
                        </div>
                    </div>
                {% endfor %}
            </div>
        {% endif %}
        
        {% if response_content and response_content.get('error') %}
            <div class="error">❌ Error: {{ response_content['error'] }}</div>
        {% endif %}
    </div>
</body>
</html>
'''


@app.route('/', methods=['GET', 'POST'])
def home():
    """Main search interface"""
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            try:
                response = requests.post(
                    'http://127.0.0.1:5000/query',
                    json={'query': query, 'top_k': 5, 'auto_correct': True},
                    timeout=10
                )
                if response.status_code == 200:
                    return render_template_string(
                        HTML_TEMPLATE,
                        response_content=response.json(),
                        query=query
                    )
                else:
                    return render_template_string(
                        HTML_TEMPLATE,
                        response_content={'error': f'API Error: {response.status_code}'},
                        query=query
                    )
            except requests.exceptions.ConnectionError:
                return render_template_string(
                    HTML_TEMPLATE,
                    message='❌ Cannot connect to API server. Make sure app.py is running on port 5000!',
                    message_type='error',
                    query=query
                )
            except Exception as e:
                return render_template_string(
                    HTML_TEMPLATE,
                    response_content={'error': str(e)},
                    query=query
                )
        else:
            return render_template_string(
                HTML_TEMPLATE,
                message='⚠️ Please enter a search query',
                message_type='warning'
            )
    return render_template_string(HTML_TEMPLATE)


@app.route('/crawl_data', methods=['POST'])
def crawl_data():
    """Crawl new data"""
    try:
        try:
            current_size = os.path.getsize('natural.txt')
            message = f'🚀 Starting crawler...<br>Current data: {current_size/1024:.1f} KB<br><br>'
        except:
            message = '🚀 Starting crawler (no existing data)...<br><br>'
        
        subprocess.Popen(
            [sys.executable, 'crawler.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        message += '✅ Crawler started in background!<br>'
        message += '⏱️ This will take 3-5 minutes for 50 pages<br>'
        message += '👀 Check the terminal running sendrequest.py for progress<br><br>'
        message += '<strong>After crawling completes:</strong><br>'
        message += '1. Click "Rebuild Index" button<br>'
        message += '2. Wait for success message<br>'
        message += '3. Restart app.py (Ctrl+C, then python app.py)<br>'
        message += '4. Try searching again'
        
        return render_template_string(
            HTML_TEMPLATE,
            message=message,
            message_type='success'
        )
    except Exception as e:
        return render_template_string(
            HTML_TEMPLATE,
            message=f'❌ Error starting crawler:<br><pre>{str(e)}</pre>',
            message_type='error'
        )


@app.route('/index_data', methods=['POST'])
def index_data():
    """Rebuild search index"""
    try:
        if not os.path.exists('natural.txt'):
            return render_template_string(
                HTML_TEMPLATE,
                message='❌ natural.txt not found!<br><br>Please click "Crawl New Data" first.',
                message_type='error'
            )
        
        file_size = os.path.getsize('natural.txt')
        if file_size < 1000:
            return render_template_string(
                HTML_TEMPLATE,
                message=f'❌ natural.txt is too small ({file_size} bytes)<br><br>Please run crawler first.',
                message_type='error'
            )
        
        print(f"🔨 Rebuilding index from natural.txt ({file_size/1024:.1f} KB)...")
        
        result = subprocess.run(
            [sys.executable, 'indexer.py'],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            if os.path.exists('index.json'):
                index_size = os.path.getsize('index.json')
                message = f'✅ Index rebuilt successfully!<br><br>'
                message += f'📊 Statistics:<br>'
                message += f'• Source data: {file_size/1024:.1f} KB<br>'
                message += f'• Index file: {index_size/1024:.1f} KB<br><br>'
                message += f'<strong>⚠️ IMPORTANT: You must restart app.py to use the new index!</strong><br><br>'
                message += f'Steps:<br>'
                message += f'1. Go to terminal running app.py<br>'
                message += f'2. Press Ctrl+C to stop<br>'
                message += f'3. Run: python app.py<br>'
                message += f'4. Come back here and search again'
                
                return render_template_string(
                    HTML_TEMPLATE,
                    message=message,
                    message_type='success'
                )
            else:
                return render_template_string(
                    HTML_TEMPLATE,
                    message=f'⚠️ Indexer ran but index.json not found<br><pre>{result.stdout}</pre>',
                    message_type='warning'
                )
        else:
            message = f'❌ Index rebuild failed!<br><br>'
            message += f'<strong>Error output:</strong><br><pre>{result.stderr}</pre><br>'
            message += f'<strong>Standard output:</strong><br><pre>{result.stdout}</pre>'
            
            return render_template_string(
                HTML_TEMPLATE,
                message=message,
                message_type='error'
            )
            
    except subprocess.TimeoutExpired:
        return render_template_string(
            HTML_TEMPLATE,
            message='⚠️ Indexing timeout (>60 seconds)<br><br>The file might be too large or there was an error.',
            message_type='warning'
        )
    except Exception as e:
        return render_template_string(
            HTML_TEMPLATE,
            message=f'❌ Error rebuilding index:<br><pre>{str(e)}</pre>',
            message_type='error'
        )


if __name__ == "__main__":
    print("\n" + "="*80)
    print("  WEB UI SERVER - WITH SPELL CHECKING")
    print("="*80)
    print("  URL: http://127.0.0.1:8080")
    print("  ⚠️  Make sure app.py is running on port 5000!")
    print("  ✨ Features: Search + Spell Check + Auto-correction")
    print("="*80 + "\n")
    
    app.run(debug=True, port=8080)