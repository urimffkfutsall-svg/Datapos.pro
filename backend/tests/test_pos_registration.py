"""Actual approval code, actual Pydantic models; in-memory DB, no HTTP/Mongo driver."""
import ast, copy, hmac, importlib.util, math, types, unittest, uuid
from pathlib import Path
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict, ValidationError
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('registration_models',ROOT/'models.py');models=importlib.util.module_from_spec(spec);spec.loader.exec_module(models)
class HTTPException(Exception):
 def __init__(self,status_code,detail):self.status_code,self.detail=status_code,detail
class Cursor:
 def __init__(self,rows):self.rows=rows
 async def to_list(self,n):return copy.deepcopy(self.rows[:n])
def matches(r,q):
 return all((r.get(k)!=v['$ne'] if isinstance(v,dict) and '$ne' in v else r.get(k,0)<v['$lt'] if isinstance(v,dict) and '$lt' in v else r.get(k)==v) for k,v in q.items())
class Collection:
 def __init__(self):self.rows=[]
 def find(self,q,p=None):return Cursor([r for r in self.rows if matches(r,q)])
 async def find_one(self,q,p=None):return next((copy.deepcopy(r) for r in self.rows if matches(r,q)),None)
 async def delete_many(self,q):self.rows=[r for r in self.rows if not matches(r,q)]
 async def update_one(self,q,u,upsert=False):
  row=next((r for r in self.rows if matches(r,q)),None);created=False
  if row is None and upsert:row=copy.deepcopy(q);row.update(copy.deepcopy(u.get('$setOnInsert',{})));self.rows.append(row);created=True
  if row is not None:
   for k,v in u.get('$inc',{}).items():row[k]=row.get(k,0)+v
  return types.SimpleNamespace(upserted_id=row.get('_id') if created else None)
class DB:
 def __init__(self):self.users=Collection();self.products=Collection();self.pos_pin_attempts=Collection()
