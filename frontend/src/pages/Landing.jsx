import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * LANDING PAGE - DataPOS
 * Struktura e frymezuar nga data-view.app, me paletën e gjelbër.
 * Shenim: asnje referenca ndaj ATK-se nuk shfaqet ne kete faqe.
 */

const T = {
  sq: {
    nav: {
      modules: 'Modulet',
      who: 'Për kë',
      erp: 'Integrimi me ERP',
      security: 'Siguria',
      setup: 'Instalimi',
      faq: 'Pyetje',
      contact: 'Kontakti',
      demo: 'Kërko një demonstrim',
      login: 'Kyçu',
    },
    hero: {
      eyebrow: 'Arkë digjitale për pikën e shitjes',
      title1: 'Arka digjitale, e ndërtuar për',
      title2: 'punën e përditshme',
      sub: 'E shpejtë në pikën e shitjes — e pavarur ose e integruar me sistemet tuaja ekzistuese.',
      cta: 'Kërko një demonstrim',
      cta2: 'Hyr në aplikacion',
      shot: 'Pamje reale: ekrani i shitjes',
      s1: 'Gjuhë · Shqip, Serbisht, Anglisht',
      s2: 'Raporte për çdo periudhë',
      s3v: 'Offline',
      s3: 'Punon edhe pa internet',
    },
    pills: [
      ['E shpejtë', 'Skanoje ose prek një artikull — shitja mbyllet me një shtypje.'],
      ['E thjeshtë për stafin', 'Ekran me prekje dhe butona të mëdhenj — mësohet brenda një dite.'],
      ['Punon edhe pa internet', 'Shitja vazhdon, dhe të dhënat sinkronizohen vetë kur kthehet interneti.'],
    ],
    stepsTitle: 'Në pikën e shitjes',
    stepsHead: 'Katër hapa, çdo herë',
    steps: ['Skano', 'Paguaj', 'Regjistrohet', 'Printohet me QR'],
    modTitle: 'Modulet',
    modHead: 'Gjithçka në një arkë',
    modules: [
      ['Shitja', 'Mur artikujsh me foto, kërkim me kod ose barkod, një shtypje deri te shitja.'],
      ['Kuponi', 'Kupon me QR, i nënshkruar dhe i regjistruar në çast — shitje, kthim, anulim.'],
      ['Restoranti dhe kafiteria', 'Tavolina, porosi të hapura, printim në kuzhinë e banak, ndarje e faturës.'],
      ['Stoku', 'Gjendja shihet në pikën e shitjes, me shenja për stok të ulët.'],
      ['Fatura për kompani', 'Faturë A4 për biznese, e numëruar, me kontratë opsionale.'],
      ['Raportet', 'Shtatë raporte për çdo periudhë — në ekran, të printueshme dhe PDF.'],
    ],
    whoTitle: 'Për kë',
    whoHead: 'E bërë për punën tuaj',
    who: [
      ['Dyqan me pakicë', 'Skano, mbyll shitjen, printo kuponin.'],
      ['Farmaci', 'Kërkim i shpejtë dhe raporte të sakta.'],
      ['Mishtore me peshore', 'Peshon, printon etiketën, arka lexon peshën.'],
      ['Kafiteri / Restorant', 'Tavolina, porosi të hapura, ndarje e faturës.'],
      ['Shërbime dhe riparime', 'Faturë B2B me të dhënat e klientit dhe garancion.'],
      ['Shumicë', 'Fatura për kompani, të kërkueshme e të riprintueshme.'],
    ],
    erpTitle: 'Integrimi me ERP',
    erpHead: 'E pavarur, ose e lidhur me ERP-në tuaj',
    erpBody:
      'Punon edhe krejt i pavarur, pa ERP. E kur ju duhet, lidhet me sistemet të cilat i përdorni: artikujt e çmimet vijnë nga ERP-ja dhe çdo shitje kthehet si dokument.',
    erpPoints: [
      'Artikujt dhe çmimet nga ERP-ja',
      'Çdo shitje e blerje si dokument',
      'Disa arka dhe degë nën një biznes',
    ],
    noErp: ['Pa ERP', 'Nuk keni ERP? Nuk ka problem — DataPOS punon më vete, me bazën e vet.'],
    secTitle: 'Siguria',
    secHead: 'Të dhënat tuaja, të qeta',
    secSub: 'Gjithçka ruhet me kujdes dhe komunikohet në mënyrë të sigurt — pa asgjë për t’u shqetësuar.',
    sec: [
      ['Të dhëna të mbrojtura', 'Baza ruhet e enkriptuar në arkë, e mbrojtur nga Windows.'],
      ['Çdo kupon i regjistruar me kujdes', 'Kuponët ruhen të nënshkruar dhe të lidhur me radhë, në rregull.'],
      ['Lidhje e sigurt', 'Komunikimi bëhet vetëm përmes HTTPS, me certifikatë të vlefshme.'],
      ['Asgjë nuk humbet', 'Pa internet shitja vazhdon, dhe përditësimet nuk i prekin kurrë të dhënat tuaja.'],
    ],
    setupTitle: 'Instalimi',
    setupHead: 'Nga kutia te pika e shitjes',
    setup: [
      ['Përgatitja', 'Përgatiten njësitë, klasifikimet dhe mënyrat e pagesës — gati për arkën.'],
      ['Një instalues', 'Një setup.exe i vetëm: instalon aplikacionin dhe konfiguron arkën.'],
      ['Gati për shitje', 'Stafi mund të praktikojë më parë; kalimi në punë të vërtetë bëhet me një veprim.'],
    ],
    faqTitle: 'Pyetje të shpeshta',
    faqHead: 'Pyetjet që bëhen më shpesh',
    faq: [
      ['A punon pa internet?', 'Po. Shitja vazhdon normalisht dhe të dhënat sinkronizohen vetë kur kthehet lidhja.'],
      ['A më duhet një ERP?', 'Jo — DataPOS punon edhe krejt i pavarur, me bazën e vet. E kur ju duhet, integrohet me sistemin tuaj.'],
      ['A mund të praktikojë stafi më parë?', 'Po, me modalitetin e praktikës — asnjë dokument zyrtar nuk lëshohet.'],
      ['Çfarë pajisjesh?', 'Një PC ose tablet me Windows dhe një printer termik (80 ose 58 mm). Opsionale: skaner barkodi, sirtar parash, ekran me prekje dhe peshore.'],
      ['Cilat gjuhë?', 'Shqip, Serbisht dhe Anglisht — sipas kasierit, në ekran dhe në kupon.'],
      ['A instalohet në disa kompjuterë?', 'Po. Setup.exe instalohet në çdo PC; çdo arkë lidhet me degën dhe firmën tuaj.'],
    ],
    contactTitle: 'Kontakti',
    contactHead: 'Kërkoni një demonstrim',
    contactSub: 'Tregoni pak për biznesin tuaj dhe ju kontaktojmë për një demonstrim në pikën e shitjes.',
    contactNote: 'Staf me përvojë mbi 10 vjeçare në implementime të sistemeve të shitjes dhe ERP-ve.',
    form: {
      name: 'Emri',
      business: 'Biznesi',
      city: 'Qyteti',
      contact: 'Telefon ose e-mail',
      message: 'Mesazhi',
      send: 'Dërgo kërkesën',
      ok: '✓ Faleminderit! Kërkesa u dërgua — ju kontaktojmë së shpejti.',
    },
    footerTag: 'Pikë shitëse digjitale — e pavarur ose e integruar me sistemin tuaj.',
  },
  en: {
    nav: {
      modules: 'Modules',
      who: "Who it's for",
      erp: 'ERP integration',
      security: 'Security',
      setup: 'Setup',
      faq: 'FAQ',
      contact: 'Contact',
      demo: 'Book a demo',
      login: 'Sign in',
    },
    hero: {
      eyebrow: 'A digital till for the point of sale',
      title1: 'A digital till, built for',
      title2: 'everyday work',
      sub: 'Fast at the point of sale — standalone or integrated with your existing systems.',
      cta: 'Book a demo',
      cta2: 'Open the app',
      shot: 'Real screenshot: the sale screen',
      s1: 'Languages · Albanian, Serbian, English',
      s2: 'Reports for any period',
      s3v: 'Offline',
      s3: 'Works without internet',
    },
    pills: [
      ['Fast', 'Scan or tap an article — the sale closes with one press.'],
      ['Simple for staff', 'A touch screen with big buttons — learned in a day.'],
      ['Works without internet', 'The sale continues, and data syncs by itself when the internet is back.'],
    ],
    stepsTitle: 'At the point of sale',
    stepsHead: 'Four steps, every time',
    steps: ['Scan', 'Pay', 'Recorded', 'Printed with QR'],
    modTitle: 'Modules',
    modHead: 'Everything in one till',
    modules: [
      ['Selling', 'An article wall with photos, search by code or barcode, one press to the sale.'],
      ['Receipt', 'A QR receipt, signed and recorded instantly — sale, return, annulment.'],
      ['Restaurant & café', 'Tables, open orders, kitchen and bar printing, split bills.'],
      ['Stock', 'Stock is visible at the point of sale, with low-stock marks.'],
      ['Invoices to companies', 'An A4 invoice for businesses, numbered, with an optional contract.'],
      ['Reports', 'Seven reports for any period — on screen, printable and as PDF.'],
    ],
    whoTitle: "Who it's for",
    whoHead: 'Made for your work',
    who: [
      ['Retail shop', 'Scan, close the sale, print the receipt.'],
      ['Pharmacy', 'Fast search and precise reports.'],
      ['Butcher with scale', 'Weigh, print the label, the till reads the weight.'],
      ['Café / Restaurant', 'Tables, open orders, split bills.'],
      ['Services & repairs', 'A B2B invoice with customer data and warranty.'],
      ['Wholesaler', 'Company invoices, searchable and reprintable.'],
    ],
    erpTitle: 'ERP integration',
    erpHead: 'Standalone, or plugged into your ERP',
    erpBody:
      'It runs fully standalone, without an ERP. And when you need it, it connects to the systems you already use: articles and prices come from the ERP and every sale goes back as a document.',
    erpPoints: [
      'Articles and prices from the ERP',
      'Every sale and purchase booked as a document',
      'Several tills and branches under one business',
    ],
    noErp: ['No ERP', 'No ERP? No problem — DataPOS runs on its own, with its own database.'],
    secTitle: 'Security',
    secHead: 'Your data, at ease',
    secSub: 'Everything is kept with care and communicated securely — nothing to worry about.',
    sec: [
      ['Protected data', 'The database is stored encrypted on the till, protected by Windows.'],
      ['Every receipt safely recorded', 'Receipts are stored signed and neatly linked in order.'],
      ['Secure connection', 'Communication happens over HTTPS only, with a valid certificate.'],
      ['Nothing is lost', 'Offline the sale continues, and updates never touch your records.'],
    ],
    setupTitle: 'How it starts',
    setupHead: 'From the box to the point of sale',
    setup: [
      ['Preparation', 'Units, classifications and payment methods are prepared — ready for the till.'],
      ['One installer', 'A single setup.exe: it installs the application and configures the till.'],
      ['Ready to sell', 'Staff can practise first; going live takes a single action.'],
    ],
    faqTitle: 'FAQ',
    faqHead: 'The questions asked most',
    faq: [
      ['Does it work without internet?', 'Yes. The sale continues normally and data syncs by itself when the connection is back.'],
      ['Do I need an ERP?', 'No — DataPOS also runs fully standalone, on its own database. And when you need it, it integrates with your system.'],
      ['Can staff practise first?', 'Yes, with practice mode — no official document is issued.'],
      ['What hardware?', 'A Windows PC or tablet and a thermal printer (80 or 58 mm). Optional: a barcode scanner, cash drawer, touch screen and shop scale.'],
      ['Which languages?', 'Albanian, Serbian and English — per cashier, on the screen and on the receipt.'],
      ['Can it be installed on several PCs?', 'Yes. The setup.exe installs on any PC; each till is linked to your branch and company.'],
    ],
    contactTitle: 'Contact',
    contactHead: 'Book a demonstration',
    contactSub: "Tell us a little about your business and we'll arrange a demo at the point of sale.",
    contactNote: 'A team with over 10 years of experience implementing POS and ERP systems.',
    form: {
      name: 'Name',
      business: 'Business',
      city: 'City',
      contact: 'Phone or e-mail',
      message: 'Message',
      send: 'Send request',
      ok: "✓ Thank you! Your request was sent — we'll be in touch shortly.",
    },
    footerTag: 'A digital point of sale — standalone or integrated with your system.',
  },
};

