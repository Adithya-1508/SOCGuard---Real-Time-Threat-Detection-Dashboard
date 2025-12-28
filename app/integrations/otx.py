import os
import httpx
from typing import Dict, List, Optional

class OTXClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OTX_API_KEY")
        self.base_url = "https://otx.alienvault.com/api/v1"
        self.headers = {
            "X-OTX-API-KEY": self.api_key,
            "Accept": "application/json"
        }

    async def get_ip_reputation(self, ip: str) -> Dict:
        """
        Query OTX for IP reputation.
        Returns a dict with 'reputation' (score) and 'tags'.
        """
        if not self.api_key:
            return {}

        if ":" in ip:
            url = f"{self.base_url}/indicators/IPv6/{ip}/general"
        else:
            url = f"{self.base_url}/indicators/IPv4/{ip}/general"
        
        def _fetch():
            import urllib.request
            import json
            req = urllib.request.Request(url)
            req.add_header("X-OTX-API-KEY", self.api_key)
            req.add_header("Accept", "application/json")
            
            print(f"[*] OTX Fetching: {url} with Key: {self.api_key[:5]}...")
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    print(f"[*] OTX Response Code: {response.getcode()}")
                    if response.getcode() == 200:
                        raw = response.read().decode()
                        # print(f"[*] OTX Raw: {raw[:100]}...")
                        return json.loads(raw)
                    else:
                        print(f"[-] OTX API Error: {response.getcode()}")
            except Exception as e:
                print(f"[-] OTX Request Failed: {e}")
            return {}

        import asyncio
        data = await asyncio.to_thread(_fetch)
        
        if data:
            pulse_info = data.get("pulse_info", {})
            count = pulse_info.get("count", 0)
            
            # Simple heuristic: more pulses = higher risk
            score = min(count * 10, 100) 
            
            tags = set()
            for pulse in pulse_info.get("pulses", []):
                for tag in pulse.get("tags", []):
                    tags.add(tag)
                    
            return {
                "reputation": score,
                "tags": list(tags)[:5] # Limit to top 5 tags
            }
            
        return {}
