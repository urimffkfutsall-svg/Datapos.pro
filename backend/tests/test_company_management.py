"""Exercise actual tenant models/routes offline with an in-memory Mongo-style DB.
No MongoDB, network, FastAPI HTTP dispatch or password cryptography is simulated as real.
Run: python3 -m unittest discover -s backend/tests -p test_company_management.py -v
"""
import ast
import base64
import copy
import importlib.util
import io
from pathlib import Path
import re
import types
import unittest
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, ValidationError

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('company_models',ROOT/'models.py')
models=importlib.util.module_from_spec(spec);spec.loader.exec_module(models)
class HTTPException(Exception):
    def __init__(self,status_code,detail): self.status_code,self.detail=status_code,detail

def matches(doc,query):
    for key,value in query.items():
        if key=='$or':
            if not any(matches(doc,q) for q in value): return False
        elif isinstance(value,dict):
            v=doc.get(key)
            if '$in' in value and v not in value['$in']: return False
            if '$ne' in value and v==value['$ne']: return False
            if '$regex' in value and not re.fullmatch(value['$regex'],str(v),re.I): return False
        elif doc.get(key)!=value: return False
    return True
class Cursor:
    def __init__(self,rows): self.rows=copy.deepcopy(rows)
    def sort(self,key,direction): self.rows.sort(key=lambda row:str(row.get(key,'')),reverse=direction==-1);return self
    async def to_list(self,length): return self.rows if length is None else self.rows[:length]
class Collection:
    def __init__(self): self.rows=[];self.fail_insert=False;self.on_update=None
    def find(self,q,p=None):return Cursor([r for r in self.rows if matches(r,q)])
    async def find_one(self,q,p=None):return next((copy.deepcopy(r) for r in self.rows if matches(r,q)),None)
    async def count_documents(self,q):return sum(matches(r,q) for r in self.rows)
    async def insert_one(self,r):
        if self.fail_insert:raise RuntimeError('Write unavailable')
        r.setdefault('_id',str(uuid.uuid4()));self.rows.append(copy.deepcopy(r))
    async def update_one(self,q,u):
        for r in self.rows:
            if matches(r,q):r.update(copy.deepcopy(u.get('$set',{})))
        if self.on_update:self.on_update(q,u)
    async def delete_many(self,q):
        before=len(self.rows);self.rows=[r for r in self.rows if not matches(r,q)]
        return types.SimpleNamespace(deleted_count=before-len(self.rows))
    async def delete_one(self,q):
        for i,r in enumerate(self.rows):
            if matches(r,q):self.rows.pop(i);return types.SimpleNamespace(deleted_count=1)
        return types.SimpleNamespace(deleted_count=0)
class DB:
    def __init__(self):self.collections={}
    def __getattr__(self,name):return self[name]
    def __getitem__(self,name):return self.collections.setdefault(name,Collection())
    async def list_collection_names(self):return list(self.collections)
class FakeQR:
    last=None
    def __init__(self,**kw):pass
    def add_data(self,value):FakeQR.last=value
    def make(self,**kw):pass
    def make_image(self,**kw):return self
    def save(self,buffer,**kw):buffer.write(b'fake image')
async def audit(*args,**kwargs):pass

def load_routes(db):
    tree=ast.parse((ROOT/'routers/tenants.py').read_text())
    tree.body=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom)) and not (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='router' for t in n.targets))]
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):node.decorator_list=[]
    env=dict(db=db,re=re,uuid=uuid,datetime=datetime,timezone=timezone,relativedelta=relativedelta,BaseModel=BaseModel,Optional=Optional,List=List,HTTPException=HTTPException,Depends=lambda *x:None,get_current_user=None,hash_password=lambda value:'hash:'+value,log_audit=audit,io=io,base64=base64,qrcode=types.SimpleNamespace(QRCode=FakeQR,constants=types.SimpleNamespace(ERROR_CORRECT_L=1)))
    for name in ('TenantCreate','TenantUpdate','TenantResponse','TenantPublicInfo','TenantStatus','UserRole'):env[name]=getattr(models,name)
    exec(compile(ast.fix_missing_locations(tree),str(ROOT/'routers/tenants.py'),'exec'),env)
    return env

class CompanyTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):self.db=DB();self.routes=load_routes(self.db);self.super={'id':'root','role':'super_admin'}
    def create_model(self,**kw):return models.TenantCreate(**dict(name='marketnlagje',company_name='Market',email='market@example.com',admin_username='admin',admin_password='test-only',admin_full_name='Administrator',**kw))
    async def seed(self):
        await self.db.tenants.insert_one({'id':'A','name':'marketnlagje','company_name':'Market','email':'a@example.com','status':'active','primary_color':'#000000','secondary_color':'#ffffff','created_at':datetime.now(timezone.utc).isoformat()})
    async def test_create_company_and_admin(self):
        result=await self.routes['create_tenant'](self.create_model(),self.super)
        self.assertEqual(result.name,'marketnlagje');self.assertEqual(result.users_count,1)
        self.assertEqual(self.db.users.rows[0]['tenant_id'],result.id)
        self.assertNotIn('password_hash',result.model_dump())
    async def test_selected_subscription_is_saved(self):
        model=self.create_model();model.subscription_months=3
        result=await self.routes['create_tenant'](model,self.super)
        self.assertEqual(result.status,'active');self.assertGreater(datetime.fromisoformat(result.subscription_expires),datetime.now(timezone.utc))
    async def test_admin_write_failure_rolls_back_company(self):
        self.db.users.fail_insert=True
        with self.assertRaises(RuntimeError):await self.routes['create_tenant'](self.create_model(),self.super)
        self.assertEqual(self.db.tenants.rows,[])
    async def test_hash_failure_does_not_create_company(self):
        def fail(value):raise ValueError('Bad hash input')
        self.routes['hash_password']=fail
        with self.assertRaises(ValueError):await self.routes['create_tenant'](self.create_model(),self.super)
        self.assertEqual(self.db.tenants.rows,[])
    async def test_duplicate_company_rejected(self):
        await self.routes['create_tenant'](self.create_model(),self.super)
        with self.assertRaises(HTTPException):await self.routes['create_tenant'](self.create_model(),self.super)
        self.assertEqual(len(self.db.tenants.rows),1)
    async def test_non_super_cannot_create_or_delete(self):
        for name,args in [('create_tenant',(self.create_model(),{'id':'x','role':'admin'})),('delete_tenant',('A',{'id':'x','role':'admin'}))]:
            with self.assertRaises(HTTPException) as err:await self.routes[name](*args)
            self.assertEqual(err.exception.status_code,403)
    async def test_delete_archives_all_collections_and_isolates_firms(self):
        await self.seed()
        for name in ('users','products','sales','debts','coupons','warranties','orders','warehouses','reset_backups'):
            await self.db[name].insert_one({'id':name+'A','tenant_id':'A'})
            await self.db[name].insert_one({'id':name+'B','tenant_id':'B'})
        result=await self.routes['delete_tenant']('A',self.super)
        self.assertTrue(result['backup_id']);self.assertEqual(self.db.tenants.rows,[])
        for name in result['deleted']:self.assertTrue(all(r['tenant_id']=='B' for r in self.db[name].rows))
        records=[r for r in self.db.tenant_deletion_backups.rows if r.get('kind')=='record']
        self.assertEqual(len(records),9)
        self.assertEqual(self.db.tenant_deletion_backups.rows[0]['status'],'deleted')
    async def test_backup_failure_prevents_deletion(self):
        await self.seed();await self.db.sales.insert_one({'id':'s','tenant_id':'A'})
        self.db.tenant_deletion_backups.fail_insert=True
        with self.assertRaises(RuntimeError):await self.routes['delete_tenant']('A',self.super)
        self.assertEqual(len(self.db.sales.rows),1);self.assertEqual(len(self.db.tenants.rows),1)
    async def test_concurrent_data_does_not_claim_success(self):
        await self.seed();await self.db.sales.insert_one({'id':'s','tenant_id':'A'})
        def concurrent(q,u):
            if u.get('$set',{}).get('deleting'):self.db.sales.rows.append({'_id':'late','id':'late','tenant_id':'A'})
        self.db.tenants.on_update=concurrent
        with self.assertRaises(HTTPException) as err:await self.routes['delete_tenant']('A',self.super)
        self.assertEqual(err.exception.status_code,409);self.assertEqual(len(self.db.tenants.rows),1)
    async def test_update_company_and_list(self):
        await self.seed()
        result=await self.routes['update_tenant']('A',models.TenantUpdate(company_name='Updated'),self.super)
        self.assertEqual(result.company_name,'Updated')
        self.assertEqual(len(await self.routes['get_all_tenants'](self.super)),1)
    async def test_duplicate_email_on_update_rejected(self):
        await self.seed();await self.db.tenants.insert_one({'id':'B','email':'other@example.com'})
        with self.assertRaises(HTTPException):await self.routes['update_tenant']('A',models.TenantUpdate(email='other@example.com'),self.super)
    async def test_super_can_change_admin_password_without_leaking_it(self):
        await self.db.users.insert_one({'id':'u','tenant_id':'A','role':'admin','password_hash':'old'})
        result=await self.routes['update_tenant_user']('A','u',self.routes['TenantUserUpdate'](password='new-test'),self.super)
        self.assertEqual(self.db.users.rows[0]['password_hash'],'hash:new-test');self.assertNotIn('password',str(result))
    async def test_user_update_cannot_target_other_firm_or_promote_super(self):
        await self.db.users.insert_one({'id':'u','tenant_id':'B','role':'admin'})
        with self.assertRaises(HTTPException):await self.routes['update_tenant_user']('A','u',self.routes['TenantUserUpdate'](password='new'),self.super)
        with self.assertRaises(HTTPException):await self.routes['update_tenant_user']('B','u',self.routes['TenantUserUpdate'](role='super_admin'),self.super)
    def test_tenant_model_rejects_invalid_input(self):
        data=self.create_model().model_dump()
        for field,value in [('name','bad.example.com'),('name','www'),('name','bad,other'),('name','-bad'),('email','invalid'),('admin_password',''),('company_name',' ')]:
            with self.assertRaises(ValidationError):models.TenantCreate(**{**data,field:value})
    def load_async(self, file, name, extra=None):
        tree=ast.parse((ROOT/file).read_text())
        node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name==name)
        node.decorator_list=[];node.returns=None
        for arg in node.args.args:arg.annotation=None
        node.args.defaults=[ast.Constant(None) for _ in node.args.defaults]
        env={'db':self.db,'HTTPException':HTTPException,'hash_password':lambda value:'hash:'+value,'logger':types.SimpleNamespace(info=lambda *a:None,warning=lambda *a:None,exception=lambda *a:None),'UserRole':models.UserRole,'get_tenant_filter':lambda u:{'tenant_id':u['tenant_id']}}
        env.update(extra or {})
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(ROOT/file),'exec'),env)
        return env[name]
    async def test_bootstrap_never_overwrites_existing_credentials(self):
        await self.db.users.insert_one({'id':'root','role':'super_admin','username':'existing','password_hash':'unchanged'})
        await self.load_async('server.py','init_super_admin')()
        self.assertEqual(self.db.users.rows[0]['password_hash'],'unchanged')
    async def test_bootstrap_missing_environment_does_not_create_default_account(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ,{'BOOTSTRAP_ADMIN_USERNAME':'','BOOTSTRAP_ADMIN_PASSWORD':''}):await self.load_async('server.py','init_super_admin')()
        self.assertEqual(self.db.users.rows,[])
    async def test_bootstrap_provisions_once_from_environment(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ,{'BOOTSTRAP_ADMIN_USERNAME':'test-bootstrap','BOOTSTRAP_ADMIN_PASSWORD':'not-a-real-password'}):
            init=self.load_async('server.py','init_super_admin');await init();await init()
        self.assertEqual(len(self.db.users.rows),1)
    async def test_legacy_public_password_reset_is_disabled(self):
        with self.assertRaises(HTTPException) as err:await self.load_async('routers/admin.py','init_super_admin')()
        self.assertEqual(err.exception.status_code,410)
    async def test_regular_admin_cannot_create_super_admin(self):
        with self.assertRaises(HTTPException) as err:await self.load_async('routers/users.py','create_user')(types.SimpleNamespace(role=models.UserRole.SUPER_ADMIN),{'id':'admin','tenant_id':'A'})
        self.assertEqual(err.exception.status_code,403)
    async def test_regular_admin_cannot_promote_user_to_super_admin(self):
        with self.assertRaises(HTTPException) as err:await self.load_async('routers/users.py','update_user')('user',types.SimpleNamespace(role=models.UserRole.SUPER_ADMIN),{'id':'admin','tenant_id':'A'})
        self.assertEqual(err.exception.status_code,403)
    def test_qr_link_has_no_literal_braces(self):
        self.routes['generate_whatsapp_qr']('+383 44 123 456');self.assertEqual(FakeQR.last,'https://wa.me/38344123456')

if __name__=='__main__':unittest.main()
