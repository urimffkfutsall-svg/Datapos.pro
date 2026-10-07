"""Offline tests for separate frontend/API hosts and tenant guard flow.
Run: python3 -m unittest discover -s backend/tests -p test_tenant_api_host.py -v
JWT decode is mocked; no real MongoDB/network integration is claimed.
"""
import ast
import importlib.util
from pathlib import Path
import re
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
class HTTPException(Exception):
    def __init__(self, status_code, detail): self.status_code, self.detail = status_code, detail
old = sys.modules.get('fastapi')
stub = types.ModuleType('fastapi'); stub.HTTPException = HTTPException
sys.modules['fastapi'] = stub
spec = importlib.util.spec_from_file_location('tenant_context_test', ROOT/'tenant_context.py')
context = importlib.util.module_from_spec(spec); spec.loader.exec_module(context)
if old is None: del sys.modules['fastapi']
else: sys.modules['fastapi'] = old

def request(**headers): return types.SimpleNamespace(headers=headers)
def compile_function(path, name, env):
    tree=ast.parse((ROOT/path).read_text()); node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name==name)
    node.decorator_list=[]; node.returns=None
    for arg in node.args.args: arg.annotation=None
    node.args.defaults=[ast.Constant(None) for _ in node.args.defaults]
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(ROOT/path),'exec'),env)
    return env[name]

class Collection:
    def __init__(self, data): self.data=data
    async def find_one(self, query, projection=None):
        for doc in self.data:
            if 'id' in query and doc.get('id')==query['id']: return dict(doc)
            checks=query.get('$or',[query])
            for check in checks:
                value=check.get('name')
                if isinstance(value,dict):
                    if re.fullmatch(value['$regex'],doc['name'],re.I): return dict(doc)
                elif value==doc.get('name'): return dict(doc)
        return None

class TenantTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db=types.SimpleNamespace(tenants=Collection([{'id':'A','name':'marketnlagje'},{'id':'B','name':'other'}]),users=Collection([{'id':'user','role':'admin','tenant_id':'A'}]))
        env={'db':self.db,'re':re,'HTTPException':HTTPException,'request_tenant_subdomain':context.request_tenant_subdomain}
        self.resolve=compile_function('auth.py','_host_tenant_id',env)
        self.login_resolve=compile_function('routers/auth.py','_resolve_tenant_id_from_request',env)
        class Expired(Exception): pass
        class Invalid(Exception): pass
        env.update({'jwt':types.SimpleNamespace(decode=lambda *a,**k:{'sub':'user'},ExpiredSignatureError=Expired,InvalidTokenError=Invalid),'JWT_SECRET':'test','JWT_ALGORITHM':'HS256'})
        self.current=compile_function('auth.py','get_current_user',env)
    async def test_vercel_origin_fallback(self):
        req=request(host='backend.vercel.app',origin='https://marketnlagje.datapos.pro')
        self.assertEqual(await self.resolve(req),'A')
        self.assertEqual(await self.login_resolve(req),('A',True))
    async def test_vercel_tenant_header(self):
        req=request(**{'host':'backend.vercel.app','x-tenant-subdomain':'marketnlagje'})
        self.assertEqual(await self.resolve(req),'A')
    async def test_duplicate_identical_header_from_live_screenshot(self):
        req=request(**{'host':'datapos-pro-axbv.vercel.app','origin':'https://marketnlagje.datapos.pro','x-tenant-subdomain':'marketnlagje, marketnlagje'})
        self.assertEqual(await self.resolve(req),'A')
        self.assertEqual(await self.login_resolve(req),('A',True))
        user=await self.current(req,types.SimpleNamespace(credentials='mocked-jwt'))
        self.assertEqual(user['tenant_id'],'A')
    async def test_duplicate_identical_header_case_and_spacing(self):
        req=request(**{'host':'backend.vercel.app','x-tenant-subdomain':' Marketnlagje , marketnlagje '})
        self.assertEqual(await self.resolve(req),'A')
    def test_duplicate_different_firms_rejected(self):
        with self.assertRaises(HTTPException) as err:
            context.request_tenant_subdomain(request(**{'host':'backend.vercel.app','x-tenant-subdomain':'marketnlagje, other'}))
        self.assertEqual(err.exception.status_code,403)
    def test_duplicate_empty_value_rejected(self):
        with self.assertRaises(HTTPException):
            context.request_tenant_subdomain(request(**{'host':'backend.vercel.app','x-tenant-subdomain':'marketnlagje,'}))
    async def test_cached_headers_no_host_rewriting_needed(self):
        req=request(**{'host':'backend.vercel.app','x-forwarded-host':'backend.vercel.app','origin':'https://marketnlagje.datapos.pro','x-tenant-subdomain':'marketnlagje'})
        self.assertEqual(await self.resolve(req),'A')
    async def test_protected_request_matches_logged_in_tenant(self):
        req=request(host='backend.vercel.app',origin='https://marketnlagje.datapos.pro')
        result=await self.current(req,types.SimpleNamespace(credentials='mocked-jwt'))
        self.assertEqual(result['tenant_id'],'A')
    async def test_token_from_other_firm_rejected(self):
        req=request(host='backend.vercel.app',origin='https://other.datapos.pro')
        with self.assertRaises(HTTPException) as err: await self.current(req,types.SimpleNamespace(credentials='mocked-jwt'))
        self.assertEqual(err.exception.status_code,403)
    def test_mismatching_hint_and_origin_rejected(self):
        with self.assertRaises(HTTPException): context.request_tenant_subdomain(request(**{'host':'backend.vercel.app','origin':'https://marketnlagje.datapos.pro','x-tenant-subdomain':'other'}))
    def test_real_host_cannot_be_overridden(self):
        with self.assertRaises(HTTPException): context.request_tenant_subdomain(request(**{'host':'marketnlagje.datapos.pro','x-tenant-subdomain':'other'}))
    def test_invalid_hint_rejected(self):
        for hint in ('../other','other.datapos.pro','www','bad,other'):
            with self.assertRaises(HTTPException): context.request_tenant_subdomain(request(**{'host':'backend.vercel.app','x-tenant-subdomain':hint}))
    async def test_unknown_tenant_is_not_global_lookup(self):
        with self.assertRaises(HTTPException) as err: await self.resolve(request(host='backend.vercel.app',origin='https://unknown.datapos.pro'))
        self.assertEqual(err.exception.status_code,404)
    async def test_no_tenant_context_rejects_regular_user(self):
        with self.assertRaises(HTTPException) as err: await self.current(request(host='backend.vercel.app'),types.SimpleNamespace(credentials='mocked-jwt'))
        self.assertEqual(err.exception.status_code,403)

if __name__=='__main__': unittest.main()
