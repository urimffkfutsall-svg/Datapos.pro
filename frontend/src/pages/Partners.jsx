import React, { useCallback, useEffect, useRef, useState } from 'react';
import { api, useAuth } from '../App';
import { toast } from 'sonner';
import { PartnerLogo } from '../components/PartnerStrip';
import { apiErrorMessage } from '../lib/apiError';
import { emptyPartner, partnerPayload, SOCIAL_HOSTS, safeSocialUrl } from '../lib/partners';
import '../partners.css';

export function PartnerEditor({ draft, setDraft, editingId, preview, uploading, saving, onUpload, onSave, onCancel }) {
  const input = (key, label, placeholder, options = {}) => <label className="sp-field" key={key} htmlFor={`sp-${key}`}><span>{label}</span><input id={`sp-${key}`} value={draft[key]} placeholder={placeholder} onChange={e => setDraft(old => ({...old, [key]: e.target.value}))} {...options} /></label>;
  return <form className="sp-editor" onSubmit={onSave}>
    <div className="sp-editor-heading"><h2>{editingId ? 'Ndrysho të dhënat' : 'Shto sponsor ose firmë'}</h2><button className="sp-secondary" type="button" onClick={onCancel} disabled={saving || uploading}>Anulo</button></div>
    <p className="sp-visibility-note">Të dhënat e regjistrimeve aktive janë publike në faqen e hyrjes të DataPOS dhe të firmave. Shtoni vetëm të dhëna që keni leje t’i publikoni.</p>
    <div className="sp-editor-grid">
      {input('name', 'Emri i sponsorit / firmës *', 'P.sh. Market N’Lagje', {required: true, minLength: 2, maxLength: 120})}
      <label className="sp-field" htmlFor="sp-kind"><span>Lloji</span><select id="sp-kind" value={draft.kind} onChange={e => setDraft(old => ({...old, kind: e.target.value}))}><option value="company">Firmë që përdor aplikacionin</option><option value="sponsor">Sponsor</option></select></label>
      {input('address', 'Adresa', 'Rruga, qyteti', {maxLength: 300})}
      {input('phone', 'Telefoni', '+383 …', {type: 'tel', maxLength: 40})}
      {input('facebook', 'Facebook', 'https://www.facebook.com/faqja', {type: 'url', maxLength: 500})}
      {input('instagram', 'Instagram', 'https://www.instagram.com/profili', {type: 'url', maxLength: 500})}
      {input('tiktok', 'TikTok', 'https://www.tiktok.com/@profili', {type: 'url', maxLength: 500})}
      {input('sort_order', 'Renditja (numri më i vogël del më parë)', '0', {type: 'number', min: 0, max: 10000, step: 1})}
    </div>
    <div className="sp-upload-block"><div className="sp-upload-preview">{preview ? <img src={preview} alt="Paraqitja e logos që do të ruhet" /> : <span>Logoja juaj</span>}</div>
      <div><label className="sp-field" htmlFor="sp-logo-file"><span>Ngarko logon nga PC-ja *</span><input type="file" id="sp-logo-file" accept="image/png,image/jpeg,image/webp" disabled={saving || uploading} onChange={onUpload} /></label><p>PNG, JPG ose WebP · deri në 2 MB. Preferohet PNG transparent. Logoja ruhet vetëm pasi klikoni “Ruaj”.</p>{uploading && <p role="status">Duke ngarkuar logon…</p>}</div>
    </div>
    <div className="sp-editor-footer"><label className="sp-checkbox"><input type="checkbox" checked={draft.is_active} onChange={e => setDraft(old => ({...old, is_active: e.target.checked}))} /><span>Shfaq në faqen publike të hyrjes</span></label><button className="sp-primary" type="submit" disabled={saving || uploading}>{saving ? 'Duke ruajtur…' : editingId ? 'Ruaj ndryshimet' : 'Ruaj regjistrimin'}</button></div>
  </form>;
}

export function PartnersView({ rows, loading, error, refresh, draft, setDraft, editingId, editorOpen, preview, uploading, saving, onUpload, onSave, onCancel, onNew, onEdit, onDelete, deleting }) {
  return <div className="sp-admin-page">
    <div className="sp-admin-heading"><div><h1>Sponsorat dhe firmat</h1><p>Menaxhoni logot dhe të dhënat që shfaqen në fund të faqes së hyrjes.</p></div><div className="sp-heading-actions"><button type="button" className="sp-secondary" onClick={refresh} disabled={loading || saving || uploading || !!deleting}>Rifresko</button><button type="button" className="sp-primary" onClick={onNew} disabled={saving || uploading || !!deleting}>+ Shto sponsor / firmë</button></div></div>
    {error && <div role="alert" className="sp-admin-error">{error}</div>}
    {editorOpen && <PartnerEditor {...{draft, setDraft, editingId, preview, uploading, saving, onUpload, onSave, onCancel}} />}
    {loading ? <p role="status" className="sp-empty">Duke ngarkuar regjistrimet…</p> : rows.length ? <div className="sp-admin-grid">{rows.map(row => <article className="sp-admin-card" key={row.id}>
      <div className="sp-card-logo"><PartnerLogo partner={row} /></div><div className="sp-card-title"><h2>{row.name}</h2><span className={row.is_active ? 'sp-visible' : 'sp-hidden'}>{row.is_active ? 'Publik' : 'I fshehur'}</span></div>
      <p>{row.kind === 'sponsor' ? 'Sponsor' : 'Firmë që përdor aplikacionin'}</p><p className="sp-card-address">{row.address || 'Pa adresë'}<br />{row.phone || 'Pa telefon'}</p>
      <div className="sp-card-actions"><button type="button" className="sp-secondary" onClick={() => onEdit(row)} disabled={saving || uploading || !!deleting}>Ndrysho</button><button type="button" className="sp-danger" onClick={() => onDelete(row)} disabled={saving || uploading || !!deleting}>{deleting === row.id ? 'Duke fshirë…' : 'Fshij'}</button></div>
    </article>)}</div> : !error && <div className="sp-empty"><h2>Nuk ka ende sponsorë ose firma</h2><p>Shtoni logon dhe të dhënat e regjistrimit të parë. Regjistrimet aktive shfaqen automatikisht në hyrje.</p></div>}
  </div>;
}

