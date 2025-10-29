import json
from fastapi.testclient import TestClient
from src.backend.api.main import app

client = TestClient(app)

def test_ingest_and_ask():
    r = client.post('/ingest/run')
    assert r.status_code == 200
    r = client.post('/ask', json={"query": "latest arxiv", "max_facts": 5})
    assert r.status_code == 200
    data = r.json()
    assert 'answer' in data
    assert 'facts' in data
    assert isinstance(data['facts'], list)