const Logo = ({ light }) => (
  <div className="flex items-center gap-2 select-none">
    <div
      className="h-8 w-8 rounded-lg grid place-items-center font-black text-[13px]"
      style={{ background: light ? '#EAF3F1' : '#0E4B49', color: light ? '#0E4B49' : '#EAF3F1' }}
    >
      DP
    </div>
    <div className="leading-none" style={{ fontFamily: "'Archivo', system-ui, sans-serif" }}>
      <span className="font-extrabold tracking-tight" style={{ color: light ? '#EAF3F1' : '#13211F' }}>
        DataPOS
      </span>
      <span className="font-semibold" style={{ color: light ? '#9CC4BF' : '#7C8A87' }}>
        .pro
      </span>
    </div>
  </div>
);

const Landing = () => {
  const navigate = useNavigate();
  const [lang, setLang] = useState(() => localStorage.getItem('datapos_lang') || 'sq');
  const [openFaq, setOpenFaq] = useState(0);
  const [sent, setSent] = useState(false);
  const [menu, setMenu] = useState(false);
  const t = T[lang];

  useEffect(() => {
    localStorage.setItem('datapos_lang', lang);
  }, [lang]);

  useEffect(() => {
    document.title = 'DataPOS — ' + t.hero.eyebrow;
  }, [t]);

  const go = (id) => (e) => {
    e.preventDefault();
    setMenu(false);
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const submit = (e) => {
    e.preventDefault();
    setSent(true);
  };

  const nav = [
    ['modules', t.nav.modules],
    ['who', t.nav.who],
    ['erp', t.nav.erp],
    ['security', t.nav.security],
    ['setup', t.nav.setup],
    ['faq', t.nav.faq],
  ];

  return (
    <div
      className="min-h-screen"
      style={{
        background: '#F5F8F6',
        color: '#13211F',
        fontFamily: "'IBM Plex Sans', system-ui, sans-serif",
      }}
    >
      {/* ================= HEADER ================= */}
      <header
        className="sticky top-0 z-50 border-b backdrop-blur"
        style={{ background: 'rgba(255,255,255,.85)', borderColor: '#DBE4E1' }}
      >
        <div className="mx-auto flex h-16 items-center justify-between px-5" style={{ maxWidth: 1120 }}>
          <Logo />
          <nav className="hidden lg:flex items-center gap-6 text-[13.5px] font-medium">
            {nav.map(([id, label]) => (
              <a
                key={id}
                href={`#${id}`}
                onClick={go(id)}
                className="transition-colors hover:text-[#0E4B49]"
                style={{ color: '#51615E' }}
              >
                {label}
              </a>
            ))}
          </nav>
          <div className="flex items-center gap-2">
            <div className="hidden sm:flex rounded-lg overflow-hidden border text-[12px] font-bold" style={{ borderColor: '#DBE4E1' }}>
              {['sq', 'en'].map((l) => (
                <button
                  key={l}
                  onClick={() => setLang(l)}
                  className="px-2.5 py-1.5 transition-colors"
                  style={{
                    background: lang === l ? '#0E4B49' : 'transparent',
                    color: lang === l ? '#EAF3F1' : '#51615E',
                  }}
                >
                  {l.toUpperCase()}
                </button>
              ))}
            </div>
            <button
              onClick={() => navigate('/login')}
              className="hidden sm:inline-flex px-3.5 py-2 rounded-lg text-[13px] font-semibold border transition-colors hover:bg-[#EAF0EE]"
              style={{ borderColor: '#C6D2CF', color: '#0E4B49' }}
            >
              {t.nav.login}
            </button>
            <a
              href="#contact"
              onClick={go('contact')}
              className="inline-flex px-4 py-2 rounded-lg text-[13px] font-bold text-white transition-transform hover:-translate-y-px"
              style={{ background: '#0E4B49' }}
            >
              {t.nav.demo}
            </a>
            <button className="lg:hidden p-2" onClick={() => setMenu(!menu)} aria-label="Menu">
              <div className="space-y-1">
                <span className="block h-0.5 w-5" style={{ background: '#13211F' }} />
                <span className="block h-0.5 w-5" style={{ background: '#13211F' }} />
                <span className="block h-0.5 w-5" style={{ background: '#13211F' }} />
              </div>
            </button>
          </div>
        </div>
        {menu && (
          <div className="lg:hidden border-t px-5 py-3 grid gap-1" style={{ borderColor: '#DBE4E1', background: '#fff' }}>
            {nav.concat([['contact', t.nav.contact]]).map(([id, label]) => (
              <a key={id} href={`#${id}`} onClick={go(id)} className="py-2 text-sm font-medium" style={{ color: '#51615E' }}>
                {label}
              </a>
            ))}
          </div>
        )}
      </header>

      {/* ================= HERO ================= */}
      <section className="px-5 pt-14 pb-16">
        <div className="mx-auto grid lg:grid-cols-2 gap-12 items-center" style={{ maxWidth: 1120 }}>
          <div>
            <div
              className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-[12px] font-semibold mb-5"
              style={{ background: '#EAF0EE', color: '#0E4B49' }}
            >
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: '#1E9E5A' }} />
              {t.hero.eyebrow}
            </div>
            <h1
              className="text-[clamp(2rem,5vw,3.4rem)] font-extrabold leading-[1.06] tracking-[-0.02em]"
              style={{ fontFamily: "'Archivo', system-ui, sans-serif" }}
            >
              {t.hero.title1}
              <br />
              <span style={{ color: '#0E4B49' }}>{t.hero.title2}</span>
            </h1>
            <p className="mt-5 text-[17px] leading-relaxed" style={{ color: '#51615E', maxWidth: 520 }}>
              {t.hero.sub}
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <a
                href="#contact"
                onClick={go('contact')}
                className="px-5 py-3 rounded-xl font-bold text-white text-sm transition-transform hover:-translate-y-0.5"
                style={{ background: '#0E4B49', boxShadow: '0 8px 24px -12px rgba(16,45,43,.5)' }}
              >
                {t.hero.cta}
              </a>
              <button
                onClick={() => navigate('/login')}
                className="px-5 py-3 rounded-xl font-bold text-sm border transition-colors hover:bg-[#EAF0EE]"
                style={{ borderColor: '#C6D2CF', color: '#0E4B49' }}
              >
                {t.hero.cta2}
              </button>
            </div>
            <div className="mt-9 grid grid-cols-3 gap-4">
              {[
                ['3', t.hero.s1],
                ['7', t.hero.s2],
                [t.hero.s3v, t.hero.s3],
              ].map(([n, label], i) => (
                <div key={i}>
                  <div
                    className="text-[22px] font-extrabold"
                    style={{ color: '#0E4B49', fontFamily: "'Archivo', system-ui, sans-serif" }}
                  >
                    {n}
                  </div>
                  <div className="text-[12px] leading-snug mt-0.5" style={{ color: '#7C8A87' }}>
                    {label}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Receipt mock */}
          <div className="relative">
            <div
              className="rounded-2xl p-6"
              style={{ background: '#0E4B49', boxShadow: '0 26px 52px -20px rgba(16,45,43,.55)' }}
            >
              <div className="rounded-xl bg-white p-5" style={{ fontFamily: "'IBM Plex Mono', ui-monospace, monospace" }}>
                <div className="text-center border-b pb-3 mb-3" style={{ borderColor: '#DBE4E1' }}>
                  <div className="font-extrabold text-[15px]" style={{ fontFamily: "'Archivo', sans-serif" }}>
                    DataPOS<span style={{ color: '#7C8A87' }}>.pro</span>
                  </div>
                  <div className="text-[10px] tracking-wider mt-1" style={{ color: '#7C8A87' }}>
                    {lang === 'sq' ? 'ARKË DIGJITALE' : 'DIGITAL TILL'}
                  </div>
                </div>
                {[
                  ['Espresso ×2', '1.00'],
                  ['Makiato', '0.80'],
                  ['Bukë ×3', '1.20'],
                ].map(([n, p]) => (
                  <div key={n} className="flex justify-between text-[13px] py-1">
                    <span>{n}</span>
                    <span>{p}</span>
                  </div>
                ))}
                <div
                  className="flex justify-between font-bold text-[15px] border-t mt-3 pt-3"
                  style={{ borderColor: '#DBE4E1' }}
                >
                  <span>TOTAL</span>
                  <span style={{ color: '#0E4B49' }}>3.00 €</span>
                </div>
                <div className="mt-4 flex items-center justify-center gap-3">
                  <div
                    className="h-14 w-14 rounded grid place-items-center text-[8px] font-bold"
                    style={{ background: '#13211F', color: '#fff' }}
                  >
                    QR
                  </div>
                  <div className="text-[10px] leading-tight" style={{ color: '#7C8A87' }}>
                    <div>NR. 368636262195</div>
                    <div>a1b2-c3d4-e5f6</div>
                  </div>
                </div>
                <div
                  className="mt-4 rounded-lg py-2 text-center text-[11px] font-bold"
                  style={{ background: '#EAF0EE', color: '#1E9E5A' }}
                >
                  ✓ {lang === 'sq' ? 'I regjistruar · I sinkronizuar' : 'Recorded · Synced'}
                </div>
              </div>
              <div className="text-center text-[11px] mt-4" style={{ color: '#A9C6C2' }}>
                [ {t.hero.shot} ]
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ================= PILLS ================= */}
      <section className="px-5 pb-16">
        <div className="mx-auto grid md:grid-cols-3 gap-4" style={{ maxWidth: 1120 }}>
          {t.pills.map(([title, body]) => (
            <div
              key={title}
              className="rounded-2xl border p-6"
              style={{ background: '#fff', borderColor: '#DBE4E1' }}
            >
              <div className="font-bold text-[15px] mb-1.5" style={{ fontFamily: "'Archivo', sans-serif" }}>
                {title}
              </div>
              <p className="text-[13.5px] leading-relaxed" style={{ color: '#51615E' }}>
                {body}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ================= STEPS ================= */}
      <section className="px-5 py-16" style={{ background: '#EAF0EE' }}>
        <div className="mx-auto" style={{ maxWidth: 1120 }}>
          <SectionHead kicker={t.stepsTitle} title={t.stepsHead} />
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-9">
            {t.steps.map((s, i) => (
              <div key={s} className="rounded-2xl p-6 bg-white border" style={{ borderColor: '#DBE4E1' }}>
                <div
                  className="h-9 w-9 rounded-lg grid place-items-center font-extrabold text-sm mb-3"
                  style={{ background: '#0E4B49', color: '#EAF3F1' }}
                >
                  {i + 1}
                </div>
                <div className="font-bold" style={{ fontFamily: "'Archivo', sans-serif" }}>
                  {s}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================= MODULES ================= */}
      <Section id="modules" kicker={t.modTitle} title={t.modHead}>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {t.modules.map(([title, body]) => (
            <Card key={title} title={title} body={body} />
          ))}
        </div>
      </Section>

      {/* ================= WHO ================= */}
      <div style={{ background: '#EAF0EE' }}>
        <Section id="who" kicker={t.whoTitle} title={t.whoHead}>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {t.who.map(([title, body]) => (
              <Card key={title} title={title} body={body} />
            ))}
          </div>
        </Section>
      </div>

      {/* ================= ERP ================= */}
      <Section id="erp" kicker={t.erpTitle} title={t.erpHead}>
        <div className="grid lg:grid-cols-2 gap-10 items-start">
          <div>
            <p className="text-[15px] leading-relaxed" style={{ color: '#51615E' }}>
              {t.erpBody}
            </p>
            <ul className="mt-6 space-y-3">
              {t.erpPoints.map((p) => (
                <li key={p} className="flex items-start gap-3 text-[14px]">
                  <span
                    className="mt-1 h-4 w-4 shrink-0 rounded-full grid place-items-center text-[10px] font-bold text-white"
                    style={{ background: '#1E9E5A' }}
                  >
                    ✓
                  </span>
                  <span>{p}</span>
                </li>
              ))}
            </ul>
            <div
              className="mt-7 rounded-xl border p-5"
              style={{ background: '#EAF0EE', borderColor: '#C6D2CF' }}
            >
              <div className="font-bold text-sm mb-1" style={{ color: '#0E4B49' }}>
                {t.noErp[0]}
              </div>
              <p className="text-[13.5px]" style={{ color: '#51615E' }}>
                {t.noErp[1]}
              </p>
            </div>
          </div>
          <div className="rounded-2xl border p-7" style={{ background: '#fff', borderColor: '#DBE4E1' }}>
            <div
              className="rounded-xl py-4 text-center font-extrabold text-white"
              style={{ background: '#0E4B49', fontFamily: "'Archivo', sans-serif" }}
            >
              DataPOS.pro
              <div className="text-[11px] font-medium mt-0.5" style={{ color: '#A9C6C2' }}>
                {lang === 'sq' ? 'Pika e shitjes' : 'The point of sale'}
              </div>
            </div>
            <div className="flex justify-between text-[11px] font-mono my-4" style={{ color: '#7C8A87' }}>
              <span>{lang === 'sq' ? 'shitjet →' : 'sales →'}</span>
              <span>{lang === 'sq' ? '← artikujt' : '← articles'}</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[['Datalab', 'Pantheon'], ['MS Dynamics', 'NAV / Navision']].map(([a, b]) => (
                <div
                  key={a}
                  className="rounded-xl border p-4 text-center"
                  style={{ borderColor: '#DBE4E1', background: '#F5F8F6' }}
                >
                  <div className="text-[11px]" style={{ color: '#7C8A87' }}>
                    {a}
                  </div>
                  <div className="font-bold text-[14px]" style={{ color: '#0E4B49' }}>
                    {b}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Section>

      {/* ================= SECURITY ================= */}
      <div style={{ background: '#0E4B49' }}>
        <div className="mx-auto px-5 py-16" style={{ maxWidth: 1120 }}>
          <div
            className="text-[12px] font-bold tracking-[0.14em] uppercase mb-2"
            style={{ color: '#A9C6C2' }}
            id="security"
          >
            {t.secTitle}
          </div>
          <h2
            className="text-[clamp(1.6rem,3.4vw,2.4rem)] font-extrabold tracking-tight text-white"
            style={{ fontFamily: "'Archivo', sans-serif" }}
          >
            {t.secHead}
          </h2>
          <p className="mt-3 text-[15px]" style={{ color: '#A9C6C2', maxWidth: 620 }}>
            {t.secSub}
          </p>
          <div className="grid md:grid-cols-2 gap-4 mt-9">
            {t.sec.map(([title, body]) => (
              <div
                key={title}
                className="rounded-2xl p-6 border"
                style={{ background: 'rgba(255,255,255,.06)', borderColor: 'rgba(169,198,194,.25)' }}
              >
                <div className="font-bold text-white mb-1.5" style={{ fontFamily: "'Archivo', sans-serif" }}>
                  {title}
                </div>
                <p className="text-[13.5px] leading-relaxed" style={{ color: '#A9C6C2' }}>
                  {body}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ================= SETUP ================= */}
      <Section id="setup" kicker={t.setupTitle} title={t.setupHead}>
        <div className="grid md:grid-cols-3 gap-4">
          {t.setup.map(([title, body], i) => (
            <div key={title} className="rounded-2xl border p-6" style={{ background: '#fff', borderColor: '#DBE4E1' }}>
              <div
                className="h-9 w-9 rounded-lg grid place-items-center font-extrabold text-sm mb-3"
                style={{ background: '#DE7C33', color: '#fff' }}
              >
                {i + 1}
              </div>
              <div className="font-bold mb-1.5" style={{ fontFamily: "'Archivo', sans-serif" }}>
                {title}
              </div>
              <p className="text-[13.5px] leading-relaxed" style={{ color: '#51615E' }}>
                {body}
              </p>
            </div>
          ))}
        </div>
      </Section>

      {/* ================= FAQ ================= */}
      <div style={{ background: '#EAF0EE' }}>
        <Section id="faq" kicker={t.faqTitle} title={t.faqHead}>
          <div className="grid gap-3" style={{ maxWidth: 820 }}>
            {t.faq.map(([q, a], i) => (
              <div key={q} className="rounded-xl border bg-white overflow-hidden" style={{ borderColor: '#DBE4E1' }}>
                <button
                  onClick={() => setOpenFaq(openFaq === i ? -1 : i)}
                  className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left font-semibold text-[14.5px]"
                >
                  <span>{q}</span>
                  <span
                    className="shrink-0 text-lg leading-none transition-transform"
                    style={{ color: '#0E4B49', transform: openFaq === i ? 'rotate(45deg)' : 'none' }}
                  >
                    +
                  </span>
                </button>
                {openFaq === i && (
                  <div className="px-5 pb-4 text-[13.5px] leading-relaxed" style={{ color: '#51615E' }}>
                    {a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>
      </div>

      {/* ================= CONTACT ================= */}
      <Section id="contact" kicker={t.contactTitle} title={t.contactHead}>
        <div className="grid lg:grid-cols-2 gap-10">
          <div>
            <p className="text-[15px] leading-relaxed" style={{ color: '#51615E' }}>
              {t.contactSub}
            </p>
            <p className="mt-4 text-[13.5px]" style={{ color: '#7C8A87' }}>
              {t.contactNote}
            </p>
            <div className="mt-7 space-y-2 text-[14px]">
              <div className="font-bold" style={{ fontFamily: "'Archivo', sans-serif" }}>
                DataPOS
              </div>
              <a href="mailto:info@datapos.pro" className="block hover:underline" style={{ color: '#0E4B49' }}>
                info@datapos.pro
              </a>
              <a href="https://www.datapos.pro" className="block hover:underline" style={{ color: '#0E4B49' }}>
                www.datapos.pro
              </a>
            </div>
          </div>

          <form onSubmit={submit} className="rounded-2xl border p-6 grid gap-3" style={{ background: '#fff', borderColor: '#DBE4E1' }}>
            {[t.form.name, t.form.business, t.form.city, t.form.contact].map((ph) => (
              <input
                key={ph}
                required
                placeholder={ph}
                className="w-full rounded-lg border px-3.5 py-2.5 text-[14px] outline-none focus:border-[#0E4B49]"
                style={{ borderColor: '#DBE4E1', background: '#F5F8F6' }}
              />
            ))}
            <textarea
              rows={4}
              placeholder={t.form.message}
              className="w-full rounded-lg border px-3.5 py-2.5 text-[14px] outline-none focus:border-[#0E4B49] resize-none"
              style={{ borderColor: '#DBE4E1', background: '#F5F8F6' }}
            />
            <button
              type="submit"
              className="rounded-lg py-3 font-bold text-white text-sm transition-transform hover:-translate-y-px"
              style={{ background: '#0E4B49' }}
            >
              {t.form.send}
            </button>
            {sent && (
              <div
                className="rounded-lg px-3 py-2.5 text-[13px] font-semibold text-center"
                style={{ background: '#EAF0EE', color: '#1E9E5A' }}
              >
                {t.form.ok}
              </div>
            )}
          </form>
        </div>
      </Section>

      {/* ================= FOOTER ================= */}
      <footer style={{ background: '#0A3634' }}>
        <div className="mx-auto px-5 py-12" style={{ maxWidth: 1120 }}>
          <div className="flex flex-wrap items-start justify-between gap-8">
            <div style={{ maxWidth: 340 }}>
              <Logo light />
              <p className="mt-3 text-[13px] leading-relaxed" style={{ color: '#9CC4BF' }}>
                {t.footerTag}
              </p>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-10 gap-y-2 text-[13px]">
              {nav.concat([['contact', t.nav.contact]]).map(([id, label]) => (
                <a key={id} href={`#${id}`} onClick={go(id)} className="hover:text-white" style={{ color: '#9CC4BF' }}>
                  {label}
                </a>
              ))}
            </div>
          </div>
          <div
            className="mt-9 pt-6 border-t flex flex-wrap justify-between gap-3 text-[12px]"
            style={{ borderColor: 'rgba(156,196,191,.25)', color: '#9CC4BF' }}
          >
            <span>v1.0.0</span>
            <span>© {new Date().getFullYear()} DataPOS.pro</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

const SectionHead = ({ kicker, title }) => (
  <>
    <div className="text-[12px] font-bold tracking-[0.14em] uppercase mb-2" style={{ color: '#0E4B49' }}>
      {kicker}
    </div>
    <h2
      className="text-[clamp(1.6rem,3.4vw,2.4rem)] font-extrabold tracking-tight"
      style={{ fontFamily: "'Archivo', sans-serif" }}
    >
      {title}
    </h2>
  </>
);

const Section = ({ id, kicker, title, children }) => (
  <section id={id} className="px-5 py-16 scroll-mt-16">
    <div className="mx-auto" style={{ maxWidth: 1120 }}>
      <SectionHead kicker={kicker} title={title} />
      <div className="mt-9">{children}</div>
    </div>
  </section>
);

const Card = ({ title, body }) => (
  <div className="rounded-2xl border p-6 transition-transform hover:-translate-y-0.5" style={{ background: '#fff', borderColor: '#DBE4E1' }}>
    <div className="font-bold text-[15px] mb-1.5" style={{ fontFamily: "'Archivo', sans-serif" }}>
      {title}
    </div>
    <p className="text-[13.5px] leading-relaxed" style={{ color: '#51615E' }}>
      {body}
    </p>
  </div>
);

export default Landing;
