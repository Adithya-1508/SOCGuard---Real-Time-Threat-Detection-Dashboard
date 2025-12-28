import requests
import time
import json
import sys

# Known IP that usually has some OTX data (e.g., a public scanner or similar)
# Using a generic scanner IP often found in logs, or we can use 8.8.8.8 which usually has 'whitelist' or similar info, 
# but for OTX specifically we want to see if we get *any* response.
# Let's use a random IP that is likely to have some noise, or just a sample.
# 185.156.73.106 is often cited in threat lists.
TEST_IP = "185.156.73.106" 

API_URL = "http://localhost:8000/api"

def verify_otx():
    print(f"[*] Injecting event with IP: {TEST_IP}...")
    
    # 1. Send Event
    payload = {
        "source": "manual_test",
        "message": "Test event for OTX verification",
        "ip": TEST_IP,
        "user": "tester",
        "metadata": {"type": "test"}
    }
    
    try:
        resp = requests.post(f"{API_URL}/ingest", json=payload)
        if resp.status_code != 200:
            print(f"[-] Ingest failed: {resp.text}")
            sys.exit(1)
        print("[+] Event sent successfully.")
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        sys.exit(1)

    # 2. Wait for processing (Enrichment takes a moment)
    print("[*] Waiting for enrichment (5s)...")
    time.sleep(5)

    # 3. Fetch latest alert
    print("[*] Fetching latest alerts...")
    try:
        resp = requests.get(f"{API_URL}/alerts/?limit=5")
        alerts = resp.json()["items"]
        
        found = False
        for alert in alerts:
            if alert["ip"] == TEST_IP:
                found = True
                print(f"\n[+] Found Alert ID: {alert['id']}")
                print(f"    Summary: {alert['summary']}")
                print(f"    Reputation Score: {alert['reputation_score']}")
                print(f"    Threat Tags: {alert['threat_tags']}")
                
                # Check if we got tags (OTX usually returns tags for this IP)
                if alert["threat_tags"] and alert["threat_tags"] != "null":
                    print("\n[SUCCESS] OTX Enrichment verified! Tags found.")
                else:
                    print("\n[WARNING] Alert found but no tags. Check API Key or IP data.")
                break
        
        if not found:
            print("[-] Test alert not found in latest 5 items.")
            
    except Exception as e:
        print(f"[-] Failed to fetch alerts: {e}")

if __name__ == "__main__":
    verify_otx()
