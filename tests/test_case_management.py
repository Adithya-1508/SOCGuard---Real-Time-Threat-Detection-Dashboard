import requests
import sys

BASE_URL = "http://localhost:8000"

def test_case_management():
    # 1. Login to get token
    print("Logging in...")
    resp = requests.post(f"{BASE_URL}/auth/token", data={
        "username": "admin@example.com",
        "password": "password123"
    })
    
    if resp.status_code != 200:
        # Try registering if login fails
        print("Login failed, trying to register...")
        resp = requests.post(f"{BASE_URL}/auth/register", json={
            "email": "admin@example.com",
            "password": "password123",
            "full_name": "Admin User"
        })
        if resp.status_code == 200:
            print("Registered. Logging in...")
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

    # 2. Get User ID
    resp = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    user_id = resp.json()["id"]
    print(f"User ID: {user_id}")

    # 3. Get an Alert
    resp = requests.get(f"{BASE_URL}/api/alerts/?limit=1", headers=headers)
    if resp.status_code != 200:
        print(f"Get alerts failed: {resp.status_code} {resp.text}")
        sys.exit(1)
        
    alerts = resp.json()["items"]
    if not alerts:
        print("No alerts found to test with.")
        sys.exit(0)
    
    alert_id = alerts[0]["id"]
    print(f"Testing with Alert ID: {alert_id}")

    # 4. Assign Alert
    print("Assigning alert...")
    resp = requests.patch(f"{BASE_URL}/api/alerts/{alert_id}", json={"assigned_to": user_id}, headers=headers)
    if resp.status_code == 200:
        print("Alert assigned successfully.")
        assert resp.json()["assigned_to"] == user_id
    else:
        print(f"Assignment failed: {resp.text}")

    # 5. Add Comment
    print("Adding comment...")
    comment_text = "This is a test comment from the verification script."
    resp = requests.post(f"{BASE_URL}/api/alerts/{alert_id}/comments", json={"content": comment_text}, headers=headers)
    if resp.status_code == 200:
        print("Comment added successfully.")
    else:
        print(f"Add comment failed: {resp.text}")

    # 6. Get Comments
    print("Fetching comments...")
    resp = requests.get(f"{BASE_URL}/api/alerts/{alert_id}/comments", headers=headers)
    if resp.status_code == 200:
        comments = resp.json()
        print(f"Found {len(comments)} comments.")
        found = False
        for c in comments:
            if c["content"] == comment_text:
                found = True
                print(f"Verified comment: {c['content']} by {c['user_name']}")
                break
        if not found:
            print("Test comment not found in list!")
    else:
        print(f"Get comments failed: {resp.text}")

if __name__ == "__main__":
    test_case_management()
