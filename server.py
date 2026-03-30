import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

@app.route('/fetch-terms', methods=['POST'])
def fetch_terms():
    url = request.json.get('url')
    try:
        res = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        for tag in soup(['script','style','nav','footer','header']):
            tag.decompose()
        text = soup.get_text(separator='\n', strip=True)
        return jsonify({ 'text': text[:8000] })
    except Exception as e:
        return jsonify({ 'error': str(e) }), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        messages = data.get('messages', [])
        system = data.get('system', '')
        res = requests.post('https://api.anthropic.com/v1/messages', 
            headers={
                'Content-Type': 'application/json',
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01'
            },
            json={
                'model': 'claude-sonnet-4-20250514',
                'max_tokens': 1000,
                'system': system,
                'messages': messages
            },
            timeout=60
        )
        return jsonify(res.json())
    except Exception as e:
        return jsonify({ 'error': str(e) }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
