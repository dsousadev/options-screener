from fastapi.testclient import TestClient
from services.api.main import app # Assumes PYTHONPATH is configured

client = TestClient(app)

def test_health_check():
    """Tests if the /health endpoint is reachable."""
    response = client.get("/health")
    assert response.status_code == 200
    # In a real test, we'd mock the DB connection
    assert "status" in response.json()

def test_start_screening():
    """Tests the /screen endpoint for a valid request."""
    response = client.post(
        "/screen",
        json={"tickers": ["GOOG"], "strategy": "iron_condor"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert "request_id" in data 