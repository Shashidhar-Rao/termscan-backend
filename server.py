from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

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

if __name__ == '__main__':
    app.run()
```
