import React, { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../App';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { partnerLogoUrl, phoneHref, safeSocialUrl } from '../lib/partners';
import '../partners.css';

export function PartnerLogo({ partner, preview = '' }) {
  const url = preview || partnerLogoUrl(partner);
  const [failed, setFailed] = useState(false);
  useEffect(() => { setFailed(false); }, [url]);
  return url && !failed ? <img src={url} alt={`Logo e ${partner.name}`} loading="lazy" onError={() => setFailed(true)} /> : <span className="sp-logo-fallback">{partner.name}</span>;
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

export function PartnerStripView({ partners, paused, setPaused, selected, setSelected }) {
  if (!partners.length) return null;
  return <section className={`sp-strip ${paused ? 'sp-strip-static' : ''}`} aria-label="Sponsorat dhe firmat">
    <div className="sp-strip-heading"><div><h2>Sponsorat dhe firmat</h2><p>Klikoni një logo për të parë të dhënat e firmës.</p></div>
      <button type="button" className="sp-secondary" onClick={() => setPaused(!paused)} aria-pressed={paused}>{paused ? 'Vazhdo lëvizjen' : 'Ndalo lëvizjen'}</button>
    </div>
    <div className="sp-marquee-window">
      <div className="sp-marquee-track" style={{'--sp-duration': `${Math.max(28, partners.length * 5)}s`}}>
        {[0, 1].map(copy => <div className="sp-marquee-group" key={copy} aria-hidden={copy === 1 ? 'true' : undefined}>
          {partners.map(partner => <button type="button" key={partner.id} className="sp-logo-button" tabIndex={copy === 1 ? -1 : 0}
            aria-label={`Shfaq të dhënat e ${partner.name}`} onFocus={event => { if (!copy && event.currentTarget.matches(':focus-visible')) setPaused(true); }} onClick={() => { setSelected(partner); setPaused(true); }}>
            <PartnerLogo partner={partner} /><span>{partner.name}</span>
          </button>)}
        </div>)}
      </div>
    </div>
    <PartnerDetails partner={selected} onClose={() => setSelected(null)} />
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
