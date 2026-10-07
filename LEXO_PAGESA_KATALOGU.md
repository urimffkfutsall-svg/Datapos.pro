# Hyrja dark green, katalogu dhe pagesa responsive

Version i plotë që ruan të gjitha korrigjimet e mëparshme.

## Ndryshimet
- Hyrja: kontur dark green, theks në pjesën e sipërme dhe nuancë e butë në formular. Logot e ngarkuara mbeten pa sfond të gjelbër; shiriti kompakt i sponsorëve ruhet.
- Katalogu: i mbyllur në çdo hyrje/refresh/hapje të re arke. Hapet vetëm nga përdoruesi. Çdo hapje merr afat të ri 60 sekonda; mbyllja manuale anulon afatin e vjetër. Pas kthimit nga një tab në sfond, nëse minuta ka kaluar, mbyllet.
- Pagesa: dritare e kufizuar sipas lartësisë dhe gjerësisë reale të ekranit. Titulli/mbyllja dhe veprimet e përfundimit mbeten të arritshme. Në ekran të ulët, fushat lëvizin brenda dritares — nuk zvogëlohen të gjitha shkrimet dhe nuk priten butonat.
- Në ekran të gjerë numpad dhe përmbledhja shfaqen në dy kolona; në telefon në një kolonë. Dritarja ndjek visualViewport edhe kur hapet tastiera mobile.
- Nuk hapet automatikisht tastiera native në pajisje touch kur hapet pagesa. Futja manuale dhe numpad mbeten funksionale.
- Ruhen Cash/Bank, kuponi, borgji, klienti, printimi direkt, konfirmimi me dy Enter dhe mbrojtja nga shitjet e dyfishta.

## Aplikimi
Shpaketojeni ZIP-in në Desktop si Datapos-checkout-fixed. Ekzekutoni:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\Desktop\Datapos-checkout-fixed\APLIKO_PAGESA.ps1"
```

Skripti kontrollon repo-n dhe versionin, nuk mbishkruan ndryshime lokale dhe nuk përdor force-push. Bën commit/push në origin/main nga PC-ja juaj. Pritni frontend-in në Vercel të jetë Ready dhe rifreskoni Ctrl+Shift+R. Backend-i nuk ndryshoi nga versioni i sponsorëve.

## Verifikimi
95 skedarë JS/JSX u parsuan; 31 testet ekzistuese JS dhe testet e reja të timer-it/strukturës kaluan. Komponenti i pagesës dhe hook-u real u provuan me UI/CSS-utility/shitje të simuluara në 8 madhësi 320–1366px, duke përfshirë laptop, tablet, telefon dhe orientim horizontal; u provua zvogëlimi i visualViewport si kur hapet tastiera. Katalogu u provua në 59999/60000ms, me anulim/rifillim dhe ndërrim arke. U inspektuan pamjet desktop/telefon të hyrjes dhe laptop/telefon/tablet/tastierë të pagesës.

Preview-t përdorin logo sintetike dhe komponentë UI të thjeshtuar. Nuk u krye build i plotë i frontend-it ose provë live në Vercel, MongoDB, Safari apo pajisje reale. Testet mund të ekzekutohen me node tests/test_checkout_regressions.cjs dhe testet e tjera tests/*.cjs pasi të jenë instaluar varësitë e frontend-it.
