import pytest
import requests
import time
import os
import uuid

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000/api")

@pytest.fixture
def mock_event():
    return {
        "source": "pytest_integration",
        "message": f"Test Event {uuid.uuid4()}",
        "ip": "1.2.3.4", # Mock IP
        "user": "test_user",
        "metadata": {"test_run": "true"}
    }

def test_health_check():
    """Verify the API is reachable."""
    try:
        # Assuming there's a docs endpoint or similar, or just check alerts list
        resp = requests.get(f"{API_URL}/alerts/?limit=1")
        assert resp.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.fail("API is not reachable. Is Docker running?")

def test_ingest_event(mock_event):
    """Test sending an event to the ingest endpoint."""
    resp = requests.post(f"{API_URL}/ingest", json=mock_event)
    assert resp.status_code == 200
    assert resp.json().get("status") == "queued"

def test_alert_processing_flow(mock_event):
    """
    End-to-End Test:
    1. Ingest a specific high-severity event.
    2. Wait for background processing.
    3. Verify it appears in the alerts list.
    """
    # Use a known malicious IP to trigger enrichment (mock or OTX)
    # And a message that triggers rule-based overrides ("Suspicious Process")
    mock_event["ip"] = "185.156.73.106" 
    mock_event["source"] = "pytest_e2e"
    mock_event["message"] = "Suspicious Process: powershell.exe execution detected"
    
    # 1. Ingest
    resp = requests.post(f"{API_URL}/ingest", json=mock_event)
    assert resp.status_code == 200
    
    # 2. Wait
    time.sleep(10) 
    
    # 3. Verify
    # Fetch alerts filter by source to find ours
    resp = requests.get(f"{API_URL}/alerts/?source=pytest_e2e&limit=5")
    assert resp.status_code == 200
    data = resp.json()
    
    items = data.get("items", [])
    found = False
    for item in items:
        if item["ip"] == mock_event["ip"]:
            found = True
            # Verify enrichment happen
            # assert item["reputation_score"] is not None
            # assert item["threat_tags"] is not None
            break
            
    assert found, "Ingested event was not found in alerts list. Processing might have failed or lagged."
