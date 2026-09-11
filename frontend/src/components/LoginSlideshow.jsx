import React, { useState, useEffect, useCallback } from 'react'

// ---------------------------------------------------------------------------
// Slideshow nen formen e kycjes: shfaq se cfare ben aplikacioni
// ---------------------------------------------------------------------------
const SLIDES = [
  {
    img: '/slides/1-shitja.svg',
    title: 'Shitje e shpejte ne arke',
    text: 'Skano barkodin ose zgjidh artikullin nga katalogu me kategori dhe nenkategori. Shporta, ulja dhe pagesa ne nje ekran.',
  },
  {
    img: '/slides/2-kuponi.svg',
    title: 'Kupon me printim te menjehershem',
    text: 'Kuponi printohet ne printer termik pa dialog, me QR kod dhe me te gjitha te dhenat e shitjes.',
  },
  {
    img: '/slides/3-stoku.svg',
    title: 'Stoku nen kontroll',
    text: 'Gjendja perditesohet me secilen shitje. Sinjalizime per artikujt ne mbarim dhe hyrje te blerjeve.',
  },
  {
    img: '/slides/4-raportet.svg',
    title: 'Raporte per vendime te sakta',
    text: 'Xhiro ditore, artikujt me te shitur, fitimi dhe pasqyra e arkes sipas deges dhe arketarit.',
  },
  {
    img: '/slides/5-offline.svg',
    title: 'Punon edhe pa internet',
    text: 'Shitjet vazhdojne offline dhe sinkronizohen vetvetiu sapo kthehet lidhja. Asnje kupon nuk humbet.',
  },
]

const INTERVAL = 5000

export default function LoginSlideshow() {
  const [index, setIndex] = useState(0)
  const [paused, setPaused] = useState(false)

  const go = useCallback((i) => {
    setIndex(((i % SLIDES.length) + SLIDES.length) % SLIDES.length)
  }, [])

  useEffect(() => {
    if (paused) return undefined
    const t = setTimeout(() => go(index + 1), INTERVAL)
    return () => clearTimeout(t)
  }, [index, paused, go])

  return (
    <div
      className="dps-wrap"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <style>{`
        .dps-wrap {
          width: 100%;
          max-width: 980px;
          margin: 28px auto 0;
          padding: 0 16px 32px;
        }
        .dps-card {
          position: relative;
          display: grid;
          grid-template-columns: 1.15fr 1fr;
          background: #FFFFFF;
          border: 1px solid #DBE4E1;
          border-radius: 18px;
          overflow: hidden;
          box-shadow: 0 12px 34px rgba(10, 54, 52, .09);
        }
        .dps-stage {
          position: relative;
          background: #0A3634;
          min-height: 246px;
        }
        .dps-img {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          object-fit: cover;
          opacity: 0;
          transform: scale(1.04);
          transition: opacity .7s ease, transform 6s ease-out;
        }
        .dps-img.on { opacity: 1; transform: scale(1); }
        .dps-body {
          padding: 30px 30px 26px;
          display: flex;
          flex-direction: column;
        }
        .dps-kicker {
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 1.4px;
          text-transform: uppercase;
          color: #3BB0AA;
          margin-bottom: 12px;
        }
        .dps-slide { display: none; }
        .dps-slide.on { display: block; animation: dpsIn .5s ease both; }
        @keyframes dpsIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .dps-title {
          font-size: 19px;
          font-weight: 700;
          letter-spacing: -.3px;
          color: #13211F;
          margin: 0 0 9px;
        }
        .dps-text {
          font-size: 13.5px;
          line-height: 1.65;
          color: #51615E;
          margin: 0;
        }
        .dps-foot {
          margin-top: auto;
          padding-top: 22px;
          display: flex;
          align-items: center;
          gap: 14px;
        }
        .dps-dots { display: flex; gap: 7px; }
        .dps-dot {
          width: 22px;
          height: 4px;
          border-radius: 3px;
          border: none;
          padding: 0;
          background: #DBE4E1;
          cursor: pointer;
          transition: background .2s, width .2s;
        }
        .dps-dot.on { background: #0E4B49; width: 34px; }
        .dps-nav { margin-left: auto; display: flex; gap: 8px; }
        .dps-btn {
          width: 30px;
          height: 30px;
          border-radius: 8px;
          border: 1px solid #DBE4E1;
          background: #F5F8F6;
          color: #0E4B49;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background .15s, border-color .15s;
        }
        .dps-btn:hover { background: #EAF0EE; border-color: #C6D2CF; }
        @media (max-width: 780px) {
          .dps-card { grid-template-columns: 1fr; }
          .dps-stage { min-height: 180px; }
          .dps-body { padding: 22px; }
        }
      `}</style>

      <div className="dps-card">
        <div className="dps-stage">
          {SLIDES.map((s, i) => (
            <img
              key={s.img}
              src={s.img}
              alt={s.title}
              className={'dps-img' + (i === index ? ' on' : '')}
            />
          ))}
        </div>

        <div className="dps-body">
          <div className="dps-kicker">Me DataPOS</div>

          {SLIDES.map((s, i) => (
            <div
              key={s.title}
              className={'dps-slide' + (i === index ? ' on' : '')}
            >
              <h3 className="dps-title">{s.title}</h3>
              <p className="dps-text">{s.text}</p>
            </div>
          ))}

          <div className="dps-foot">
            <div className="dps-dots">
              {SLIDES.map((s, i) => (
                <button
                  key={'d' + s.img}
                  type="button"
                  aria-label={s.title}
                  className={'dps-dot' + (i === index ? ' on' : '')}
                  onClick={() => go(i)}
                />
              ))}
            </div>

            <div className="dps-nav">
              <button
                type="button"
                className="dps-btn"
                aria-label="Para"
                onClick={() => go(index - 1)}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                     stroke="currentColor" strokeWidth="2.2"
                     strokeLinecap="round" strokeLinejoin="round">
                  <path d="M15 18l-6-6 6-6" />
                </svg>
              </button>
              <button
                type="button"
                className="dps-btn"
                aria-label="Pas"
                onClick={() => go(index + 1)}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                     stroke="currentColor" strokeWidth="2.2"
                     strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 6l6 6-6 6" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
