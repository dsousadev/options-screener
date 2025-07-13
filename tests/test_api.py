from fastapi.testclient import TestClient
from services.api.main import app
from unittest.mock import patch

client = TestClient(app)

def test_health_check():
    """Tests if the /health endpoint is reachable."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()

@patch('services.api.main.q') # This decorator replaces the real queue with a mock
def test_start_screening(mock_queue):
    """
    Tests the /screen endpoint.
    Verifies it returns a success and tries to enqueue a job.
    """
    # Arrange: We can configure our mock object if needed
    # For example, to make job.get_id() work:
    mock_queue.enqueue.return_value.get_id.return_value = "mock_job_id"
    
    # Act: Call the API endpoint
    response = client.post(
        "/screen",
        json={"tickers": ["GOOG"], "strategy": "find_cheap_weeklies", "email": "test@example.com"}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["job_id"] == "mock_job_id"
    
    # Assert that our API code called the enqueue method on the queue object
    mock_queue.enqueue.assert_called_once() 