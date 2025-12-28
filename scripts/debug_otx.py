import asyncio
import os
from dotenv import load_dotenv
from app.integrations.otx import OTXClient

# Load env vars
load_dotenv()

async def debug():
    key = os.getenv("OTX_API_KEY")
    print(f"Using Key: {key[:5]}...{key[-5:] if key else 'None'}")
    
    client = OTXClient(api_key=key)
    ip = "185.156.73.106"
    print(f"Querying OTX for {ip}...")
    
    try:
        data = await client.get_ip_reputation(ip)
        print(f"Result: {data}")
    except Exception as e:
        print(f"Async Error: {repr(e)}")
        
    # Try with requests (sync)
    import requests
    print("Trying with requests...")
    try:
        headers = {"X-OTX-API-KEY": key}
        url = f"https://otx.alienvault.com/api/v1/indicators/IPv4/{ip}/general"
        r = requests.get(url, headers=headers, timeout=10)
        print(f"Requests Status: {r.status_code}")
        if r.status_code != 200:
            print(f"Response: {r.text[:200]}")
    except Exception as e:
        print(f"Requests Error: {repr(e)}")

if __name__ == "__main__":
    asyncio.run(debug())
