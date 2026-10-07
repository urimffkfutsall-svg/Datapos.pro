"""Global public sponsor directory, explicitly managed by the super-administrator."""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Response
from datetime import datetime, timezone
import base64
import uuid
from database import db
from auth import get_current_user
from partner_assets import PartnerWrite, normalize_logo, decode_logo, public_partner, MAX_UPLOAD

router = APIRouter(prefix='/partners', tags=['Sponsorat dhe firmat'])


def require_super(current_user):
    if current_user.get('role') != 'super_admin':
        raise HTTPException(status_code=403, detail='Vetëm superadministratori mund të menaxhojë sponsorët dhe firmat.')


@router.get('/public')
async def public_list(response: Response):
    response.headers['Cache-Control'] = 'no-store'
    records = await db.partners.find({'is_active': True}, {'_id': 0, 'logo_bytes': 0}).sort([('sort_order', 1), ('name', 1)]).to_list(200)
    return [public_partner(record) for record in records]


@router.get('')
async def admin_list(current_user: dict = Depends(get_current_user)):
    require_super(current_user)
    records = await db.partners.find({}, {'_id': 0, 'logo_bytes': 0}).sort([('sort_order', 1), ('name', 1)]).to_list(200)
    return [dict(public_partner(r), is_active=r.get('is_active', False), sort_order=r.get('sort_order', 0)) for r in records]


@router.post('/logo-upload')
async def upload_partner_logo(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    require_super(current_user)
    try:
        logo = normalize_logo(await file.read(MAX_UPLOAD + 1))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {'logo_data': 'data:image/png;base64,' + base64.b64encode(logo).decode('ascii')}


@router.post('')
async def create_partner(data: PartnerWrite, current_user: dict = Depends(get_current_user)):
    require_super(current_user)
    if await db.partners.count_documents({}) >= 200:
        raise HTTPException(status_code=400, detail='Maksimumi është 200 sponsorë/firma; hiqni një regjistrim para shtimit.')
    if not data.logo_data:
        raise HTTPException(status_code=400, detail='Ngarkoni logon para ruajtjes.')
    try:
        logo = decode_logo(data.logo_data)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    now = datetime.now(timezone.utc).isoformat()
    record = dict(data.model_dump(exclude={'logo_data'}), id=str(uuid.uuid4()), has_logo=True, logo_bytes=logo,
                  created_at=now, updated_at=now, created_by=current_user.get('id'))
    await db.partners.insert_one(record)
    return dict(public_partner(record), is_active=record['is_active'], sort_order=record['sort_order'])


@router.put('/{partner_id}')
async def update_partner(partner_id: str, data: PartnerWrite, current_user: dict = Depends(get_current_user)):
    require_super(current_user)
    changes = data.model_dump(exclude={'logo_data'})
    if data.logo_data:
        try:
            changes['logo_bytes'] = decode_logo(data.logo_data)
            changes['has_logo'] = True
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
    changes['updated_at'] = datetime.now(timezone.utc).isoformat()
    result = await db.partners.update_one({'id': partner_id}, {'$set': changes})
    if not result.matched_count:
        raise HTTPException(status_code=404, detail='Sponsori/firma nuk u gjet.')
    record = await db.partners.find_one({'id': partner_id}, {'_id': 0, 'logo_bytes': 0})
    if not record:
        raise HTTPException(status_code=404, detail='Regjistrimi u fshi gjatë përditësimit.')
    return dict(public_partner(record), is_active=record['is_active'], sort_order=record['sort_order'])


@router.delete('/{partner_id}')
async def delete_partner(partner_id: str, current_user: dict = Depends(get_current_user)):
    require_super(current_user)
    result = await db.partners.delete_one({'id': partner_id})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail='Sponsori/firma nuk u gjet.')
    return {'success': True}


@router.get('/{partner_id}/logo')
async def partner_logo(partner_id: str):
    record = await db.partners.find_one({'id': partner_id, 'is_active': True}, {'logo_bytes': 1, '_id': 0})
    if not record or not record.get('logo_bytes'):
        raise HTTPException(status_code=404, detail='Logoja nuk u gjet.')
    return Response(content=bytes(record['logo_bytes']), media_type='image/png', headers={
        'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
        'Content-Security-Policy': "default-src 'none'; sandbox",
    })


@router.get('/{partner_id}/admin-logo')
async def admin_partner_logo(partner_id: str, current_user: dict = Depends(get_current_user)):
    require_super(current_user)
    record = await db.partners.find_one({'id': partner_id}, {'logo_bytes': 1, '_id': 0})
    if not record or not record.get('logo_bytes'):
        raise HTTPException(status_code=404, detail='Logoja nuk u gjet.')
    # An authenticated fetch returns a data URI for the edit preview, even when hidden publicly.
    return {'logo_data': 'data:image/png;base64,' + base64.b64encode(bytes(record['logo_bytes'])).decode('ascii')}
