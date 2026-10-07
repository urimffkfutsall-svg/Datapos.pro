"""Actual Decimal/atomic service with an in-memory transaction adapter.
Not a real MongoDB, Motor, HTTP/JWT or deployment integration test.
"""
import asyncio
import copy
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sale_service import quote_sale, request_identity, save_sale, SaleError


def match(row, query):
    for key, value in query.items():
        if key == '$or':
            if not any(match(row, q) for q in value): return False
        elif isinstance(value, dict):
            if '$lt' in value and not (row.get(key, 0) < value['$lt']): return False
            if '$exists' in value and ((key in row) != value['$exists']): return False
        elif row.get(key) != value: return False
    return True


class Collection:
    def __init__(self, db, name): self.db, self.name = db, name
    @property
    def rows(self): return self.db.store.setdefault(self.name, [])
    async def find_one(self, query, session=None):
        return copy.deepcopy(next((row for row in self.rows if match(row, query)), None))
    async def insert_one(self, row, session=None):
        self.db.write(session)
        if '_id' in row and any(r.get('_id') == row['_id'] for r in self.rows):
            error = RuntimeError('duplicate'); error.code = 11000; raise error
        self.rows.append(copy.deepcopy(row)); return SimpleNamespace(inserted_id=row.get('_id'))
    async def update_one(self, query, update, session=None):
        self.db.write(session)
        row = next((row for row in self.rows if match(row, query)), None)
        if row is None: return SimpleNamespace(matched_count=0)
        for key, amount in update.get('$inc', {}).items(): row[key] = row.get(key, 0) + amount
        row.update(copy.deepcopy(update.get('$set', {}))); return SimpleNamespace(matched_count=1)
    async def find_one_and_update(self, query, update, upsert=False, return_document=None, session=None):
        row = next((row for row in self.rows if match(row, query)), None)
        if row is None:
            row = {**query, **copy.deepcopy(update.get('$setOnInsert', {}))}; self.rows.append(row)
        await self.update_one(query, update, session=session)
        return copy.deepcopy(row)


class Database:
    def __init__(self):
        self.store = {'products':[{'id':'p1','tenant_id':'t1','name':'Produkt','current_stock':100}],
            'cash_drawers':[{'id':'drawer1','tenant_id':'t1','user_id':'u1','status':'open','expected_balance':10}],
            'sales':[], 'sale_requests':[], 'sale_counters':[], 'coupons':[], 'stock_movements':[], 'audit_logs':[]}
        self.lock = asyncio.Lock(); self.write_count = 0; self.fail_at = None
    def __getattr__(self, name): return Collection(self, name)
    def write(self, session):
        assert session is not None, 'mutation must participate in transaction'
        self.write_count += 1
        if self.fail_at == self.write_count: raise RuntimeError('injected write failure')


async def transaction(db, callback):
    async with db.lock:
        before = copy.deepcopy(db.store)
        try: return await callback(object())
        except Exception:
            db.store = before; raise


USER = {'id':'u1','tenant_id':'t1','branch_id':'b1'}
FILTER = {'tenant_id':'t1'}
def payload(**kwargs):
    return {'request_id':'request-0001','items':[{'product_id':'p1','quantity':2,'unit_price':1.25,'vat_percent':0,'discount_percent':0}],
        'payment_method':'cash','cash_amount':5,'bank_amount':0, **kwargs}


class QuoteTests(unittest.TestCase):
    def setUp(self): self.products = {'p1':{'name':'Produkt'}}
    def test_decimal_half_up(self):
        data = payload(items=[{'product_id':'p1','quantity':3,'unit_price':0.335,'vat_percent':18,'discount_percent':10}])
        q = quote_sale(data,self.products); self.assertEqual((q['subtotal'],q['total_discount'],q['total_vat'],q['grand_total']),(1.01,.10,.16,1.07))
    def test_negative_and_nonfinite(self):
        for field, value in [('quantity',-1),('quantity',0),('unit_price',-2),('unit_price',float('nan')),('discount_percent',101),('vat_percent',101)]:
            data=payload();data['items'][0][field]=value
            with self.subTest(field=field,value=value), self.assertRaises(SaleError): quote_sale(data,self.products)
    def test_empty_and_missing_product(self):
        for data in [payload(items=[]),payload(items=[{'product_id':'missing','quantity':1,'unit_price':1}])]:
            with self.assertRaises(SaleError): quote_sale(data,self.products)
    def test_cash_insufficient_and_bank_overpayment(self):
        for data in [payload(cash_amount=1),payload(payment_method='bank',cash_amount=0,bank_amount=3)]:
            with self.assertRaises(SaleError): quote_sale(data,self.products)
    def test_bank_and_mixed(self):
        bank=quote_sale(payload(payment_method='bank',cash_amount=0,bank_amount=2.5),self.products)
        mixed=quote_sale(payload(payment_method='mixed',cash_amount=2,bank_amount=1),self.products)
        self.assertEqual(bank['net_cash'],0); self.assertEqual(mixed['change_amount'],.5)
    def test_debt_server_calculates_balance(self):
        q=quote_sale(payload(is_debt=True,debtor_name='Klient',cash_amount=1,remaining_debt=999),self.products)
        self.assertEqual(q['remaining_debt'],1.5);self.assertEqual(q['net_cash'],1)
        with self.assertRaises(SaleError):quote_sale(payload(is_debt=True,debtor_name=''),self.products)
    def test_coupon_validation(self):
        for coupon in [None,{'active':False},{'max_uses':1,'used_count':1},{'min_purchase_amount':10},{'valid_until':'2000-01-01'},{'discount_type':'percent','discount_value':101}]:
            with self.assertRaises(SaleError):quote_sale(payload(coupon_code='TEST'),self.products,coupon)
    def test_coupon_total_and_change(self):
        q=quote_sale(payload(coupon_code='TEST'),self.products,{'discount_type':'fixed','discount_value':.5})
        self.assertEqual(q['grand_total'],2);self.assertEqual(q['change_amount'],3)
    def test_package_stock_units(self):
        q=quote_sale(payload(items=[{'product_id':'p1','quantity':2,'unit_price':10,'is_package_sale':True}],cash_amount=20),{'p1':{'name':'Produkt','metadata':{'is_package':True,'units_per_package':6}}})
        self.assertEqual(q['items'][0]['stock_quantity'],12);self.assertEqual(q['items'][0]['product_name'],'Produkt (Pako)')
    def test_identity_tenant_user_and_key_mismatch(self):
        a=request_identity(payload(),USER,FILTER);b=request_identity(payload(),{**USER,'id':'u2'},FILTER);c=request_identity(payload(),USER,{'tenant_id':'t2'})
        self.assertNotEqual(a[1],b[1]);self.assertNotEqual(a[1],c[1])
        with self.assertRaises(SaleError):request_identity(payload(),USER,FILTER,'different-key')
        with self.assertRaises(SaleError):request_identity(payload(request_id='bad'),USER,FILTER)


class AtomicTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self): self.db=Database()
    async def save(self,data=None):return await save_sale(self.db,data or payload(),USER,FILTER,transaction_runner=transaction)
    async def test_success_all_records(self):
        sale=await self.save();self.assertEqual(self.db.products.rows[0]['current_stock'],98);self.assertEqual(self.db.cash_drawers.rows[0]['expected_balance'],12.5)
        self.assertEqual(len(self.db.sales.rows),1);self.assertEqual(len(self.db.audit_logs.rows),1);self.assertEqual(len(self.db.stock_movements.rows),1)
        self.assertIn('-S-',sale['receipt_number']);self.assertEqual(self.db.audit_logs.rows[0]['tenant_id'],'t1')
    async def test_replay_once_even_after_sale_deleted(self):
        a=await self.save();b=await self.save();self.db.sales.rows.clear();c=await self.save();self.assertEqual(a,b);self.assertEqual(a,c);self.assertEqual(self.db.products.rows[0]['current_stock'],98)
    async def test_same_key_changed_payload_conflicts(self):
        await self.save()
        with self.assertRaises(SaleError) as error:await self.save(payload(cash_amount=10))
        self.assertEqual(error.exception.status,409);self.assertEqual(len(self.db.sales.rows),1)
    async def test_validation_before_mutation(self):
        before=copy.deepcopy(self.db.store)
        with self.assertRaises(SaleError):await self.save(payload(coupon_code='missing'))
        self.assertEqual(self.db.store,before);self.assertEqual(self.db.write_count,0)
    async def test_every_write_failure_rolls_back(self):
        for failure in range(1,9):
            self.db=Database();before=copy.deepcopy(self.db.store);self.db.fail_at=failure
            with self.subTest(failure=failure),self.assertRaises(SaleError):await self.save()
            self.assertEqual(self.db.store,before)
    async def test_concurrent_replays_and_distinct_sales(self):
        results=await asyncio.gather(*[self.save() for _ in range(6)])
        self.assertEqual(len({r['id'] for r in results}),1)
        other=await self.save(payload(request_id='request-0002'));self.assertNotEqual(results[0]['receipt_number'],other['receipt_number']);self.assertEqual(self.db.products.rows[0]['current_stock'],96)
    async def test_package_and_duplicate_lines_stock(self):
        self.db.products.rows[0]['metadata']={'is_package':True,'units_per_package':6}
        data=payload(items=[{'product_id':'p1','quantity':1,'unit_price':1},{'product_id':'p1','quantity':1,'unit_price':2,'is_package_sale':True}])
        await self.save(data);self.assertEqual(self.db.products.rows[0]['current_stock'],93);self.assertEqual(len(self.db.stock_movements.rows),1)
    async def test_coupon_usage_and_debt_cash(self):
        self.db.coupons.rows.append({'code':'TEST','tenant_id':'t1','discount_type':'fixed','discount_value':.5,'used_count':0,'max_uses':1})
        await self.save(payload(coupon_code='TEST',is_debt=True,debtor_name='Klient',cash_amount=1))
        self.assertEqual(self.db.coupons.rows[0]['used_count'],1);self.assertEqual(self.db.cash_drawers.rows[0]['expected_balance'],11)
    async def test_closed_drawer_and_wrong_tenant(self):
        self.db.cash_drawers.rows[0]['status']='closed'
        with self.assertRaises(SaleError):await self.save()
        with self.assertRaises(SaleError):await save_sale(self.db,payload(),USER,{'tenant_id':'t2'},transaction_runner=transaction)
        self.assertEqual(len(self.db.sales.rows),0)
    async def test_no_transaction_support_fails_closed(self):
        async def unsupported(db,cb):error=RuntimeError('standalone');error.code=20;raise error
        before=copy.deepcopy(self.db.store)
        with self.assertRaises(SaleError) as error:await save_sale(self.db,payload(),USER,FILTER,transaction_runner=unsupported)
        self.assertEqual(error.exception.status,503);self.assertEqual(self.db.store,before)

if __name__=='__main__':unittest.main()
