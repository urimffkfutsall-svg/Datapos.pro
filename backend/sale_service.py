"""Atomic POS sale creation. No external effects inside a transaction callback.
Requires MongoDB replica-set/sharded transactions (for example MongoDB Atlas).
"""
import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from zoneinfo import ZoneInfo

_PREPARED_DATABASES = set()

CENT = Decimal('0.01')


class SaleError(Exception):
    def __init__(self, status, detail):
        self.status, self.detail = status, detail
        super().__init__(detail)


def number(value, label, minimum=Decimal('0'), maximum=Decimal('999999999')):
    try:
        result = Decimal(str(0 if value is None else value))
    except (InvalidOperation, ValueError):
        raise SaleError(400, f'{label}: vlerë e pavlefshme')
    if not result.is_finite() or result < minimum or result > maximum:
        raise SaleError(400, f'{label}: vlerë jashtë kufijve')
    return result


def money(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def quote_sale(data, products, coupon=None, now=None):
    """Validate all lines/coupon/payment before any mutation; sum rounded line amounts."""
    lines = data.get('items') or []
    if not lines or len(lines) > 500:
        raise SaleError(400, 'Shporta duhet të ketë 1–500 rreshta')
    result, stock = [], {}
    subtotal = discount = vat_total = Decimal('0')
    for item in lines:
        pid = item.get('product_id')
        product = products.get(pid)
        if not product:
            raise SaleError(404, 'Një produkt i shportës nuk u gjet në këtë firmë')
        qty = number(item.get('quantity'), 'Sasia', Decimal('0.000001'))
        price = number(item.get('unit_price'), 'Çmimi')
        pct = number(item.get('discount_percent'), 'Zbritja', maximum=Decimal('100'))
        tax = number(item.get('vat_percent'), 'TVSH', maximum=Decimal('100'))
        line_sub = money(qty * price)
        line_discount = money(line_sub * pct / 100)
        line_vat = money((line_sub - line_discount) * tax / 100)
        packaged = bool(item.get('is_package_sale', False))
        physical_qty = qty
        if packaged:
            metadata = product.get('metadata') or {}
            if not metadata.get('is_package'):
                raise SaleError(400, 'Produkti nuk është i konfiguruar për shitje në pako')
            physical_qty *= number(metadata.get('units_per_package'), 'Njësitë për pako', Decimal('0.000001'))
        stock[pid] = stock.get(pid, Decimal('0')) + physical_qty
        result.append({
            'product_id': pid, 'product_name': (product.get('name') or '') + (' (Pako)' if packaged else ''),
            'quantity': float(qty), 'unit_price': float(price),
            'discount_percent': float(pct), 'vat_percent': float(tax),
            'subtotal': float(line_sub), 'vat_amount': float(line_vat),
            'total': float(line_sub - line_discount + line_vat),
            'is_package_sale': packaged, 'stock_quantity': float(physical_qty),
        })
        subtotal += line_sub
        discount += line_discount
        vat_total += line_vat
    total = subtotal - discount + vat_total
    coupon_discount = Decimal('0')
    code = (data.get('coupon_code') or '').strip().upper() or None
    if code:
        if not coupon or not coupon.get('active', True):
            raise SaleError(400, 'Kuponi nuk u gjet ose nuk është aktiv')
        now = now or datetime.now(timezone.utc)
        for field, before in [('valid_from', True), ('valid_until', False)]:
            value = coupon.get(field)
            if value:
                try:
                    stamp = datetime.fromisoformat(value.replace('Z', '+00:00')) if isinstance(value, str) else value
                    if stamp.tzinfo is None:
                        stamp = stamp.replace(tzinfo=timezone.utc)
                except (ValueError, AttributeError):
                    raise SaleError(400, 'Datat e kuponit janë të pavlefshme')
                if (before and now < stamp) or (not before and now > stamp):
                    raise SaleError(400, 'Kuponi nuk është aktiv për këtë datë')
        if coupon.get('max_uses') is not None and coupon.get('used_count', 0) >= coupon['max_uses']:
            raise SaleError(400, 'Kuponi ka arritur limitin e përdorimit')
        minimum = number(coupon.get('min_purchase_amount'), 'Minimumi i kuponit')
        if total < minimum:
            raise SaleError(400, f'Shuma minimale për kuponin është {minimum:.2f} EUR')
        value = number(coupon.get('discount_value'), 'Vlera e kuponit')
        if coupon.get('discount_type', 'percent') == 'percent':
            if value > 100:
                raise SaleError(400, 'Përqindja e kuponit duhet të jetë 0–100')
            coupon_discount = money(total * value / 100)
        elif coupon.get('discount_type') == 'fixed':
            coupon_discount = min(total, money(value))
        else:
            raise SaleError(400, 'Lloji i kuponit është i pavlefshëm')
        total = max(Decimal('0'), total - coupon_discount)
    if total > Decimal('999999999'):
        raise SaleError(400, 'Totali i shitjes tejkalon kufirin')
    method = data.get('payment_method')
    if method not in ('cash', 'bank', 'mixed'):
        raise SaleError(400, 'Mënyra e pagesës është e pavlefshme')
    cash = money(number(data.get('cash_amount'), 'Pagesa cash'))
    bank = money(number(data.get('bank_amount'), 'Pagesa bankare'))
    if method == 'cash' and bank:
        raise SaleError(400, 'Pagesa Cash nuk mund të përmbajë shumë bankare')
    if method == 'bank' and cash:
        raise SaleError(400, 'Pagesa Bank nuk mund të përmbajë shumë cash')
    paid = cash + bank
    debt = bool(data.get('is_debt'))
    debtor = (data.get('debtor_name') or '').strip()
    if debt:
        if not debtor:
            raise SaleError(400, 'Emri i debitorit është i detyrueshëm')
        if paid > total:
            raise SaleError(400, 'Pagesa e borxhit nuk mund të tejkalojë totalin')
        remaining = total - paid  # server is authoritative, not remaining_debt sent by client
        change = Decimal('0')
    else:
        if paid < total:
            raise SaleError(400, 'Shuma e paguar është më e vogël se totali')
        if bank > total:
            raise SaleError(400, 'Pagesa bankare nuk mund të tejkalojë totalin')
        remaining = Decimal('0')
        change = paid - total
        if change > cash:
            raise SaleError(400, 'Kusuri nuk mund të tejkalojë pagesën cash')
    return {
        'items': result, 'stock': stock, 'subtotal': float(subtotal),
        'total_discount': float(discount), 'total_vat': float(vat_total),
        'grand_total': float(total), 'grand_total_cents': int(total * 100),
        'cash_amount': float(cash), 'bank_amount': float(bank), 'change_amount': float(change),
        'remaining_debt': float(remaining), 'debtor_name': debtor or None,
        'coupon_code': code, 'coupon_discount': float(coupon_discount),
        'net_cash': float(cash - change),
    }


def request_identity(data, user, tenant_filter, header_key=None):
    body_key = data.get('request_id')
    if header_key and body_key and header_key != body_key:
        raise SaleError(400, 'Identifikuesit e kërkesës nuk përputhen')
    key = header_key or body_key or str(uuid.uuid4())  # old clients remain compatible
    if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9._:-]{8,128}', key):
        raise SaleError(400, 'Identifikuesi i kërkesës është i pavlefshëm')
    payload = {k: v for k, v in data.items() if k != 'request_id'}
    try:
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    except (ValueError, TypeError):
        raise SaleError(400, 'Të dhënat e shitjes janë të pavlefshme')
    scope = str(tenant_filter.get('tenant_id') or '__legacy__')
    identity = hashlib.sha256(f'{scope}:{user["id"]}:{key}'.encode()).hexdigest()
    return key, identity, digest, scope


