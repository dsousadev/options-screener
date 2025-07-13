#!/usr/bin/env python3
"""
Local test script that mocks database connection to test API logic.
"""

import os
import sys
import time
from unittest.mock import patch

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, ScreenerRequest
from fastapi.testclient import TestClient

# Mock the database connection for testing
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test"

client = TestClient(app)

def test_health_endpoint():
    """Test the /health endpoint with mocked database."""
    with patch('main.psycopg2.connect') as mock_connect:
        # Mock successful connection
        mock_conn = mock_connect.return_value
        mock_conn.close.return_value = None
        
        response = client.get("/health")
        print(f"Health Status Code: {response.status_code}")
        print(f"Health Response: {response.json()}")
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["database"] == "ok"
        
        print("✅ Health endpoint test passed!")

def test_screen_endpoint():
    """Test the /screen endpoint."""
    data = {
        "tickers": ["AAPL", "TSLA"],
        "strategy": "covered_call"
    }
    
    response = client.post("/screen", json=data)
    print(f"Screen Status Code: {response.status_code}")
    print(f"Screen Response: {response.json()}")
    
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert "request_id" in response.json()
    
    print("✅ Screen endpoint test passed!")

if __name__ == "__main__":
    print("Testing API endpoints with mocked database...")
    
    try:
        test_health_endpoint()
        test_screen_endpoint()
        print("\n🎉 All API tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1) 