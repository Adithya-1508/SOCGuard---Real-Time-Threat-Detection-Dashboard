import asyncio
import httpx
from datetime import datetime, timedelta

async def test_time_filter():
    async with httpx.AsyncClient() as client:
        # 1. Get Chart Data
        print("Fetching chart data...")
        r = await client.get("http://localhost:8000/api/alerts/chart")
        if r.status_code != 200:
            print(f"Failed to get chart: {r.status_code}")
            return
        
        chart_data = r.json()
        # Find a bucket with alerts
        target_bucket = None
        for item in chart_data:
            if item["alerts"] > 0:
                target_bucket = item
                break
        
        if not target_bucket:
            print("No alerts found in chart data to test with.")
            return

        print(f"Testing with bucket: {target_bucket['name']} (Alerts: {target_bucket['alerts']})")
        timestamp = target_bucket["timestamp"]
        print(f"Timestamp: {timestamp}")

        # Calculate end time (+1 hour)
        start_dt = datetime.fromisoformat(timestamp)
        end_dt = start_dt + timedelta(hours=1)
        end_time = end_dt.isoformat()
        
        print(f"Querying range: {timestamp} to {end_time}")

        # 2. Query Alerts with Time Filter
        params = {
            "start_time": timestamp,
            "end_time": end_time
        }
        r = await client.get("http://localhost:8000/api/alerts/", params=params)
        
        if r.status_code == 200:
            data = r.json()
            print(f"Filtered Alerts Count: {data['total']}")
            print(f"Expected Count: ~{target_bucket['alerts']}")
            
            if data['total'] == 0:
                print("FAILURE: No alerts returned for the time range.")
            else:
                print("SUCCESS: Alerts returned.")
        else:
            print(f"Filter API Error: {r.status_code}")
            print(r.text)

if __name__ == "__main__":
    asyncio.run(test_time_filter())
