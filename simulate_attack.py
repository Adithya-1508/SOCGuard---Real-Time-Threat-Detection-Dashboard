import asyncio
import aiohttp
import random
import time

API_URL = "http://localhost:8000/api/ingest"

async def send_attack():
    async with aiohttp.ClientSession() as session:
        print("🚀 [ATTACK] initiating distributed brute-force simulation...")
        
        # 5 distinct attacks from different "IPs" to scatter hits on the map
        attacks = [
            {"ip": "192.168.1.105", "source": "Firewall", "message": "Suspicious Process: powershell.exe -enc payload"},
            {"ip": "45.33.22.11", "source": "IDS", "message": "SQL Injection Attempt: UNION SELECT 1,2,3"},
            {"ip": "103.21.244.0", "source": "WAF", "message": "XSS Attack Detected: <script>alert(1)</script>"},
            {"ip": "185.100.84.91", "source": "Endpoint", "message": "Malware detected: Ransomware.WannaCry"},
            {"ip": "203.0.113.42", "source": "Network", "message": "Port Scan Detected from external IP"},
        ]

        for i, attack in enumerate(attacks):
            payload = {
                "source": attack["source"],
                "message": attack["message"],
                "ip": attack["ip"]
            }
            try:
                async with session.post(API_URL, json=payload) as resp:
                    if resp.status == 202:
                        print(f"💥 [HIT {i+1}/5] Sent threat from {attack['ip']} ({attack['source']})")
                    else:
                        print(f"❌ Failed to send: {resp.status}")
            except Exception as e:
                print(f"❌ Connection Error: {e}")
            
            # Small delay to let the user see each "ping" on the map
            await asyncio.sleep(1.5) 

        print("\n✅ Simulation Complete. Check Dashboard!")

if __name__ == "__main__":
    asyncio.run(send_attack())
