import requests
import sys
import time

BASE_URL = "http://localhost:8000"

def verify_real_time():
    print("Fetching latest alerts...")
    try:
        resp = requests.get(f"{BASE_URL}/api/alerts/?limit=50")
        if resp.status_code != 200:
            print(f"Failed to fetch alerts: {resp.status_code}")
            sys.exit(1)
            
        alerts = resp.json()["items"]
        found_process = False
        found_network = False
        
        for alert in alerts:
            # print(f"Alert: {alert['summary']} ({alert['source']})")
            if alert['source'] == 'endpoint_prevention':
                found_process = True
                print(f"Found Process Alert: {alert['summary']}")
            if alert['source'] == 'network_ids':
                found_network = True
                print(f"Found Network Alert: {alert['summary']}")
                
        if found_process or found_network:
            print("SUCCESS: Found real-time alerts!")
        else:
            print("FAILURE: No real-time alerts found in the last 50 items.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Wait a moment for ingestion
    time.sleep(2)
    verify_real_time()
