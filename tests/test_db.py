import asyncio
from app.db import AsyncSessionLocal
from app.models import User
from sqlalchemy import select

async def test():
    print("Starting DB test...")
    async with AsyncSessionLocal() as session:
        print("Session created.")
        try:
            # Check if user exists
            stmt = select(User).where(User.email == 'test@test.com')
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                print("User already exists.")
                return

            print("Creating user...")
            u = User(email='test@test.com', hashed_password='pw', full_name='Test')
            session.add(u)
            print("Adding to session...")
            await session.commit()
            print("Committed.")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
