"""Reports routes (Dashboard, Sales, Stock, Cashier Performance, PDF/Excel Export)"""
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from typing import Optional
from datetime import datetime, timezone
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import xlsxwriter

from database import db
from models import UserRole
from auth import get_current_user, require_role, get_tenant_filter

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/dashboard")
async def get_dashboard(
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get dashboard statistics"""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    
    tenant_filter = get_tenant_filter(current_user)
    query = {"created_at": {"$gte": today}, **tenant_filter}
    if branch_id:
        query["branch_id"] = branch_id
    
    sales_today = await db.sales.find(query, {"_id": 0}).to_list(10000)
    total_sales = sum(s.get("grand_total", 0) for s in sales_today)
    total_transactions = len(sales_today)
    
    low_stock_query = {"current_stock": {"$lt": 10}, **tenant_filter}
    if branch_id:
        low_stock_query["branch_id"] = branch_id
    low_stock_count = await db.products.count_documents(low_stock_query)
    
    product_query = {**tenant_filter}
    if branch_id:
        product_query["branch_id"] = branch_id
    total_products = await db.products.count_documents(product_query)
    
    recent_sales = await db.sales.find({**query}, {"_id": 0}).sort("created_at", -1).to_list(10)

    # Produktet me te shitura (nga te gjitha shitjet e firmes)
    top_query = {**tenant_filter}
    if branch_id:
        top_query["branch_id"] = branch_id
    all_sales_tp = await db.sales.find(top_query, {"_id": 0, "items": 1}).to_list(100000)
    qty_by_product = {}
    name_by_product = {}
    for s_tp in all_sales_tp:
        for item in s_tp.get("items", []):
            pid = item.get("product_id")
            if not pid:
                continue
            qty_by_product[pid] = qty_by_product.get(pid, 0) + item.get("quantity", 0)
            if item.get("product_name"):
                name_by_product[pid] = item.get("product_name")
    missing_tp = [pid for pid in qty_by_product if pid not in name_by_product]
    if missing_tp:
        prods_tp = await db.products.find({"id": {"$in": missing_tp}, **tenant_filter}, {"_id": 0, "id": 1, "name": 1}).to_list(100000)
        for p_tp in prods_tp:
            name_by_product[p_tp.get("id")] = p_tp.get("name")
    top_products = sorted(
        [{"name": name_by_product.get(pid) or "?", "sales": qty} for pid, qty in qty_by_product.items()],
        key=lambda x: x["sales"],
        reverse=True
    )[:5]
    
    return {
        "total_sales_today": round(total_sales, 2),
        "total_transactions_today": total_transactions,
        "low_stock_products": low_stock_count,
        "total_products": total_products,
        "recent_sales": recent_sales,
        "top_products": top_products
    }


@router.get("/sales")
async def get_sales_report(
    start_date: str = Query(...),
    end_date: str = Query(...),
    branch_id: Optional[str] = None,
    user_id: Optional[str] = None,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Get sales report"""
    tenant_filter = get_tenant_filter(current_user)
    query = {"created_at": {"$gte": start_date, "$lte": end_date}, **tenant_filter}
    if branch_id:
        query["branch_id"] = branch_id
    if user_id:
        query["user_id"] = user_id
    
    sales = await db.sales.find(query, {"_id": 0}).to_list(100000)
    
    total_revenue = sum(s.get("grand_total", 0) for s in sales)
    total_vat = sum(s.get("total_vat", 0) for s in sales)
    total_discount = sum(s.get("total_discount", 0) for s in sales)
    
    daily_sales = {}
    for sale in sales:
        date = sale["created_at"][:10]
        if date not in daily_sales:
            daily_sales[date] = {"total": 0, "count": 0}
        daily_sales[date]["total"] += sale.get("grand_total", 0)
        daily_sales[date]["count"] += 1
    
    return {
        "period": {"start": start_date, "end": end_date},
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "total_vat": round(total_vat, 2),
            "total_discount": round(total_discount, 2),
            "total_transactions": len(sales),
            "average_transaction": round(total_revenue / len(sales), 2) if sales else 0
        },
        "daily_breakdown": [{"date": k, **v} for k, v in sorted(daily_sales.items())],
        "sales": sales[:100]
    }


