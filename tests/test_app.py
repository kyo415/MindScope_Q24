from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import app
from prediction_service import FEATURES, QUESTIONS
import response_store

client = TestClient(app)


def complete_answers():
    return {code: 1 for code in FEATURES}


def test_page_contains_correct_research_scope_and_static_files():
    page = client.get('/')
    assert page.status_code == 200
    assert 'Bhutan, Morocco và UAE' in page.text
    assert 'Bảng câu hỏi nghiên cứu' in page.text
    assert 'phân loại thống kê' in page.text
    assert client.get('/static/css/style.css').status_code == 200
    assert client.get('/static/js/app.js').status_code == 200
    assert client.get('/static/favicon.svg').status_code == 200
    assert page.headers['Cache-Control'] == 'no-store'
    assert page.headers['X-Frame-Options'] == 'DENY'


def test_questions_model_info_and_health():
    health = client.get('/api/health').json()
    assert health['status'] == 'ok'
    assert health['models'] == ['Bhutan', 'Morocco', 'UAE']
    questions = client.get('/api/questions').json()
    assert [q['id'] for q in questions['questions']] == FEATURES
    assert len(QUESTIONS) == 10
    assert questions['retention_days'] == 30
    for country in health['models']:
        result = client.get('/api/model-info', params={'country': country})
        assert result.status_code == 200
        assert result.json()['test_rows'] > 0
    assert client.get('/api/model-info', params={'country': 'Other'}).status_code == 422


def test_all_countries_predict_without_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(response_store, 'DB_PATH', tmp_path / 'not_created.sqlite3')
    for country in ('Bhutan', 'Morocco', 'UAE'):
        response = client.post('/api/predict', json={'country': country, 'answers': complete_answers()})
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload['target'] == 'Q24'
        assert payload['predicted_code'] in (1, 2)
        assert 0 <= payload['model_score_yes'] <= 1
        assert payload['saved'] is False
        assert 'receipt' not in payload
    assert not response_store.DB_PATH.exists()
    assert client.post('/api/records/lookup', json={'receipt':'a' * 44}).status_code == 404
    assert not response_store.DB_PATH.exists()


def test_validation_missing_wrong_codes_or_bad_country():
    base = complete_answers()
    assert client.post('/api/predict', json={'country': 'Bhutan', 'answers': {'Q1': 1}}).status_code == 422
    assert client.post('/api/predict', json={'country': 'Utopia', 'answers': base}).status_code == 422
    assert client.post('/api/predict', json={'country': 'Bhutan', 'answers': {**base, 'Q24': 1}}).status_code == 422
    assert client.post('/api/predict', json={'country': 'Bhutan', 'answers': {**base, 'Q1': 99}}).status_code == 422
    assert client.post('/api/predict', json={'country': 'Bhutan', 'answers': {**base, 'Q2': True}}).status_code == 422
    assert client.post('/api/predict', json={'country': 'Bhutan', 'answers': {**base, 'Q20': 2, 'Q21': 1}}).status_code == 422
    assert client.post('/api/predict', json={'country': 'Bhutan', 'answers': {**base, 'Q20': 1, 'Q21': 2}}).status_code == 422


def test_optin_sqlite_lookup_delete(monkeypatch, tmp_path):
    db = tmp_path / 'q24_test.sqlite3'
    monkeypatch.setattr(response_store, 'DB_PATH', db)
    req = {'country': 'Bhutan', 'answers': complete_answers(), 'save_response': True}
    result = client.post('/api/predict', json=req)
    assert result.status_code == 200, result.text
    stored = result.json()
    assert stored['saved'] is True
    receipt = stored['receipt']
    assert len(receipt) > 30 and db.exists()
    assert receipt not in db.read_bytes().decode('latin-1', errors='ignore')
    lookup = client.post('/api/records/lookup', json={'receipt': receipt})
    assert lookup.status_code == 200, lookup.text
    assert lookup.json()['answers'] == complete_answers()
    assert lookup.json()['predicted_code'] == stored['predicted_code']
    assert client.post('/api/records/lookup', json={'receipt': 'x' * 45}).status_code == 404
    deleted = client.post('/api/records/delete', json={'receipt': receipt})
    assert deleted.status_code == 200
    assert deleted.json() == {'deleted': True}
    assert client.post('/api/records/lookup', json={'receipt': receipt}).status_code == 404


def test_no_raw_sensitive_content_in_health_or_model_info():
    for uri in ('/api/health', '/api/model-info?country=Bhutan'):
        body = client.get(uri).json()
        assert 'answers' not in body
        assert 'receipt' not in body


def test_embedded_theme_with_strict_csp():
    page = client.get('/')
    assert '<style id="mindscope-style">' in page.text
    assert '<script id="mindscope-script">' in page.text
    assert '.hero-orbit { display:none !important; }' in page.text
    assert 'sha256-' in page.headers['Content-Security-Policy']
    assert 'unsafe-inline' not in page.headers['Content-Security-Policy']
