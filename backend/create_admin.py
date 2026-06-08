"""Create or update a super admin user."""
import asyncio
import os
import sys
import uuid
import bcrypt
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

USERNAME = "urimi1806"
PASSWORD = "1806"
FULL_NAME = "Urim Krasniqi"
ROLE = "super_admin"

async def main():
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    # Hash the password
    password_hash = bcrypt.hashpw(PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    existing = await db.users.find_one({"username": USERNAME})
    now_iso = datetime.now(timezone.utc).isoformat()

    if existing:
        await db.users.update_one(
            {"username": USERNAME},
            {"$set": {
                "password_hash": password_hash,
                "role": ROLE,
                "is_active": True,
                "full_name": FULL_NAME,
            }}
        )
        print(f"OK: U perditesua super admin '{USERNAME}' (id={existing.get('id')})")
    else:
        user_doc = {
            "id": str(uuid.uuid4()),
            "username": USERNAME,
            "password_hash": password_hash,
            "full_name": FULL_NAME,
            "role": ROLE,
            "is_active": True,
            "created_at": now_iso,
        }
        await db.users.insert_one(user_doc)
        print(f"OK: U krijua super admin '{USERNAME}' (id={user_doc['id']})")

    print(f"   Username: {USERNAME}")
    print(f"   Password: {PASSWORD}")
    print(f"   Role:     {ROLE}")

    client.close()

if __name__ == "__main__":
    asyncio.run(main())
