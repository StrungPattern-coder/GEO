#!/usr/bin/env python3
"""
Test the /ask/stream endpoint directly to debug output
"""

import requests
import json

url = "http://localhost:8000/ask/stream"
data = {"query": "What is 2+2?", "max_facts": 5}

print("🧪 Testing /ask/stream endpoint...")
print(f"Query: {data['query']}")
print("="*60)

try:
    response = requests.post(url, json=data, stream=True)
    print(f"Status: {response.status_code}")
    print("="*60)
    print("Stream output:")
    print("-"*60)
    
    for i, chunk in enumerate(response.iter_content(chunk_size=None, decode_unicode=True)):
        if chunk:
            print(f"Chunk {i}: {repr(chunk)}")
    
    print("-"*60)
    print("✅ Stream complete")
    
except Exception as e:
    print(f"❌ Error: {e}")
