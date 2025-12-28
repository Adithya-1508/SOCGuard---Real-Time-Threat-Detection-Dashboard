import asyncio
from sqlalchemy import text
from app.db import engine

async def update_schema():
    async with engine.begin() as conn:
        print("Adding reputation_score column...")
        try:
            await conn.execute(text("ALTER TABLE alerts ADD COLUMN reputation_score INTEGER"))
            print("Success.")
        except Exception as e:
            print(f"Skipped (maybe exists): {e}")

        print("Adding threat_tags column...")
        try:
            await conn.execute(text("ALTER TABLE alerts ADD COLUMN threat_tags VARCHAR"))
            print("Success.")
        except Exception as e:
            print(f"Skipped (maybe exists): {e}")

        print("Adding latitude column...")
        try:
            await conn.execute(text("ALTER TABLE alerts ADD COLUMN latitude FLOAT"))
            print("Success.")
        except Exception as e:
            print(f"Skipped (maybe exists): {e}")

        print("Adding longitude column...")
        try:
            await conn.execute(text("ALTER TABLE alerts ADD COLUMN longitude FLOAT"))
            print("Success.")
        except Exception as e:
            print(f"Skipped (maybe exists): {e}")

        print("Adding assigned_to column...")
        try:
            await conn.execute(text("ALTER TABLE alerts ADD COLUMN assigned_to INTEGER REFERENCES users(id)"))
            print("Success.")
        except Exception as e:
            print(f"Skipped (maybe exists): {e}")

        print("Creating comments table...")
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS comments (
                    id SERIAL PRIMARY KEY,
                    alert_id INTEGER NOT NULL REFERENCES alerts(id),
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    content TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
                )
            """))
            print("Success.")
        except Exception as e:
            print(f"Skipped (maybe exists): {e}")

if __name__ == "__main__":
    asyncio.run(update_schema())
