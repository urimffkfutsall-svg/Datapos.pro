"""PhoneSoftware Database Collections"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
_client = AsyncIOMotorClient(mongo_url)
_db = _client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 't3next_pos_secret_key')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')

security = HTTPBearer()

# PhoneSoftware specific collections
ps_tenants = _db["ps_tenants"]
ps_users = _db["ps_users"]
ps_customers = _db["ps_customers"]
ps_repairs = _db["ps_repairs"]
ps_inventory = _db["ps_inventory"]
ps_stock_movements = _db["ps_stock_movements"]
ps_sales = _db["ps_sales"]
ps_notifications = _db["ps_notifications"]
ps_audit_logs = _db["ps_audit_logs"]

# Also access POS users for super_admin check
pos_users = _db["users"]


async def get_ps_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get the current authenticated user for PhoneSoftware - checks ps_users and pos_users (for super_admin)"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        
        # First check PhoneSoftware users
        user = await ps_users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
        
        if not user:
            # Check POS users (for super_admin)
            user = await pos_users.find_one({"id": user_id, "role": "super_admin"}, {"_id": 0, "password_hash": 0})
        
        if not user:
            raise HTTPException(status_code=401, detail="Përdoruesi nuk u gjet")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token-i ka skaduar")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token i pavlefshëm")


async def init_ps_indexes():
    """Initialize indexes for PhoneSoftware collections"""
    # Tenants
    await ps_tenants.create_index("name", unique=True)
    await ps_tenants.create_index("email", unique=True)
    
    # Users
    await ps_users.create_index([("username", 1), ("tenant_id", 1)], unique=True)
    
    # Customers
    await ps_customers.create_index([("phone", 1), ("tenant_id", 1)])
    
    # Repairs
    await ps_repairs.create_index("ticket_number", unique=True)
    await ps_repairs.create_index([("tenant_id", 1), ("status", 1)])
    await ps_repairs.create_index([("customer_id", 1)])
    await ps_repairs.create_index("imei")
    
    # Inventory
    await ps_inventory.create_index([("tenant_id", 1), ("category", 1)])
    await ps_inventory.create_index("barcode")
    await ps_inventory.create_index("imei")
    
    # Sales
    await ps_sales.create_index("sale_number", unique=True)
    await ps_sales.create_index([("tenant_id", 1), ("created_at", -1)])
