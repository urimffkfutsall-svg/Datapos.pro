# Shiriti kompakt i sponsorëve

Ky ZIP përmban versionin e plotë me të gjitha korrigjimet e mëparshme.

- Shiriti në fund të hyrjes është më i ulët: rreth 90px desktop / 86px telefon, kur lëviz normalisht.
- U hoqën titulli Sponsorat dhe firmat, udhëzimi Klikoni një logo për të parë të dhënat e firmës dhe emrat e përsëritur poshtë logove. Emrat mbeten në etiketat për lexuesit e ekranit dhe në dritaren e detajeve.
- Vetëm logot shfaqen në një rresht të pastër me hapësira të balancuara, pa ndryshuar përmasat proporcionale ose skedarët origjinalë.
- Ruhen grayscale/hover me ngjyrë, animacioni djathtas-majtas, klikimi për detaje, ndalimi nën maus/fokus dhe reduced-motion. Me reduced-motion ose fokus tastiere lista mund të mbështillet për t’i mbajtur të gjitha logot të arritshme.
- Faqja e menaxhimit Sponsorat dhe firmat mbetet e pandryshuar për superadministratorin.

## Aplikimi
Shpaketojeni në Desktop si Datapos-sponsors-compact dhe ekzekutoni:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\Desktop\Datapos-sponsors-compact\APLIKO_KOMPAKT.ps1"
```

Skripti kontrollon versionin dhe ndryshimet lokale, aplikon patch-in dhe bën commit/push pa force-push. Pritni frontend-in në Vercel të jetë Ready dhe bëni Ctrl+Shift+R. Ky ndryshim është vetëm frontend; backend-i duhet përditësuar vetëm nëse paketa fillestare e sponsorëve nuk është publikuar.

Kontrollet lokale të komponentit (API/auth/UI të simuluara) kaluan për hover-in, klikimin, rifillimin dhe pesë gjerësi 320–1920px. U parsuan 93 skedarët JS/JSX dhe u inspektuan individualisht pamjet desktop/telefon. Preview-t përdorin logo sintetike prove. Nuk u krye build i plotë ose provë live në Vercel/Safari/pajisje reale.
