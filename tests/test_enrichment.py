import asyncio
import httpx

async def test_enrichment():
    async with httpx.AsyncClient() as client:
        print("Fetching alerts...")
        r = await client.get("http://localhost:8000/api/alerts/?limit=5")
        if r.status_code != 200:
            print(f"Failed to get alerts: {r.status_code}")
            return
        
        data = r.json()
        alerts = data.get('items', [])
        
        if not alerts:
            print("No alerts found.")
            return

        print(f"Checking {len(alerts)} alerts for enrichment data...")
        enriched_count = 0
        for alert in alerts:
            score = alert.get('reputation_score')
            tags = alert.get('threat_tags')
            print(f"ID: {alert['id']}, IP: {alert.get('ip')}, Score: {score}, Tags: {tags}")
            
            if score is not None:
                enriched_count += 1

        if enriched_count > 0:
            print(f"SUCCESS: Found {enriched_count} enriched alerts.")
        else:
            print("FAILURE: No enriched alerts found. (Old alerts might not be enriched, try generating new ones)")

if __name__ == "__main__":
    asyncio.run(test_enrichment())
