"""Actual partner models/image functions and extracted route functions with an in-memory DB.
This is not a FastAPI HTTP, authentication-token or real MongoDB integration test.
"""
import ast
import base64
import copy
import io
import sys
import types
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image
from pydantic import ValidationError
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from partner_assets import PartnerWrite, normalize_logo, decode_logo, public_partner, MAX_UPLOAD

class HTTPException(Exception):
    def __init__(self, status_code, detail): self.status_code, self.detail = status_code, detail
class Response:
    def __init__(self, content=b'', media_type=None, headers=None): self.content, self.media_type, self.headers = content, media_type, headers or {}
class Cursor:
    def __init__(self, rows): self.rows = copy.deepcopy(rows)
    def sort(self, spec):
        for field, direction in reversed(spec): self.rows.sort(key=lambda r:r.get(field, ''), reverse=direction<0)
        return self
    async def to_list(self, limit): return self.rows[:limit]
class Collection:
    def __init__(self): self.rows=[]
    def match(self,r,q): return all(r.get(k)==v for k,v in q.items())
    def find(self,q,p=None): return Cursor([r for r in self.rows if self.match(r,q)])
    async def find_one(self,q,p=None): return next((copy.deepcopy(r) for r in self.rows if self.match(r,q)),None)
    async def count_documents(self,q): return sum(self.match(r,q) for r in self.rows)
    async def insert_one(self,r): self.rows.append(copy.deepcopy(r))
    async def update_one(self,q,updates):
        for r in self.rows:
            if self.match(r,q): r.update(copy.deepcopy(updates['$set']));return types.SimpleNamespace(matched_count=1)
        return types.SimpleNamespace(matched_count=0)
    async def delete_one(self,q):
        for r in self.rows:
            if self.match(r,q):self.rows.remove(r);return types.SimpleNamespace(deleted_count=1)
        return types.SimpleNamespace(deleted_count=0)

raw=io.BytesIO();Image.new('RGBA',(600,400),(20,40,50,0)).save(raw,format='PNG');RAW=raw.getvalue()
LOGO='data:image/png;base64,'+base64.b64encode(normalize_logo(RAW)).decode()
ADMIN={'id':'super-test','role':'super_admin'}
def routes(db):
    tree=ast.parse((ROOT/'routers/partners.py').read_text());nodes=[]
    for n in tree.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):n.decorator_list=[];nodes.append(n)
    ns=dict(db=db,PartnerWrite=PartnerWrite,normalize_logo=normalize_logo,decode_logo=decode_logo,public_partner=public_partner,MAX_UPLOAD=MAX_UPLOAD,HTTPException=HTTPException,Response=Response,UploadFile=object,Depends=lambda x:None,File=lambda *a:None,get_current_user=None,base64=base64,uuid=uuid,datetime=datetime,timezone=timezone)
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'partner_routes','exec'),ns);return ns

class PartnerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):self.db=types.SimpleNamespace(partners=Collection());self.api=routes(self.db)
    async def create(self,**changes):return await self.api['create_partner'](PartnerWrite(name='Market Prova',logo_data=LOGO,**changes),ADMIN)
    async def test_create_persists_png_in_database(self):
        out=await self.create();self.assertTrue(out['logo_url']);self.assertTrue(self.db.partners.rows[0]['logo_bytes'].startswith(b'\x89PNG'));self.assertNotIn('logo_bytes',out)
    async def test_public_allowlist(self):
        await self.create();self.db.partners.rows[0].update(tenant_id='private',password='private');response=Response();out=await self.api['public_list'](response)
        self.assertNotIn('tenant_id',out[0]);self.assertNotIn('password',out[0]);self.assertNotIn('created_by',out[0]);self.assertEqual(response.headers['Cache-Control'],'no-store')
    async def test_hidden_is_not_public_or_retrievable(self):
        out=await self.create(is_active=False);self.assertEqual(await self.api['public_list'](Response()),[])
        with self.assertRaises(HTTPException) as caught:await self.api['partner_logo'](out['id'])
        self.assertEqual(caught.exception.status_code,404)
        self.assertTrue((await self.api['admin_partner_logo'](out['id'],ADMIN))['logo_data'])
    async def test_update_preserves_existing_logo(self):
        out=await self.create();before=self.db.partners.rows[0]['logo_bytes'];await self.api['update_partner'](out['id'],PartnerWrite(name='Market Ndryshuar',address='Prishtinë'),ADMIN)
        self.assertEqual(self.db.partners.rows[0]['logo_bytes'],before);self.assertEqual(self.db.partners.rows[0]['address'],'Prishtinë')
    async def test_delete_removes_profile_and_logo(self):
        out=await self.create();await self.api['delete_partner'](out['id'],ADMIN);self.assertEqual(self.db.partners.rows,[])
        with self.assertRaises(HTTPException):await self.api['partner_logo'](out['id'])
    async def test_non_super_writes_and_admin_reads_forbidden(self):
        user={'role':'admin'};data=PartnerWrite(name='Not allowed',logo_data=LOGO)
        for name,args in [('admin_list',(user,)),('create_partner',(data,user)),('update_partner',('x',data,user)),('delete_partner',('x',user)),('admin_partner_logo',('x',user))]:
            with self.assertRaises(HTTPException) as c:await self.api[name](*args)
            self.assertEqual(c.exception.status_code,403)
    async def test_upload_checks_role_before_reading(self):
        class File:
            async def read(self,n):raise AssertionError('unauthorized read')
        with self.assertRaises(HTTPException) as c:await self.api['upload_partner_logo'](File(),{'role':'cashier'})
        self.assertEqual(c.exception.status_code,403)
    async def test_upload_returns_normalized_png(self):
        class File:
            async def read(self,n):return RAW
        out=await self.api['upload_partner_logo'](File(),ADMIN);self.assertTrue(out['logo_data'].startswith('data:image/png;base64,'))
    async def test_logo_response_not_cached_or_sniffed(self):
        out=await self.create();response=await self.api['partner_logo'](out['id']);self.assertEqual(response.media_type,'image/png');self.assertEqual(response.headers['X-Content-Type-Options'],'nosniff')
    async def test_missing_records_404(self):
        for name,args in [('update_partner',('missing',PartnerWrite(name='Missing'),ADMIN)),('delete_partner',('missing',ADMIN))]:
            with self.assertRaises(HTTPException) as c:await self.api[name](*args)
            self.assertEqual(c.exception.status_code,404)
    def test_social_platform_rejects_unsafe_urls(self):
        for url in ['javascript:alert(1)','http://facebook.com/test','https://facebook.com.evil.test/a','https://facebook.com@evil.test/a','https://evil.test/a']:
            with self.assertRaises(ValidationError):PartnerWrite(name='Test',facebook=url)
        self.assertTrue(PartnerWrite(name='Test',facebook='https://www.facebook.com/test').facebook)
    def test_reject_active_or_corrupt_image(self):
        for raw in [b'<svg onload="evil()"/>',b'not an image',b'x'*(MAX_UPLOAD+1)]:
            with self.assertRaises(ValueError):normalize_logo(raw)
    def test_logo_keeps_transparency_and_bounded_size(self):
        image=Image.open(io.BytesIO(decode_logo(LOGO)));self.assertLessEqual(image.width,512);self.assertLessEqual(image.height,320);self.assertEqual(image.getpixel((0,0))[3],0)
    def test_no_unknown_fields_or_invalid_name_order(self):
        for data in [dict(name='x'),dict(name='okay',sort_order=-1),dict(name='okay',tenant_id='leak')]:
            with self.assertRaises(ValidationError):PartnerWrite(**data)
    async def test_logo_required_on_create(self):
        with self.assertRaises(HTTPException):await self.api['create_partner'](PartnerWrite(name='No logo'),ADMIN)
    def test_server_and_ui_routes_registered(self):
        self.assertIn('app.include_router(partners.router, prefix="/api")',(ROOT/'server.py').read_text())
        app=(ROOT.parent/'frontend/src/App.js').read_text();self.assertIn('path="partners" element={<ProtectedRoute allowedRoles={[\'super_admin\']}',app)

if __name__=='__main__':unittest.main()
