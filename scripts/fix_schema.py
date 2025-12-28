import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@db/soc_db")

async def fix_schema():
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.connect() as conn:
        # We'll try each one in a separate transaction block (commit in between)
        # or just use isolation_level="AUTOCOMMIT" if supported, but let's just do separate connects or commits.
        
        print("Adding latitude...")
        try:
            await conn.execute(text("ALTER TABLE alerts ADD COLUMN latitude FLOAT"))
            await conn.commit()
            print("Success.")
        except Exception as e:
            print(f"Failed/Skipped: {e}")
            await conn.rollback()

        print("Adding longitude...")
        try:
            await conn.execute(text("ALTER TABLE alerts ADD COLUMN longitude FLOAT"))
            await conn.commit()
            print("Success.")
        except Exception as e:
            print(f"Failed/Skipped: {e}")
            await conn.rollback()

        print("Adding assigned_to...")
        try:
            await conn.execute(text("ALTER TABLE alerts ADD COLUMN assigned_to INTEGER REFERENCES users(id)"))
            await conn.commit()
            print("Success.")
        except Exception as e:
            print(f"Failed/Skipped: {e}")
            await conn.rollback()

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
            await conn.commit()
            print("Success.")
        except Exception as e:
            print(f"Failed/Skipped: {e}")
            await conn.rollback()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_schema())
