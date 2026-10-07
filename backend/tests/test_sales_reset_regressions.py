"""Offline, dependency-free regression tests against real endpoint function bodies.
Run: python3 -m unittest discover -s backend/tests -p test_sales_reset_regressions.py -v
Uses an in-memory Mongo-style fake, NOT a production MongoDB integration test.
"""
import ast
import asyncio
import copy
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
class HTTPException(Exception):
    def __init__(self, status_code, detail):
        self.status_code, self.detail = status_code, detail
        super().__init__(detail)

def load_dates():
    # Temporary stub only when FastAPI is unavailable in the test environment.
    previous = sys.modules.get('fastapi')
    stub = types.ModuleType('fastapi'); stub.HTTPException = HTTPException
    sys.modules['fastapi'] = stub
    spec = importlib.util.spec_from_file_location('regression_dates', ROOT / 'report_dates.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    if previous is None: del sys.modules['fastapi']
    else: sys.modules['fastapi'] = previous
    return module
DATES = load_dates()

def matches(doc, query):
    for key, value in query.items():
        if key == '$or':
            if not any(matches(doc, part) for part in value): return False
        elif isinstance(value, dict):
            actual = doc.get(key)
            for op, other in value.items():
                if op == '$in' and actual not in other: return False
                if op == '$gte' and (actual is None or actual < other): return False
                if op == '$lt' and (actual is None or actual >= other): return False
                if op == '$lte' and (actual is None or actual > other): return False
        elif doc.get(key) != value: return False
    return True

class Cursor:
    def __init__(self, docs): self.docs = copy.deepcopy(docs)
    def sort(self, key, direction):
        self.docs.sort(key=lambda x: x.get(key, ''), reverse=direction == -1); return self
    async def to_list(self, length): return self.docs if length is None else self.docs[:length]

class Collection:
    def __init__(self, docs=()): self.docs = copy.deepcopy(list(docs)); self.fail_insert = False
    def find(self, query, projection=None): return Cursor([x for x in self.docs if matches(x, query)])
    async def find_one(self, query, projection=None):
        return next((copy.deepcopy(x) for x in self.docs if matches(x, query)), None)
    async def count_documents(self, query): return sum(matches(x, query) for x in self.docs)
    async def insert_one(self, doc):
        if self.fail_insert: raise RuntimeError('Backup unavailable')
        self.docs.append(copy.deepcopy(doc))
    async def delete_many(self, query):
        before = len(self.docs); self.docs = [x for x in self.docs if not matches(x, query)]
        return types.SimpleNamespace(deleted_count=before-len(self.docs))
    async def delete_one(self, query):
        for i, doc in enumerate(self.docs):
            if matches(doc, query): self.docs.pop(i); return types.SimpleNamespace(deleted_count=1)
        return types.SimpleNamespace(deleted_count=0)
    async def update_one(self, query, update, upsert=False):
        doc = next((x for x in self.docs if matches(x, query)), None)
        if doc is None and upsert:
            doc = dict(query); doc.update(copy.deepcopy(update.get('$setOnInsert', {}))); self.docs.append(doc)
        if doc is not None:
            doc.update(copy.deepcopy(update.get('$set', {})))
            for k,v in update.get('$inc', {}).items(): doc[k] = doc.get(k,0) + v

class DB:
    def __init__(self):
        for name in ('users','sales','cash_drawers','stock_movements','reset_backups','products','deleted_sales'):
            setattr(self, name, Collection())

async def no_audit(*args, **kwargs): pass

def load_function(file, name, db, extra=None):
    tree = ast.parse((ROOT / file).read_text())
    node = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == name)
    node.decorator_list = []
    for arg in node.args.args: arg.annotation = None
    node.returns = None; node.args.defaults = [ast.Constant(None) for _ in node.args.defaults]
    namespace = {
        'db': db, 'datetime': datetime, 'timezone': timezone, 'HTTPException': HTTPException,
        'get_tenant_filter': lambda u: {'tenant_id': u['tenant_id']},
        'add_tenant_id': lambda doc,u: {**doc,'tenant_id':u['tenant_id']},
        'verify_password': lambda raw,hashed: raw == hashed,
        'period_bounds': DATES.period_bounds, 'date_filter': DATES.date_filter,
        'BUSINESS_TZ': DATES.BUSINESS_TZ, 'uuid': __import__('uuid'), 'log_audit': no_audit,
    }
    namespace.update(extra or {})
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])), str(ROOT / file), 'exec'), namespace)
    return namespace[name]

class RegressionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = DB(); self.admin = {'id':'admin','tenant_id':'A','role':'admin'}
        self.db.users.docs = [{**self.admin,'password_hash':'ok'}]
        self.now = datetime.now(timezone.utc).isoformat()
        self.sale = {'id':'sale-a','tenant_id':'A','created_at':self.now,'grand_total':25,
                     'total_vat':0,'total_discount':0,'items':[], 'cash_amount':30,'change_amount':5,
                     'cash_drawer_id':'drawer-a','user_id':'admin','receipt_number':'RCP-1'}
        self.db.sales.docs = [copy.deepcopy(self.sale), {**self.sale,'id':'sale-b','tenant_id':'B'}]
        self.db.cash_drawers.docs = [{'id':'drawer-a','tenant_id':'A','opened_at':self.now,
                                     'status':'open','expected_balance':125},
                                    {'id':'drawer-b','tenant_id':'B','opened_at':self.now,'status':'open'}]
        self.reset = load_function('routers/admin.py','reset_data',self.db)
    def request(self, kind='daily', password='ok', users=None):
        return types.SimpleNamespace(admin_password=password, reset_type=kind, user_ids=users)
    async def test_daily_reset_persists_and_isolates_tenant(self):
        response = await self.reset(self.request(),self.admin)
        self.assertEqual(response['deleted']['sales'],1)
        dashboard = load_function('routers/reports.py','get_dashboard',self.db)
        for _ in range(2): # fresh server query, equivalent to reload
            stats = await dashboard(None,self.admin)
            self.assertEqual(stats['total_sales_today'],0)
            self.assertEqual(stats['total_transactions_today'],0)
        self.assertEqual([s['id'] for s in self.db.sales.docs],['sale-b'])
        self.assertEqual([s['id'] for s in self.db.cash_drawers.docs],['drawer-b'])
    async def test_monthly_reset_preserves_previous_month(self):
        bounds = DATES.period_bounds('monthly')
        self.db.sales.docs.append({**self.sale,'id':'old','created_at':'2020-01-01T00:00:00+00:00'})
        await self.reset(self.request('monthly'),self.admin)
        self.assertEqual({s['id'] for s in self.db.sales.docs},{'old','sale-b'})
        self.assertEqual(self.db.reset_backups.docs[0]['reset_type'],'monthly')
    async def test_backup_failure_never_deletes(self):
        self.db.reset_backups.fail_insert = True
        with self.assertRaises(RuntimeError): await self.reset(self.request(),self.admin)
        self.assertEqual(len(self.db.sales.docs),2)
        self.assertEqual(len(self.db.cash_drawers.docs),2)
    async def test_wrong_password_never_deletes(self):
        with self.assertRaises(HTTPException) as error: await self.reset(self.request(password='bad'),self.admin)
        self.assertEqual(error.exception.status_code,401); self.assertEqual(len(self.db.sales.docs),2)
    async def test_invalid_reset_rejected(self):
        with self.assertRaises(HTTPException) as error: await self.reset(self.request('invalid'),self.admin)
        self.assertEqual(error.exception.status_code,422)
    async def test_empty_users_rejected(self):
        with self.assertRaises(HTTPException): await self.reset(self.request('user_specific'),self.admin)
    async def test_open_drawer_from_yesterday_removed_on_reset(self):
        self.db.cash_drawers.docs[0]['opened_at']='2020-01-01T00:00:00+00:00'
        await self.reset(self.request(),self.admin)
        self.assertEqual([d['id'] for d in self.db.cash_drawers.docs],['drawer-b'])
    async def test_deleted_sale_stays_absent_after_reload(self):
        delete = load_function('routers/sales.py','delete_sale',self.db)
        await delete('sale-a',self.admin)
        report = load_function('routers/reports.py','get_sales_report',self.db)
        today = datetime.now(DATES.BUSINESS_TZ).date().isoformat()
        for _ in range(2):
            result = await report(today,today,0,50,None,None,self.admin)
            self.assertEqual(result['summary']['total_revenue'],0)
            self.assertEqual(result['sales'],[])
        self.assertEqual(len(self.db.deleted_sales.docs),1)
        self.assertEqual(self.db.cash_drawers.docs[0]['expected_balance'],100)
        self.assertEqual(len(self.db.sales.docs),1)
    async def test_foreign_sale_cannot_be_deleted(self):
        delete = load_function('routers/sales.py','delete_sale',self.db)
        with self.assertRaises(HTTPException) as error: await delete('sale-b',self.admin)
        self.assertEqual(error.exception.status_code,404); self.assertEqual(len(self.db.sales.docs),2)
    async def test_repeated_deletion_does_not_deduct_twice(self):
        delete = load_function('routers/sales.py','delete_sale',self.db)
        await delete('sale-a',self.admin)
        with self.assertRaises(HTTPException): await delete('sale-a',self.admin)
        self.assertEqual(self.db.cash_drawers.docs[0]['expected_balance'],100)
    async def test_report_paginates_all_sales(self):
        self.db.sales.docs = [{**self.sale,'id':str(i)} for i in range(125)]
        report = load_function('routers/reports.py','get_sales_report',self.db)
        today = datetime.now(DATES.BUSINESS_TZ).date().isoformat()
        result = await report(today,today,100,50,None,None,self.admin)
        self.assertEqual(result['sales_count'],125); self.assertEqual(len(result['sales']),25)
    def test_inclusive_local_day_and_dst(self):
        bounds = DATES.date_filter('2026-10-25','2026-10-25')
        duration = datetime.fromisoformat(bounds['$lt']) - datetime.fromisoformat(bounds['$gte'])
        self.assertEqual(duration.total_seconds(),25*3600)
        self.assertEqual(bounds['$gte'],'2026-10-24T22:00:00+00:00')
        self.assertEqual(bounds['$lt'],'2026-10-25T23:00:00+00:00')
    def test_month_at_year_end(self):
        bounds = DATES.period_bounds('monthly',datetime(2026,12,15,tzinfo=timezone.utc))
        self.assertEqual(bounds['$lt'],'2026-12-31T23:00:00+00:00')
    def test_invalid_date_and_range(self):
        for start,end in [('bad','2026-10-07'),('2026-10-09','2026-10-07')]:
            with self.assertRaises(HTTPException): DATES.date_filter(start,end)

if __name__ == '__main__': unittest.main()
