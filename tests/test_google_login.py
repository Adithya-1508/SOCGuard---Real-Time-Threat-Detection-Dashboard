import asyncio
import httpx

async def test_google_login():
    async with httpx.AsyncClient() as client:
        try:
            print("Testing GET /auth/google/login...")
            r = await client.get("http://127.0.0.1:8000/auth/google/login")
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print(f"URL: {data.get('url')}")
            else:
                print(f"Error: {r.text}")
        except Exception as e:
            print(f"Exception: {repr(e)}")

if __name__ == "__main__":
    asyncio.run(test_google_login())