export default function Partners() {
  const {user} = useAuth();
  const [rows, setRows] = useState([]), [loading, setLoading] = useState(true), [error, setError] = useState('');
  const [draft, setDraft] = useState(emptyPartner), [editingId, setEditingId] = useState(null), [editorOpen, setEditorOpen] = useState(false);
  const [preview, setPreview] = useState(''), [uploading, setUploading] = useState(false), [saving, setSaving] = useState(false), [deleting, setDeleting] = useState(null);
  const saveLock = useRef(false), uploadLock = useRef(false), editVersion = useRef(0), deleteLock = useRef(false), live = useRef(true);
  const refresh = useCallback(async () => {
    setLoading(true);setError('');
    try {const {data} = await api.get('/partners');if (live.current) setRows(Array.isArray(data) ? data : []);}
    catch (err) {if (live.current) setError(apiErrorMessage(err, 'Lista nuk u ngarkua'));}
    finally {if (live.current) setLoading(false);}
  }, []);
  useEffect(() => {live.current = true;if (user?.role === 'super_admin') refresh();else setLoading(false);return () => {live.current = false;editVersion.current += 1;};}, [refresh, user?.role]);
  const cancel = () => {editVersion.current += 1;setEditorOpen(false);setEditingId(null);setDraft(emptyPartner());setPreview('');};
  const newEntry = () => {if (uploadLock.current || saveLock.current || deleteLock.current) return;cancel();setEditorOpen(true);};
  const edit = async row => {
    if (uploadLock.current || saveLock.current || deleteLock.current) return;
    const version = ++editVersion.current;setDraft({...emptyPartner(), ...partnerPayload({...row, logo_data: null})});setEditingId(row.id);setEditorOpen(true);setPreview('');setUploading(true);uploadLock.current = true;
    try {const {data} = await api.get(`/partners/${encodeURIComponent(row.id)}/admin-logo`);if (live.current && version === editVersion.current) setPreview(data.logo_data || '');}
    catch (err) {if (live.current && version === editVersion.current) toast.error(apiErrorMessage(err, 'Logoja nuk u ngarkua'));}
    finally {uploadLock.current = false;if (live.current && version === editVersion.current) setUploading(false);}
  };
  const upload = async event => {
    const file = event.target.files?.[0];event.target.value = '';if (!file || uploadLock.current) return;
    if (!['image/png','image/jpeg','image/webp'].includes(file.type) || file.size > 2 * 1024 * 1024) {toast.error('Përdorni PNG, JPG ose WebP deri në 2 MB.');return;}
    uploadLock.current = true;setUploading(true);const version = editVersion.current;
    try {const form = new FormData();form.append('file', file);const {data} = await api.post('/partners/logo-upload', form, {headers:{'Content-Type':'multipart/form-data'}});if (live.current && version === editVersion.current) {setDraft(old => ({...old, logo_data: data.logo_data}));setPreview(data.logo_data);}}
    catch (err) {toast.error(apiErrorMessage(err, 'Ngarkimi dështoi'));}
    finally {uploadLock.current = false;if (live.current) setUploading(false);}
  };
  const save = async event => {
    event.preventDefault();if (saveLock.current || uploadLock.current) return;
    const payload = partnerPayload(draft);
    if (!editingId && !payload.logo_data) {toast.error('Ngarkoni logon para ruajtjes.');return;}
    for (const platform of Object.keys(SOCIAL_HOSTS)) if (payload[platform] && !safeSocialUrl(payload[platform], platform)) {toast.error(`Vendosni një lidhje të vlefshme HTTPS për ${platform}.`);return;}
    saveLock.current = true;setSaving(true);
    try {if (editingId) await api.put(`/partners/${encodeURIComponent(editingId)}`, payload);else await api.post('/partners', payload);toast.success('Regjistrimi u ruajt.');cancel();await refresh();}
    catch (err) {toast.error(apiErrorMessage(err, 'Ruajtja dështoi'));}
    finally {saveLock.current = false;if (live.current) setSaving(false);}
  };
  const remove = async row => {
    if (deleteLock.current || !window.confirm(`Të fshihet “${row.name}”? Logoja dhe të dhënat hiqen nga hyrja publike.`)) return;
    deleteLock.current = true;setDeleting(row.id);
    try {await api.delete(`/partners/${encodeURIComponent(row.id)}`);if (editingId === row.id) cancel();toast.success('Regjistrimi u fshi.');await refresh();}
    catch (err) {toast.error(apiErrorMessage(err, 'Fshirja dështoi'));}
    finally {deleteLock.current = false;if (live.current) setDeleting(null);}
  };
  if (user?.role !== 'super_admin') return <div className="sp-admin-error" role="alert">Kjo faqe lejohet vetëm për superadministratorin.</div>;
  return <PartnersView {...{rows, loading, error, refresh, draft, setDraft, editingId, editorOpen, preview, uploading, saving, deleting}} onUpload={upload} onSave={save} onCancel={cancel} onNew={newEntry} onEdit={edit} onDelete={remove} />;
}