def replay(record, digest):
    if record['fingerprint'] != digest:
        raise SaleError(409, 'E njëjta kërkesë është përdorur me të dhëna të tjera. Mos e përsërisni si shitje të re pa verifikim.')
    if not record.get('response'):
        raise SaleError(409, 'Shitja është në proces; provoni përsëri me të njëjtën kërkesë')
    return record['response']


async def run_mongo_transaction(database, callback):
    from pymongo.read_concern import ReadConcern
    from pymongo.write_concern import WriteConcern
    from pymongo.errors import CollectionInvalid, OperationFailure
    # Create empty helper namespaces outside the snapshot transaction. No business data changes.
    if id(database) not in _PREPARED_DATABASES:
        names = set(await database.list_collection_names())
        for name in ('sale_requests', 'sale_counters', 'sales', 'stock_movements', 'audit_logs'):
            if name not in names:
                try:
                    await database.create_collection(name)
                except CollectionInvalid:
                    pass  # another process prepared it concurrently
                except OperationFailure as error:
                    if error.code != 48:
                        raise
        _PREPARED_DATABASES.add(id(database))
    async with await database.client.start_session() as session:
        return await session.with_transaction(callback, read_concern=ReadConcern('snapshot'),
                                              write_concern=WriteConcern('majority'), max_commit_time_ms=10000)


