# Logot gri me ngjyrë nën maus

Ky version i plotë përfshin të gjitha ndryshimet e mëparshme. Ndryshimi i ri prek vetëm frontend-in:
- Logot në shiritin e sponsorëve shfaqen grayscale, me opacitet 62%.
- Nën maus ose fokus me tastierë rikthehen ngjyrat origjinale dhe opaciteti 100%.
- Butoni Ndalo/Vazhdo lëvizjen u hoq. Lëvizja vazhdon automatikisht, ndalet nën maus/fokus dhe gjatë hapjes së detajeve; mbyllja e detajeve e lejon sërish lëvizjen.
- Klikimi dhe të dhënat e firmës mbeten funksionale. Logoja brenda detajeve, logoja e firmës në hyrje dhe logot në panelin e menaxhimit nuk zbehen.
- Preferenca reduced-motion vazhdon të respektohet. Skedarët origjinalë të logove nuk ndryshohen.

## Aplikimi
Shpaketojeni në Desktop si Datapos-logo-hover dhe ekzekutoni:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\Desktop\Datapos-logo-hover\APLIKO_LOGOT.ps1"
```

Skripti kontrollon ndryshimet lokale dhe versionin, aplikon patch-in përkatës dhe bën commit/push pa force-push. Pritni frontend-in në Vercel të jetë Ready dhe bëni Ctrl+Shift+R. Backend-i nuk ndryshoi nga paketa e sponsorëve; nëse nuk e keni publikuar atë paketë, publikoni edhe backend-in për rrugët e sponsorëve.

## Verifikimi
U testuan në komponentin real me API/auth/UI të simuluara: grayscale/opaciteti normal, ngjyra në hover, mungesa e butonit, ndalimi nën maus, klikimi/detajet, ngjyra origjinale brenda detajeve, rifillimi pas mbylljes dhe kthimi në gri pas largimit të mausit. U kontrolluan 5 gjerësi nga 320 në 1920px. U inspektuan pamjet e telefonit dhe hover-it në desktop me logo sintetike prove. Nuk u krye build i plotë ose provë live në Vercel/pajisje reale.
