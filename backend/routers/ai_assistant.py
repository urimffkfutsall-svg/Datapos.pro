"""Datapos AI Assistant - Gemini 2.0 Flash me function calling"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from datetime import datetime, timezone, timedelta
import os
import asyncio

from google import genai
from google.genai import types

from database import db
from auth import get_current_user

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
_client = None


def get_client():
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise HTTPException(status_code=503, detail="AI sherbimi nuk eshte konfiguruar")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    tools_used: List[str] = []


async def tool_get_dashboard_stats(tenant_id, period="today"):
    now = datetime.now(timezone.utc)
    if period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = now - timedelta(days=30)
    else:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    agg = await db.sales.aggregate([
        {"$match": {"tenant_id": tenant_id, "created_at": {"$gte": start}}},
        {"$group": {"_id": None, "total": {"$sum": "$grand_total"}, "count": {"$sum": 1}}}
    ]).to_list(1)
    total_sales = agg[0]["total"] if agg else 0
    total_orders = agg[0]["count"] if agg else 0
    total_products = await db.products.count_documents({"tenant_id": tenant_id})
    low_stock = await db.products.count_documents({"tenant_id": tenant_id, "stock_quantity": {"$lte": 5}})
    return {
        "period": period,
        "total_sales_eur": round(float(total_sales or 0), 2),
        "total_orders": total_orders,
        "total_products": total_products,
        "low_stock_count": low_stock,
    }


async def tool_search_products(tenant_id, query, limit=10):
    products = await db.products.find(
        {"tenant_id": tenant_id, "$or": [
            {"name": {"$regex": query, "$options": "i"}},
            {"barcode": {"$regex": query, "$options": "i"}},
        ]},
        {"_id": 0, "name": 1, "barcode": 1, "selling_price": 1, "stock_quantity": 1, "category": 1}
    ).limit(limit).to_list(limit)
    return {"count": len(products), "products": products}


async def tool_get_low_stock(tenant_id, threshold=5, limit=20):
    products = await db.products.find(
        {"tenant_id": tenant_id, "stock_quantity": {"$lte": threshold}},
        {"_id": 0, "name": 1, "barcode": 1, "stock_quantity": 1, "selling_price": 1}
    ).sort("stock_quantity", 1).limit(limit).to_list(limit)
    return {"count": len(products), "products": products}


async def tool_get_top_products(tenant_id, days=30, limit=10):
    start = datetime.now(timezone.utc) - timedelta(days=days)
    agg = await db.sales.aggregate([
        {"$match": {"tenant_id": tenant_id, "created_at": {"$gte": start}}},
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.product_id",
            "name": {"$first": "$items.name"},
            "total_quantity": {"$sum": "$items.quantity"},
            "total_revenue": {"$sum": {"$multiply": ["$items.quantity", "$items.unit_price"]}}
        }},
        {"$sort": {"total_quantity": -1}},
        {"$limit": limit}
    ]).to_list(limit)
    return {"count": len(agg), "products": agg}


async def tool_get_sales_report(tenant_id, start_date, end_date):
    try:
        start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc) + timedelta(days=1)
    except Exception:
        return {"error": "Format i pavlefshem date. Perdor YYYY-MM-DD"}
    agg = await db.sales.aggregate([
        {"$match": {"tenant_id": tenant_id, "created_at": {"$gte": start, "$lt": end}}},
        {"$group": {"_id": None, "total_revenue": {"$sum": "$grand_total"},
                    "total_orders": {"$sum": 1}, "avg_order": {"$avg": "$grand_total"}}}
    ]).to_list(1)
    if not agg:
        return {"start_date": start_date, "end_date": end_date, "total_revenue": 0, "total_orders": 0, "avg_order": 0}
    r = agg[0]
    return {
        "start_date": start_date, "end_date": end_date,
        "total_revenue_eur": round(float(r["total_revenue"] or 0), 2),
        "total_orders": r["total_orders"],
        "avg_order_eur": round(float(r["avg_order"] or 0), 2),
    }


async def tool_get_customer_debts(tenant_id, limit=20):
    debts = await db.debts.find(
        {"tenant_id": tenant_id, "status": {"$ne": "paid"}},
        {"_id": 0, "customer_name": 1, "amount": 1, "remaining_amount": 1, "due_date": 1}
    ).sort("remaining_amount", -1).limit(limit).to_list(limit)
    return {"count": len(debts), "debts": debts}


async def tool_get_users_list(tenant_id):
    users = await db.users.find(
        {"tenant_id": tenant_id},
        {"_id": 0, "username": 1, "full_name": 1, "role": 1, "email": 1}
    ).to_list(100)
    return {"count": len(users), "users": users}


TOOL_HANDLERS = {
    "get_dashboard_stats": tool_get_dashboard_stats,
    "search_products": tool_search_products,
    "get_low_stock": tool_get_low_stock,
    "get_top_products": tool_get_top_products,
    "get_sales_report": tool_get_sales_report,
    "get_customer_debts": tool_get_customer_debts,
    "get_users_list": tool_get_users_list,
}


def build_tools():
    return [types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="get_dashboard_stats",
            description="Statistika kryesore: shitjet, porosite, produktet, stok i ulet",
            parameters={"type": "OBJECT", "properties": {"period": {"type": "STRING", "enum": ["today", "week", "month"]}}, "required": ["period"]}
        ),
        types.FunctionDeclaration(
            name="search_products",
            description="Kerko produkte sipas emrit ose barkodit",
            parameters={"type": "OBJECT", "properties": {"query": {"type": "STRING"}, "limit": {"type": "INTEGER"}}, "required": ["query"]}
        ),
        types.FunctionDeclaration(
            name="get_low_stock",
            description="Produktet me stok te ulet (nen threshold)",
            parameters={"type": "OBJECT", "properties": {"threshold": {"type": "INTEGER"}, "limit": {"type": "INTEGER"}}}
        ),
        types.FunctionDeclaration(
            name="get_top_products",
            description="Produktet me te shitura ne dite te caktuara",
            parameters={"type": "OBJECT", "properties": {"days": {"type": "INTEGER"}, "limit": {"type": "INTEGER"}}}
        ),
        types.FunctionDeclaration(
            name="get_sales_report",
            description="Raport shitjesh nga data ne date (YYYY-MM-DD)",
            parameters={"type": "OBJECT", "properties": {"start_date": {"type": "STRING"}, "end_date": {"type": "STRING"}}, "required": ["start_date", "end_date"]}
        ),
        types.FunctionDeclaration(
            name="get_customer_debts",
            description="Lista e klienteve me borxhe te papaguar",
            parameters={"type": "OBJECT", "properties": {"limit": {"type": "INTEGER"}}}
        ),
        types.FunctionDeclaration(
            name="get_users_list",
            description="Lista e perdoruesve te firmes",
            parameters={"type": "OBJECT", "properties": {}}
        ),
    ])]


SYSTEM_INSTRUCTION = """Ti je Datapos AI, asistenti inteligjent i sistemit POS Datapos.pro.
- Pergjigjesh gjithnje ne SHQIP, ne menyre te qarte dhe profesionale
- Perdor bullet points ose tabela kur ka disa items
- Formato monedhen si "EUR XX.XX"
- Datat ne format "dd/mm/yyyy"
- Mos beje veprime destruktive - vetem lexo te dhena
- Nese pyetja kerkon te dhena reale, perdor tools qe ke ne dispozicion"""

RATE_LIMIT_PER_HOUR = 100


async def check_rate_limit(user_id):
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    count = await db.ai_messages.count_documents({"user_id": user_id, "created_at": {"$gte": one_hour_ago}})
    return count < RATE_LIMIT_PER_HOUR


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY mungon ne server")
    user_id = str(current_user.get("id") or current_user.get("_id") or current_user.get("username", "unknown"))
    tenant_id = current_user.get("tenant_id")
    role = current_user.get("role", "cashier")
    if not tenant_id and role != "super_admin":
        raise HTTPException(status_code=400, detail="Nuk ka konteks te firmes")
    if not await check_rate_limit(user_id):
        raise HTTPException(status_code=429, detail="Limit i pyetjeve/ore u arrit. Prit pak.")
    try:
        client = get_client()
        contents = []
        for msg in request.history[-10:]:
            role_g = "user" if msg.role == "user" else "model"
            contents.append(types.Content(role=role_g, parts=[types.Part(text=msg.content)]))
        contents.append(types.Content(role="user", parts=[types.Part(text=request.message)]))
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=build_tools(),
            temperature=0.4,
        )
        tools_used = []
        for iteration in range(5):
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=MODEL_NAME, contents=contents, config=config,
            )
            has_calls = False
            fresponses = []
            for candidate in (response.candidates or []):
                for part in (candidate.content.parts or []):
                    if getattr(part, "function_call", None):
                        has_calls = True
                        fname = part.function_call.name
                        fargs = dict(part.function_call.args or {})
                        tools_used.append(fname)
                        handler = TOOL_HANDLERS.get(fname)
                        try:
                            result = await handler(tenant_id=tenant_id, **fargs) if handler else {"error": "unknown tool"}
                        except Exception as e:
                            result = {"error": str(e)}
                        fresponses.append(types.Part.from_function_response(name=fname, response={"result": result}))
            if has_calls:
                contents.append(response.candidates[0].content)
                contents.append(types.Content(role="user", parts=fresponses))
            else:
                reply = (response.text or "Me fal, nuk munda te pergjigjem.").strip()
                await db.ai_messages.insert_one({
                    "user_id": user_id, "tenant_id": tenant_id,
                    "user_message": request.message, "ai_reply": reply,
                    "tools_used": tools_used, "created_at": datetime.now(timezone.utc),
                })
                return ChatResponse(reply=reply, tools_used=tools_used)
        return ChatResponse(reply="Kerkesa ishte shume e nderlikuar.", tools_used=tools_used)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="AI gabim: " + str(e))


@router.get("/history")
async def get_history(current_user: dict = Depends(get_current_user), limit: int = 50):
    user_id = str(current_user.get("id") or current_user.get("_id") or current_user.get("username", "unknown"))
    messages = await db.ai_messages.find(
        {"user_id": user_id},
        {"_id": 0, "user_message": 1, "ai_reply": 1, "created_at": 1}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return {"messages": list(reversed(messages))}


@router.delete("/history")
async def clear_history(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("id") or current_user.get("_id") or current_user.get("username", "unknown"))
    result = await db.ai_messages.delete_many({"user_id": user_id})
    return {"deleted": result.deleted_count}


@router.get("/suggestions")
async def get_suggestions(current_user: dict = Depends(get_current_user)):
    role = current_user.get("role", "cashier")
    common = ["Sa shita sot?", "Cilat produkte kane stok te ulet?", "Top 5 produkte kete jave", "Beje nje raport te ketij muaji"]
    admin_extra = ["Klientet me borxh te madh", "Krahaso shitjet e ketij muaji me te kaluarin"]
    cashier = ["A kam kabell tip C ne stok?", "Cka duhet te porosis?"]
    if role == "cashier":
        return {"suggestions": cashier + common[:2]}
    return {"suggestions": common + admin_extra}