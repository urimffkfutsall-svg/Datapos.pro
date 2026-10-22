import React, { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../App';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { partnerLogoUrl, phoneHref, safeSocialUrl } from '../lib/partners';
import '../partners.css';

export function PartnerLogo({ partner, preview = '', compact = false }) {
  const url = preview || partnerLogoUrl(partner);
  const [failed, setFailed] = useState(false);
  useEffect(() => { setFailed(false); }, [url]);
  return url && !failed ? <img src={url} alt={`Logo e ${partner.name}`} loading="lazy" onError={() => setFailed(true)} /> : <span className="sp-logo-fallback">{compact ? (partner.name || '?').split(/\s+/).filter(Boolean).slice(0, 2).map(w => w[0]).join('').toUpperCase() : partner.name}</span>;
}

export function PartnerDetails({ partner, onClose }) {
  return <Dialog open={!!partner} onOpenChange={open => { if (!open) onClose(); }}>
    <DialogContent className="sp-details-dialog">
      {partner && <>
        <DialogHeader><DialogTitle>{partner.name}</DialogTitle><DialogDescription>{partner.kind === 'sponsor' ? 'Sponsor i DataPOS' : 'Firmë që përdor DataPOS'}</DialogDescription></DialogHeader>
        <div className="sp-details-logo"><PartnerLogo partner={partner} /></div>
        <dl className="sp-contact-list">
          <div><dt>Adresa</dt><dd>{partner.address || 'Nuk është vendosur'}</dd></div>
          <div><dt>Telefoni</dt><dd>{partner.phone ? <a href={phoneHref(partner.phone)}>{partner.phone}</a> : 'Nuk është vendosur'}</dd></div>
        </dl>
        <div className="sp-social-links">
          {['facebook', 'instagram', 'tiktok'].map(platform => {
            const url = safeSocialUrl(partner[platform], platform);
            return url ? <a key={platform} href={url} target="_blank" rel="noopener noreferrer">{({facebook:'Facebook',instagram:'Instagram',tiktok:'TikTok'})[platform]} ↗</a> : null;
          })}
        </div>
        <button className="sp-secondary" type="button" onClick={onClose}>Mbyll</button>
      </>}
    </DialogContent>
  </Dialog>;
}

const KIND_LABEL = { sponsor: 'Sponsor', company: 'Firmë' };
const ACCENTS = ['#1f9d93', '#ef6a4c', '#3b6fe0', '#e8a13a', '#0f766e', '#7a5af5'];

export function PartnerStripView({ partners, paused, setPaused, selected, setSelected }) {
  if (!partners.length) return null;
  const duration = `${Math.max(28, partners.length * 6)}s`;
  const count = String(partners.length).padStart(2, '0');
  return <section className={`sp-strip sp-strip-v2 ${paused ? 'sp-strip-static' : ''}`} aria-label="Sponsorat dhe firmat"
    onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget) && !selected) setPaused(false); }}>
    <div className="sp-band">
      <div className="sp-band-intro">
        <span className="sp-band-kicker">DataPOS</span>
        <strong className="sp-band-count" data-ghost={count}>{count}</strong>
        <span className="sp-band-caption">firma &amp; sponsorë<br />punojnë me DataPOS</span>
      </div>
      <div className="sp-band-stage">
        <button type="button" className="sp-pause" onClick={() => setPaused(!paused)} aria-pressed={paused}>
          {paused ? 'Vazhdo lëvizjen' : 'Ndalo lëvizjen'}
        </button>
        <div className="sp-marquee-window">
          <div className="sp-marquee-track" style={{'--sp-duration': duration}}>
            {[0, 1].map(copy => <div className="sp-marquee-group" key={copy} aria-hidden={copy === 1 ? 'true' : undefined}>
              {partners.map((partner, index) => <button type="button" key={partner.id} className="sp-logo-button" tabIndex={copy === 1 ? -1 : 0}
                style={{'--sp-accent': ACCENTS[index % ACCENTS.length]}}
                aria-label={`Shfaq të dhënat e ${partner.name}`} onFocus={event => { if (!copy && event.currentTarget.matches(':focus-visible')) setPaused(true); }} onClick={() => { setSelected(partner); setPaused(true); }}>
                <span className="sp-logo-mark"><PartnerLogo partner={partner} compact /></span>
                <span className="sp-logo-text">
                  <small>{String(index + 1).padStart(2, '0')} / {KIND_LABEL[partner.kind] || 'Firmë'}</small>
                  <strong>{partner.name}</strong>
                </span>
                <span className="sp-logo-arrow" aria-hidden="true">↗</span>
              </button>)}
            </div>)}
          </div>
        </div>
      </div>
    </div>
    <div className="sp-ticker" aria-hidden="true">
      <div className="sp-ticker-track" style={{'--sp-duration': duration}}>
        {[0, 1].map(copy => <div className="sp-ticker-group" key={copy}>
          {partners.map((partner, index) => <span className="sp-ticker-item" key={partner.id}>
            <b style={{color: ACCENTS[index % ACCENTS.length]}}>{partner.name}</b>
            <i />
            {partner.address || (partner.kind === 'sponsor' ? 'Sponsor i DataPOS' : 'Punon me DataPOS')}
          </span>)}
        </div>)}
      </div>
    </div>
    <PartnerDetails partner={selected} onClose={() => { setSelected(null); setPaused(false); }} />
  </section>;
}

export default function PartnerStrip() {
  const [partners, setPartners] = useState([]), [paused, setPaused] = useState(false), [selected, setSelected] = useState(null), [failed, setFailed] = useState(false);
  const mounted = useRef(true), busy = useRef(false);
  const load = useCallback(async () => {
    if (busy.current) return;
    busy.current = true;
    try { const {data} = await api.get('/partners/public'); if (mounted.current) {setPartners(Array.isArray(data) ? data : []);setFailed(false);} }
    catch { if (mounted.current) setFailed(true); }
    finally { busy.current = false; }
  }, []);
  useEffect(() => {mounted.current = true;load();return () => {mounted.current = false;};}, [load]);
  if (failed && !partners.length) return <div className="sp-public-error" role="status">Lista e sponsorëve nuk u ngarkua. <button type="button" onClick={load}>Provo përsëri</button></div>;
  return <PartnerStripView partners={partners} paused={paused} setPaused={setPaused} selected={selected} setSelected={setSelected} />;
}
