import asyncio
import httpx

async def test_endpoints():
    async with httpx.AsyncClient() as client:
        # Test Chart Data
        print("Testing /api/alerts/chart...")
        r = await client.get("http://localhost:8000/api/alerts/chart")
        if r.status_code == 200:
            data = r.json()
            print(f"Chart Data (first item): {data[0] if data else 'Empty'}")
            print(f"Chart Data Length: {len(data)}")
        else:
            print(f"Chart Error: {r.status_code}")

        # Test Filtering
        print("\nTesting /api/alerts/?severity=critical...")
        r = await client.get("http://localhost:8000/api/alerts/?severity=critical")
        if r.status_code == 200:
            data = r.json()
            print(f"Critical Alerts Count: {data['total']}")
            if data['items']:
                print(f"First Critical Alert Severity: {data['items'][0]['severity']}")
        else:
            print(f"Filter Error: {r.status_code}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
