import requests
import time
import sys

# IPv6 from user report
TEST_IP = "64:ff9b::2236:546e" 

API_URL = "http://localhost:8000/api"

def verify_otx_ipv6():
    print(f"[*] Injecting event with IPv6: {TEST_IP}...")
    
    # 1. Send Event
    payload = {
        "source": "manual_test_ipv6",
        "message": "Test event for OTX IPv6 verification",
        "ip": TEST_IP,
        "user": "tester",
        "metadata": {"type": "test_ipv6"}
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

    # 2. Wait for processing
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
                print(f"    IP: {alert['ip']}")
                print(f"    Threat Tags: {alert['threat_tags']}")
                
                # Check for OTX
                if alert["threat_tags"] and alert["threat_tags"] != "null":
                    print("\n[SUCCESS] OTX Enrichment verified for IPv6!")
                else:
                    print("\n[WARNING] Alert found but no tags. Check if OTX has data for this specific IPv6.")
                break
        
        if not found:
            print("[-] Test alert not found.")
            
    except Exception as e:
        print(f"[-] Failed to fetch alerts: {e}")

if __name__ == "__main__":
    verify_otx_ipv6()
