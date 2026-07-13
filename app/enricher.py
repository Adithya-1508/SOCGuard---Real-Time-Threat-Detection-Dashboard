# app/enricher.py
import httpx
import os
from typing import Dict

# Example: AbuseIPDB enrichment stub
ABUSE_API_KEY = os.getenv("ABUSEIPDB_KEY", "")

async def enrich_ip(ip: str) -> Dict:
    """Call threat-intel providers; return enrichment dict."""
    out = {"ip": ip, "reputation": None, "blacklists": []}
    if not ip:
        return out

    # Pluggable architecture: attempt AbuseIPDB then others.
    if ABUSE_API_KEY:
        try:
            url = "https://api.abuseipdb.com/api/v2/check"
            params = {"ipAddress": ip}
            headers = {"Key": ABUSE_API_KEY, "Accept": "application/json"}
            async with httpx.AsyncClient(timeout=8) as client:
                r = await client.get(url, params=params, headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    # map to simple fields
                    out["reputation"] = data.get("data", {}).get("abuseConfidenceScore")
                    if out["reputation"] is not None:
                        out["blacklists"].append("abuseipdb")
        except Exception as e:
            print(f"[-] AbuseIPDB Enrichment Error: {e}")
            
    # AlienVault OTX Integration
    try:
        from app.integrations.otx import OTXClient
        otx = OTXClient()
        otx_data = await otx.get_ip_reputation(ip)
        
        if otx_data:
            # Merge OTX data
            if otx_data.get("reputation", 0) > (out["reputation"] or 0):
                out["reputation"] = otx_data["reputation"]
            
            if otx_data.get("tags"):
                current_tags = set(out.get("tags", []))
                current_tags.update(otx_data["tags"])
                out["tags"] = list(current_tags)
                out["blacklists"].append("alienvault_otx")
                
    except Exception as e:
        print(f"[-] OTX Enrichment Error: {e}")
    # Mock Enrichment for Demo (Deterministic based on IP)
    if not out["reputation"]:
        # Generate a fake score based on IP hash
        import hashlib
        hash_val = int(hashlib.md5(ip.encode()).hexdigest(), 16)
        mock_score = hash_val % 101 # 0-100
        
        out["reputation"] = mock_score
        if mock_score > 80:
            out["blacklists"].append("mock_botnet_tracker")
            out["tags"] = ["Botnet", "High Risk"]
        elif mock_score > 50:
             out["tags"] = ["Suspicious", "Spam"]
        else:
             out["tags"] = ["Safe"]
        
        # Mock Lat/Long (Deterministic)
        # Simple hash to map to valid lat/long ranges
        # Lat: -90 to 90, Long: -180 to 180
        out["latitude"] = (hash_val % 180) - 90
        out["longitude"] = ((hash_val // 180) % 360) - 180

    return out
