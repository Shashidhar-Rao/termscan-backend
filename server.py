import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
SUPABASE_URL = 'https://fddtzrimuuwpbheqyvit.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZkZHR6cmltdXV3cGJoZXF5dml0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ4OTMyNjksImV4cCI6MjA5MDQ2OTI2OX0.U_4V8N42D3ikBOY83TOfSly24cXw8vAPnec5XmMWkGw'

def save_scan(company_name, fairness_score, verdict, input_type):
    try:
        requests.post(
            f'{SUPABASE_URL}/rest/v1/scans',
            headers={
                'apikey': SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'company_name': company_name,
                'fairness_score': fairness_score,
                'verdict': verdict,
                'input_type': input_type
            },
            timeout=5
        )
    except Exception as e:
        print(f'Supabase save error: {e}')

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

@app.route('/save-scan', methods=['POST'])
def save_scan_route():
    try:
        data = request.json
        save_scan(
            data.get('company_name', 'Unknown'),
            data.get('fairness_score', 0),
            data.get('verdict', 'warn'),
            data.get('input_type', 'paste')
        )
        return jsonify({ 'success': True })
    except Exception as e:
        return jsonify({ 'error': str(e) }), 500

@app.route('/stats', methods=['GET'])
def stats():
    try:
        res = requests.get(
            f'{SUPABASE_URL}/rest/v1/scans?select=*&order=scan_date.desc',
            headers={
                'apikey': SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}'
            },
            timeout=10
        )
        scans = res.json()
        total = len(scans)
        companies = {}
        for s in scans:
            name = s.get('company_name', 'Unknown')
            companies[name] = companies.get(name, 0) + 1
        top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:10]
        avg_score = round(sum(s.get('fairness_score', 0) for s in scans) / total) if total else 0
        return jsonify({
            'total_scans': total,
            'avg_score': avg_score,
            'top_companies': top_companies,
            'recent': scans[:5]
        })
    except Exception as e:
        return jsonify({ 'error': str(e) }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
