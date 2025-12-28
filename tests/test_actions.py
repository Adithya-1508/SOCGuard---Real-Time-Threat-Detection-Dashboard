import requests
import sys

BASE_URL = "http://localhost:8000"

def test_actions():
    # 1. Login
    print("Logging in...")
    resp = requests.post(f"{BASE_URL}/auth/token", data={
        "username": "admin@example.com",
        "password": "password123"
    })
    
    if resp.status_code != 200:
        print(f"Auth failed: {resp.text}")
        sys.exit(1)
        
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Logged in.")

    # 2. Get an Alert
    resp = requests.get(f"{BASE_URL}/api/alerts/?limit=1", headers=headers)
    alerts = resp.json()["items"]
    if not alerts:
        print("No alerts found.")
        sys.exit(0)
    
    alert_id = alerts[0]["id"]
    print(f"Testing with Alert ID: {alert_id}")

    # 3. Trigger Block IP Action
    print("Triggering block_ip action...")
    resp = requests.post(f"{BASE_URL}/api/alerts/{alert_id}/actions", json={"action": "block_ip"}, headers=headers)
    
    if resp.status_code == 200:
        print("Action triggered successfully.")
        print(f"Response: {resp.json()}")
    else:
        print(f"Action failed: {resp.status_code} {resp.text}")
        sys.exit(1)

    # 4. Verify System Comment
    print("Verifying system comment...")
    resp = requests.get(f"{BASE_URL}/api/alerts/{alert_id}/comments", headers=headers)
    comments = resp.json()
    
    found = False
    for c in comments:
        if "SYSTEM ACTION: IP" in c["content"] and "blocked" in c["content"]:
            found = True
            print(f"Found system comment: {c['content']}")
            break
    
    if not found:
        print("System comment not found!")
        sys.exit(1)

if __name__ == "__main__":
    test_actions()
