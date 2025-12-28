import requests
import sys
import csv
import io

BASE_URL = "http://localhost:8000"

def test_export():
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

    # 2. Trigger Export
    print("Downloading CSV...")
    resp = requests.get(f"{BASE_URL}/api/alerts/export", headers=headers)
    
    if resp.status_code == 200:
        print("Download successful.")
        content = resp.text
        print(f"Content length: {len(content)} bytes")
        
        # Verify CSV structure
        f = io.StringIO(content)
        reader = csv.reader(f)
        header = next(reader)
        print(f"Header: {header}")
        
        if "ID" in header and "Summary" in header and "Reputation Score" in header:
            print("CSV Header verified.")
        else:
            print("CSV Header missing expected columns.")
            sys.exit(1)
            
        # Check for at least one row if alerts exist
        try:
            row = next(reader)
            print(f"First row: {row}")
        except StopIteration:
            print("CSV is empty (no alerts?), but header is present.")
            
    else:
        print(f"Export failed: {resp.status_code} {resp.text}")
        sys.exit(1)

if __name__ == "__main__":
    test_export()
