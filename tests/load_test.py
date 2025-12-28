import asyncio
import aiohttp
import time
import random
import sys

API_URL = "http://localhost:8000/api/ingest"
TOTAL_REQUESTS = 1000
CONCURRENCY = 100

async def send_event(session):
    payload = {
        "source": "load_test",
        "message": "Scale test event",
        "ip": f"192.168.1.{random.randint(1, 255)}",
        "metadata": {"load": True}
    }
    async with session.post(API_URL, json=payload) as resp:
        return resp.status

async def load_test():
    print(f"🚀 Starting Load Test: {TOTAL_REQUESTS} requests, {CONCURRENCY} concurrent...")
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(TOTAL_REQUESTS):
            tasks.append(send_event(session))
            
            # Limit concurrency
            if len(tasks) >= CONCURRENCY:
                await asyncio.gather(*tasks)
                tasks = []
        
        if tasks:
            await asyncio.gather(*tasks)
            
    end_time = time.time()
    duration = end_time - start_time
    eps = TOTAL_REQUESTS / duration
    
    print(f"\n📊 Results:")
    print(f"   Total Requests: {TOTAL_REQUESTS}")
    print(f"   Duration:       {duration:.2f} seconds")
    print(f"   Throughput:     {eps:.2f} EPS (Events Per Second)")
    
    if eps > 1000:
        print("✅ Performance: Excellent (Handles bursts well)")
    elif eps > 500:
        print("✅ Performance: Good (Suitable for SMBs)")
    else:
        print("⚠️ Performance: Needs Optimization (Bottleneck detected)")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(load_test())
