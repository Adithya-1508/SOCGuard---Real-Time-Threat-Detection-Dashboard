import asyncio
import httpx

async def test_investigate():
    async with httpx.AsyncClient() as client:
        # 1. Get an alert ID
        print("Fetching alerts...")
        r = await client.get("http://localhost:8000/api/alerts/?limit=1")
        if r.status_code != 200:
            print(f"Failed to get alerts: {r.status_code}")
            return
        
        data = r.json()
        if not data['items']:
            print("No alerts found to test.")
            return

        alert_id = data['items'][0]['id']
        print(f"Testing with Alert ID: {alert_id}")

        # 2. Update Status
        print(f"Updating status to 'Investigating'...")
        r = await client.patch(f"http://localhost:8000/api/alerts/{alert_id}", json={"status": "Investigating"})
        
        if r.status_code == 200:
            updated_alert = r.json()
            print(f"Updated Status: {updated_alert['status']}")
            if updated_alert['status'] == 'Investigating':
                print("SUCCESS: Status updated.")
            else:
                print("FAILURE: Status mismatch.")
        else:
            print(f"Update Error: {r.status_code}")
            print(r.text)

if __name__ == "__main__":
    asyncio.run(test_investigate())
