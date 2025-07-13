#!/usr/bin/env python3
"""
Simple test script to verify the API endpoints work correctly.
"""

import requests
import json
import time

def test_screen_endpoint():
    """Test the /screen endpoint."""
    url = "http://localhost:8000/screen"
    data = {
        "tickers": ["AAPL", "TSLA"],
        "strategy": "covered_call"
    }
    
    try:
        response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("Could not connect to server. Make sure the API is running.")
        return False

def test_health_endpoint():
    """Test the /health endpoint."""
    url = "http://localhost:8000/health"
    
    try:
        response = requests.get(url)
        print(f"Health Status Code: {response.status_code}")
        print(f"Health Response: {response.json()}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("Could not connect to server. Make sure the API is running.")
        return False

if __name__ == "__main__":
    print("Testing API endpoints...")
    
    # Test health endpoint
    print("\n1. Testing /health endpoint:")
    health_ok = test_health_endpoint()
    
    # Test screen endpoint
    print("\n2. Testing /screen endpoint:")
    screen_ok = test_screen_endpoint()
    
    if health_ok and screen_ok:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed.") 