async def save_sale(database, data, user, tenant_filter, header_key=None, transaction_runner=run_mongo_transaction):
    key, identity, digest, scope = request_identity(data, user, tenant_filter, header_key)
    ledger_query = {'_id': identity, **tenant_filter}
    existing = await database.sale_requests.find_one(ledger_query)
    if existing:
        return replay(existing, digest)

    async def work(session):
        prior = await database.sale_requests.find_one(ledger_query, session=session)
        if prior:
            return replay(prior, digest)
        drawer = await database.cash_drawers.find_one({'user_id': user['id'], 'status': 'open', **tenant_filter}, session=session)
        if not drawer:
            raise SaleError(409, 'Arka është mbyllur ose resetuar. Hapeni përsëri para shitjes.')
        products = {}
        for item in data.get('items') or []:
            pid = item.get('product_id')
            if pid not in products:
                products[pid] = await database.products.find_one({'id': pid, **tenant_filter}, session=session)
        code = (data.get('coupon_code') or '').strip().upper()
        coupon = await database.coupons.find_one({'code': code, **tenant_filter}, session=session) if code else None
        now = datetime.now(timezone.utc)
        quote = quote_sale(data, products, coupon, now)
        stamp = now.isoformat()
        # An _id unique key reserves one logical request within the same transaction.
        await database.sale_requests.insert_one({'_id': identity, 'id': identity, **tenant_filter,
            'user_id': user['id'], 'request_id': key, 'fingerprint': digest, 'created_at': stamp}, session=session)
        day = now.astimezone(ZoneInfo('Europe/Tirane')).strftime('%Y%m%d')
        counter_id = f'sales-v3:{scope}:{day}'
        counter = await database.sale_counters.find_one_and_update({'_id': counter_id},
            {'$inc': {'sequence': 1}, '$setOnInsert': {'id': counter_id, **tenant_filter, 'created_at': stamp}},
            upsert=True, return_document=True, session=session)
        receipt = f'RCP-{day}-S-{counter["sequence"]:06d}'  # separate namespace from historical count-based numbers
        sale_id = str(uuid.uuid4())
        doc = {k: v for k, v in quote.items() if k not in ('stock', 'net_cash')}
        doc.update({'id': sale_id, 'request_id': key, 'receipt_number': receipt,
            'payment_method': data['payment_method'], 'is_debt': bool(data.get('is_debt')),
            'customer_name': data.get('customer_name') or quote['debtor_name'], 'notes': data.get('notes'),
            'user_id': user['id'], 'branch_id': user.get('branch_id'), 'cash_drawer_id': drawer['id'],
            'created_at': stamp, **tenant_filter})
        for pid, physical_qty in quote['stock'].items():
            updated = await database.products.update_one({'id': pid, **tenant_filter},
                {'$inc': {'current_stock': -float(physical_qty)}, '$set': {'updated_at': stamp}}, session=session)
            if updated.matched_count != 1:
                raise SaleError(409, 'Produkti ka ndryshuar. Rifreskoni shportën.')
            await database.stock_movements.insert_one({'id': str(uuid.uuid4()), 'product_id': pid,
                'quantity': float(physical_qty), 'movement_type': 'sale', 'reason': 'Shitje',
                'sale_id': sale_id, 'user_id': user['id'], 'branch_id': user.get('branch_id'),
                'created_at': stamp, **tenant_filter}, session=session)
        await database.sales.insert_one(doc, session=session)
        if coupon:
            guard = {'code': code, **tenant_filter}
            if coupon.get('max_uses') is not None:
                guard['$or'] = [{'used_count': {'$lt': coupon['max_uses']}}, {'used_count': {'$exists': False}}]
            updated = await database.coupons.update_one(guard, {'$inc': {'used_count': 1}}, session=session)
            if updated.matched_count != 1:
                raise SaleError(409, 'Kuponi ka arritur limitin. Shitja nuk u ruajt.')
        updated = await database.cash_drawers.update_one({'id': drawer['id'], 'status': 'open', **tenant_filter},
            {'$inc': {'expected_balance': quote['net_cash'], 'sale_revision': 1}}, session=session)
        if updated.matched_count != 1:
            raise SaleError(409, 'Arka u mbyll gjatë shitjes. Shitja nuk u ruajt.')
        await database.audit_logs.insert_one({'id': str(uuid.uuid4()), 'user_id': user['id'],
            'action': 'create_sale', 'entity_type': 'sale', 'entity_id': sale_id, 'created_at': stamp,
            'details': {'total': quote['grand_total'], 'is_debt': doc['is_debt'], 'request_id': key},
            **tenant_filter}, session=session)
        await database.sale_requests.update_one(ledger_query, {'$set': {'response': doc}}, session=session)
        return doc

    # A first concurrent upsert may produce DuplicateKey rather than a retry label.
    for attempt in range(3):
        try:
            return await transaction_runner(database, work)
        except SaleError:
            raise
        except Exception as error:
            if getattr(error, 'code', None) == 11000:
                existing = await database.sale_requests.find_one(ledger_query)
                if existing:
                    return replay(existing, digest)
                if attempt < 2:
                    continue
            if getattr(error, 'code', None) in (20, 303):
                raise SaleError(503, 'Databaza nuk mbështet transaksione. Konfiguroni MongoDB Atlas/replica set; shitja nuk u ruajt.') from error
            raise SaleError(503, 'Ruajtja e shitjes nuk u konfirmua. Mos krijoni kërkesë të re; provoni përsëri me të njëjtën shportë.') from error