@router.get("/profit-loss")
async def get_profit_loss_report(
    start_date: str = Query(...),
    end_date: str = Query(...),
    branch_id: Optional[str] = None,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Get profit/loss report"""
    tenant_filter = get_tenant_filter(current_user)
    query = {"created_at": {"$gte": start_date, "$lte": end_date}, **tenant_filter}
    if branch_id:
        query["branch_id"] = branch_id
    
    sales = await db.sales.find(query, {"_id": 0}).to_list(100000)
    
    product_ids = set()
    for sale in sales:
        for item in sale.get("items", []):
            product_ids.add(item.get("product_id"))
    
    products = await db.products.find({"id": {"$in": list(product_ids)}, **tenant_filter}, {"_id": 0}).to_list(100000)
    product_map = {p["id"]: p for p in products}
    
    daily_data = {}
    for sale in sales:
        date = sale["created_at"][:10]
        if date not in daily_data:
            daily_data[date] = {"revenue": 0, "cost": 0, "vat": 0}
        
        daily_data[date]["revenue"] += sale.get("grand_total", 0)
        daily_data[date]["vat"] += sale.get("total_vat", 0)
        
        for item in sale.get("items", []):
            product = product_map.get(item.get("product_id"), {})
            cost = (product.get("purchase_price") or 0) * item.get("quantity", 0)
            daily_data[date]["cost"] += cost
    
    total_revenue = sum(d["revenue"] for d in daily_data.values())
    total_cost = sum(d["cost"] for d in daily_data.values())
    total_vat = sum(d["vat"] for d in daily_data.values())
    gross_profit = total_revenue - total_cost - total_vat
    
    return {
        "period": {"start": start_date, "end": end_date},
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "gross_profit": round(gross_profit, 2),
            "profit_margin": round((gross_profit / total_revenue * 100) if total_revenue > 0 else 0, 2),
            "total_vat": round(total_vat, 2),
            "net_profit": round(gross_profit - total_vat, 2)
        },
        "daily_breakdown": [
            {
                "date": date,
                "revenue": round(data["revenue"], 2),
                "cost": round(data["cost"], 2),
                "profit": round(data["revenue"] - data["cost"] - data["vat"], 2),
                "vat": round(data["vat"], 2)
            }
            for date, data in sorted(daily_data.items())
        ]
    }


@router.get("/stock")
async def get_stock_report(
    branch_id: Optional[str] = None,
    category: Optional[str] = None,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Get stock report"""
    tenant_filter = get_tenant_filter(current_user)
    query = {**tenant_filter}
    if branch_id:
        query["branch_id"] = branch_id
    if category:
        query["category"] = category
    
    products = await db.products.find(query, {"_id": 0}).to_list(100000)
    
    total_value = sum((p.get("current_stock", 0) * (p.get("purchase_price", 0) or 0)) for p in products)
    total_items = sum(p.get("current_stock", 0) for p in products)
    low_stock = [p for p in products if p.get("current_stock", 0) < 10]
    out_of_stock = [p for p in products if p.get("current_stock", 0) <= 0]
    
    return {
        "summary": {
            "total_products": len(products),
            "total_items": total_items,
            "total_value": round(total_value, 2),
            "low_stock_count": len(low_stock),
            "out_of_stock_count": len(out_of_stock)
        },
        "low_stock_products": low_stock[:20],
        "out_of_stock_products": out_of_stock[:20]
    }


@router.get("/cashier-performance")
async def get_cashier_performance(
    start_date: str = Query(...),
    end_date: str = Query(...),
    branch_id: Optional[str] = None,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Get cashier performance report"""
    tenant_filter = get_tenant_filter(current_user)
    query = {"created_at": {"$gte": start_date, "$lte": end_date}, **tenant_filter}
    if branch_id:
        query["branch_id"] = branch_id
    
    sales = await db.sales.find(query, {"_id": 0}).to_list(100000)
    
    user_stats = {}
    for sale in sales:
        user_id = sale["user_id"]
        if user_id not in user_stats:
            user_stats[user_id] = {"total_sales": 0, "total_transactions": 0, "total_items": 0}
        user_stats[user_id]["total_sales"] += sale.get("grand_total", 0)
        user_stats[user_id]["total_transactions"] += 1
        user_stats[user_id]["total_items"] += sum(item.get("quantity", 0) for item in sale.get("items", []))
    
    result = []
    for user_id, stats in user_stats.items():
        user = await db.users.find_one({"id": user_id, **tenant_filter}, {"_id": 0, "full_name": 1})
        result.append({
            "user_id": user_id,
            "user_name": user.get("full_name", "Unknown") if user else "Unknown",
            **stats
        })
    
    return sorted(result, key=lambda x: x["total_sales"], reverse=True)


@router.get("/export/pdf")
async def export_pdf_report(
    report_type: str = Query(..., description="sales, stock, cashier"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    branch_id: Optional[str] = None,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Export report as PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    tenant_filter = get_tenant_filter(current_user)
    
    company = await db.settings.find_one({"type": "company", **tenant_filter} if tenant_filter else {"type": "company"}, {"_id": 0})
    company_name = company.get("data", {}).get("company_name", "iPOS") if company else "iPOS"
    
    elements.append(Paragraph(f"<b>{company_name}</b>", styles['Heading1']))
    elements.append(Spacer(1, 6))
    
    report_titles = {
        "sales": "Raport Shitjesh",
        "stock": "Raport Stoku",
        "cashier": "Raport Arkëtarësh",
        "profit": "Raport Fitimi/Humbje"
    }
    title = report_titles.get(report_type, f"Raport {report_type.capitalize()}")
    elements.append(Paragraph(f"<b>{title}</b>", styles['Heading2']))
    
    if start_date and end_date:
        elements.append(Paragraph(f"Periudha: {start_date} - {end_date}", styles['Normal']))
    elements.append(Paragraph(f"Gjeneruar: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    if report_type == "sales" and start_date and end_date:
        query = {"created_at": {"$gte": start_date, "$lte": end_date + "T23:59:59"}, **tenant_filter}
        if branch_id:
            query["branch_id"] = branch_id
        sales = await db.sales.find(query, {"_id": 0}).sort("created_at", -1).to_list(10000)
        
        total_sales = sum(s.get("grand_total", 0) for s in sales)
        total_vat = sum(s.get("total_vat", 0) for s in sales)
        cash_sales = sum(s.get("grand_total", 0) for s in sales if s.get("payment_method") == "cash")
        card_sales = sum(s.get("grand_total", 0) for s in sales if s.get("payment_method") in ["card", "bank"])
        
        summary_data = [
            ["PËRMBLEDHJE", ""],
            ["Numri i Transaksioneve", str(len(sales))],
            ["Të Ardhura Totale", f"€{total_sales:.2f}"],
            ["TVSH Total", f"€{total_vat:.2f}"],
            ["Pagesa Cash", f"€{cash_sales:.2f}"],
            ["Pagesa Kartë/Bank", f"€{card_sales:.2f}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[200, 150])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00a79d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        elements.append(Paragraph("<b>Detajet e Shitjeve</b>", styles['Heading3']))
        elements.append(Spacer(1, 10))
        
        data = [["#", "Data", "Nr. Faturës", "Totali", "TVSH", "Metoda"]]
        for i, sale in enumerate(sales[:50], 1):
            data.append([
                str(i),
                sale["created_at"][:10],
                sale.get("receipt_number", "-"),
                f"€{sale.get('grand_total', 0):.2f}",
                f"€{sale.get('total_vat', 0):.2f}",
                sale.get("payment_method", "-")
            ])
        
        if len(data) > 1:
            table = Table(data, colWidths=[30, 80, 100, 80, 60, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00a79d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("Nuk ka shitje në këtë periudhë.", styles['Normal']))
    
    elif report_type == "stock":
        products = await db.products.find(tenant_filter, {"_id": 0}).sort("name", 1).to_list(10000)
        
        total_products = len(products)
        low_stock = len([p for p in products if (p.get("current_stock", 0) or 0) < 10])
        total_value = sum((p.get("current_stock", 0) or 0) * (p.get("purchase_price", 0) or 0) for p in products)
        
        summary_data = [
            ["PËRMBLEDHJE STOKU", ""],
            ["Numri i Produkteve", str(total_products)],
            ["Produkte me Stok të Ulët (<10)", str(low_stock)],
            ["Vlera Totale e Stokut", f"€{total_value:.2f}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[200, 150])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00a79d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        data = [["Emri", "Barkodi", "Stoku", "Ç. Blerjes", "Ç. Shitjes"]]
        for p in products[:50]:
            data.append([
                (p.get("name") or "-")[:30],
                p.get("barcode") or "-",
                str(p.get("current_stock", 0)),
                f"€{p.get('purchase_price', 0) or 0:.2f}",
                f"€{p.get('sale_price', 0) or 0:.2f}"
            ])
        
        if len(data) > 1:
            table = Table(data, colWidths=[150, 80, 50, 70, 70])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00a79d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=raport_{report_type}_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )


@router.get("/export/excel")
async def export_excel_report(
    report_type: str = Query(..., description="sales, stock"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    branch_id: Optional[str] = None,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Export report as Excel"""
    buffer = io.BytesIO()
    workbook = xlsxwriter.Workbook(buffer)
    tenant_filter = get_tenant_filter(current_user)
    
    title_format = workbook.add_format({'bold': True, 'font_size': 16, 'font_color': '#00a79d'})
    header_format = workbook.add_format({'bold': True, 'bg_color': '#00a79d', 'font_color': 'white', 'border': 1})
    summary_header = workbook.add_format({'bold': True, 'bg_color': '#f0f0f0', 'border': 1})
    summary_value = workbook.add_format({'num_format': '€#,##0.00', 'border': 1})
    money_format = workbook.add_format({'num_format': '€#,##0.00'})
    
    company = await db.settings.find_one({"type": "company", **tenant_filter} if tenant_filter else {"type": "company"}, {"_id": 0})
    company_name = company.get("data", {}).get("company_name", "iPOS") if company else "iPOS"
    
    if report_type == "sales" and start_date and end_date:
        worksheet = workbook.add_worksheet("Shitjet")
        
        worksheet.write(0, 0, company_name, title_format)
        worksheet.write(1, 0, f"Raport Shitjesh: {start_date} - {end_date}")
        worksheet.write(2, 0, f"Gjeneruar: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        query = {"created_at": {"$gte": start_date, "$lte": end_date + "T23:59:59"}, **tenant_filter}
        if branch_id:
            query["branch_id"] = branch_id
        sales = await db.sales.find(query, {"_id": 0}).sort("created_at", -1).to_list(10000)
        
        total_sales = sum(s.get("grand_total", 0) for s in sales)
        total_vat = sum(s.get("total_vat", 0) for s in sales)
        cash_sales = sum(s.get("grand_total", 0) for s in sales if s.get("payment_method") == "cash")
        card_sales = sum(s.get("grand_total", 0) for s in sales if s.get("payment_method") in ["card", "bank"])
        
        worksheet.write(4, 0, "PËRMBLEDHJE", summary_header)
        worksheet.write(5, 0, "Numri i Transaksioneve", summary_header)
        worksheet.write(5, 1, len(sales))
        worksheet.write(6, 0, "Të Ardhura Totale", summary_header)
        worksheet.write(6, 1, total_sales, summary_value)
        worksheet.write(7, 0, "TVSH Total", summary_header)
        worksheet.write(7, 1, total_vat, summary_value)
        worksheet.write(8, 0, "Pagesa Cash", summary_header)
        worksheet.write(8, 1, cash_sales, summary_value)
        worksheet.write(9, 0, "Pagesa Kartë/Bank", summary_header)
        worksheet.write(9, 1, card_sales, summary_value)
        
        headers = ["#", "Data", "Nr. Faturës", "Nëntotali", "TVSH", "Totali", "Metoda"]
        for col, header in enumerate(headers):
            worksheet.write(11, col, header, header_format)
        
        for row, sale in enumerate(sales, start=12):
            worksheet.write(row, 0, row - 11)
            worksheet.write(row, 1, sale["created_at"][:10])
            worksheet.write(row, 2, sale.get("receipt_number", "-"))
            worksheet.write(row, 3, sale.get("subtotal", 0), money_format)
            worksheet.write(row, 4, sale.get("total_vat", 0), money_format)
            worksheet.write(row, 5, sale.get("grand_total", 0), money_format)
            worksheet.write(row, 6, sale.get("payment_method", "-"))
        
        worksheet.set_column(0, 0, 5)
        worksheet.set_column(1, 1, 12)
        worksheet.set_column(2, 2, 15)
        worksheet.set_column(3, 5, 12)
        worksheet.set_column(6, 6, 10)
    
    elif report_type == "stock":
        worksheet = workbook.add_worksheet("Stoku")
        
        worksheet.write(0, 0, company_name, title_format)
        worksheet.write(1, 0, "Raport Stoku")
        worksheet.write(2, 0, f"Gjeneruar: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        products = await db.products.find(tenant_filter, {"_id": 0}).sort("name", 1).to_list(10000)
        
        total_products = len(products)
        low_stock = len([p for p in products if (p.get("current_stock", 0) or 0) < 10])
        total_value = sum((p.get("current_stock", 0) or 0) * (p.get("purchase_price", 0) or 0) for p in products)
        
        worksheet.write(4, 0, "PËRMBLEDHJE STOKU", summary_header)
        worksheet.write(5, 0, "Numri i Produkteve", summary_header)
        worksheet.write(5, 1, total_products)
        worksheet.write(6, 0, "Produkte me Stok të Ulët", summary_header)
        worksheet.write(6, 1, low_stock)
        worksheet.write(7, 0, "Vlera Totale e Stokut", summary_header)
        worksheet.write(7, 1, total_value, summary_value)
        
        headers = ["Emri", "Barkodi", "Stoku", "Ç. Blerjes", "Ç. Shitjes", "Vlera"]
        for col, header in enumerate(headers):
            worksheet.write(9, col, header, header_format)
        
        for row, p in enumerate(products, start=10):
            worksheet.write(row, 0, p.get("name") or "-")
            worksheet.write(row, 1, p.get("barcode") or "-")
            worksheet.write(row, 2, p.get("current_stock", 0))
            worksheet.write(row, 3, p.get("purchase_price", 0) or 0, money_format)
            worksheet.write(row, 4, p.get("sale_price", 0) or 0, money_format)
            value = (p.get("current_stock", 0) or 0) * (p.get("purchase_price", 0) or 0)
            worksheet.write(row, 5, value, money_format)
        
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 1, 15)
        worksheet.set_column(2, 5, 12)
    
    workbook.close()
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=raport_{report_type}_{datetime.now().strftime('%Y%m%d')}.xlsx"}
    )