class ApprovalTests(unittest.IsolatedAsyncioTestCase):
 def setUp(self):
  self.db=DB();self.audit=[];self.user={'id':'cash','tenant_id':'A','role':'cashier','branch_id':'BA'}
  self.db.users.rows=[{'id':'adminA','tenant_id':'A','role':'admin','is_active':True,'pin':'1357'},{'id':'adminB','tenant_id':'B','role':'admin','is_active':True,'pin':'2468'},{'id':'cashA','tenant_id':'A','role':'cashier','pin':'1111'},{'id':'managerA','tenant_id':'A','role':'manager','pin':'2222'},{'id':'disabledA','tenant_id':'A','role':'admin','is_active':False,'pin':'3333'}]
  async def audit(*a,**kw):self.audit.append((a,kw))
  tree=ast.parse((ROOT/'pos_registration.py').read_text());tree.body=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))]
  env=dict(db=self.db,hmac=hmac,math=math,time=types.SimpleNamespace(time=lambda:100000),uuid=uuid,datetime=datetime,timezone=timezone,HTTPException=HTTPException,BaseModel=BaseModel,Field=Field,ConfigDict=ConfigDict,log_audit=audit,ProductCreate=models.ProductCreate,Product=models.Product,ProductResponse=models.ProductResponse)
  exec(compile(tree,'actual-pos-registration','exec'),env);self.env=env
 def request(self,pin='1357',**kw):return self.env['ApprovedProductRequest'](admin_pin=pin,product=dict(name='Ujë',barcode='1234567890123',sale_price=0.5,purchase_price=0.2,vat_rate=18,initial_stock=0,**kw))
 async def call(self,req=None,user=None):return await self.env['register_approved_product'](req or self.request(),user or self.user)
 async def test_valid_pin_creates_tenant_scoped_product_and_audit(self):
  p=await self.call();self.assertEqual(p.name,'Ujë');self.assertEqual(self.db.products.rows[0]['tenant_id'],'A');self.assertEqual(p.branch_id,'BA');self.assertEqual(p.current_stock,0)
  self.assertEqual(self.audit[0][0][0],'cash');self.assertEqual(self.audit[0][0][4]['approved_by'],'adminA');self.assertNotIn('1357',str(self.db.products.rows)+str(self.db.pos_pin_attempts.rows)+str(self.audit))
 async def test_wrong_foreign_cashier_manager_and_inactive_pins_fail(self):
  for pin in ['0000','2468','1111','2222','3333']:
   with self.assertRaises(HTTPException) as e:await self.call(self.request(pin))
   self.assertEqual(e.exception.status_code,422)
  self.assertEqual(self.db.products.rows,[])
 async def test_throttled_after_five_failed_attempts(self):
  for _ in range(5):
   with self.assertRaises(HTTPException):await self.call(self.request('0000'))
  with self.assertRaises(HTTPException) as e:await self.call()
  self.assertEqual(e.exception.status_code,429);self.assertFalse(self.db.products.rows)
 async def test_successful_approvals_do_not_exhaust_attempt_budget(self):
  for i in range(8):
   req=self.request();req.product.barcode=str(10000+i);await self.call(req)
  self.assertEqual(len(self.db.products.rows),8)
 async def test_duplicate_does_not_create_or_audit_twice(self):
  await self.call()
  with self.assertRaises(HTTPException) as e:await self.call()
  self.assertEqual(e.exception.status_code,409);self.assertEqual(len(self.db.products.rows),1);self.assertEqual(len(self.audit),1)
 async def test_duplicate_pin_is_ambiguous_and_fails_closed(self):
  self.db.users.rows.append({'id':'other','tenant_id':'A','role':'admin','pin':'1357'})
  with self.assertRaises(HTTPException) as e:await self.call()
  self.assertEqual(e.exception.status_code,422);self.assertFalse(self.db.products.rows)
 async def test_tenant_and_role_are_required(self):
  for u in [{'id':'super','role':'super_admin'},{'id':'bad','role':'cashier'},{'id':'bad','role':'viewer','tenant_id':'A'}]:
   with self.assertRaises(HTTPException) as e:await self.call(user=u)
   self.assertEqual(e.exception.status_code,403)
 async def test_other_branch_denied(self):
  with self.assertRaises(HTTPException) as e:await self.call(self.request(branch_id='BB'))
  self.assertEqual(e.exception.status_code,403)
 async def test_invalid_prices_stock_names_denied(self):
  for key,value in [('sale_price',-1),('sale_price',float('nan')),('purchase_price',float('inf')),('vat_rate',101),('initial_stock',2),('name',' '),('barcode','')]:
   req=self.request();setattr(req.product,key,value)
   with self.assertRaises(HTTPException) as e:await self.call(req)
   self.assertEqual(e.exception.status_code,422)
  self.assertFalse(self.db.products.rows)
 def test_pin_and_request_model_strictness(self):
  for pin in ['','abc1','1'*13]:
   with self.assertRaises(ValidationError):self.request(pin)
  with self.assertRaises(ValidationError):self.env['ApprovedProductRequest'](admin_pin='1357',product={},approved=True)
 def test_endpoint_still_requires_authenticated_session_and_old_role_guard(self):
  src=(ROOT/'routers/products.py').read_text();self.assertIn('current_user: dict = Depends(get_current_user)',src);self.assertIn('Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))',src);self.assertIn('return await register_approved_product(request, current_user)',src)
 async def test_user_read_endpoints_never_expose_admin_pins(self):
  tree=ast.parse((ROOT/'routers/users.py').read_text());tree.body=[n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name in ('get_users','get_user')]
  for n in tree.body:n.decorator_list=[]
  env=dict(db=self.db,List=list,UserRole=models.UserRole,UserResponse=models.UserResponse,HTTPException=HTTPException,Depends=lambda *a:None,get_current_user=None,require_role=lambda *a:None,get_tenant_filter=lambda u:{'tenant_id':u['tenant_id']})
  exec(compile(tree,'actual-user-read-routes','exec'),env)
  self.db.users.rows=[dict(id='a',tenant_id='A',username='admin',full_name='Admin',role='admin',is_active=True,created_at='2026-10-09T00:00:00Z',pin='1357')]
  rows=await env['get_users'](None,None,self.user);self.assertIsNone(rows[0].pin)
  row=await env['get_user']('a',self.user);self.assertIsNone(row.pin)
if __name__=='__main__':unittest.main()
