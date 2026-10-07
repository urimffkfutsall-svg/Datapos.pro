# DataPOS — Sponsorat dhe firmat

Ky është udhëzimi kryesor i kësaj pakete të plotë. Përfshihen të gjitha korrigjimet e mëparshme dhe hyrja e ridizajnuar.

## Përdorimi
1. Kyçuni si superadministrator.
2. Në menunë anësore hapni **Sponsorat dhe firmat**.
3. Klikoni **Shto sponsor / firmë**. Vendosni emrin, llojin, adresën, telefonin dhe lidhjet Facebook/Instagram/TikTok.
4. Ngarkoni logon nga PC-ja: PNG, JPG ose WebP deri në 2 MB. Preferohet PNG transparent. Logoja optimizohet në PNG me transparencën e ruajtur; SVG/skedarë aktivë nuk pranohen.
5. Shënoni **Shfaq në faqen publike të hyrjes** dhe klikoni **Ruaj regjistrimin**. Deri në ruajtje, ngarkimi është vetëm një preview i formularit.
6. Mund të ndryshoni, fshehni ose fshini regjistrime. Fshirja kërkon konfirmim. Fshehja i heq nga lista publike dhe nga adresa publike e logos.

Në fund të hyrjes shfaqen vetëm regjistrimet aktive. Logot ecin nga e djathta në të majtë, ndalojnë nën maus dhe nuk kanë më buton Ndalo/Vazhdo. Logot shfaqen gri/të zbehta dhe kthehen në ngjyrat origjinale nën maus ose gjatë fokusimit me tastierë. Klikimi hap adresën, telefonin dhe lidhjet sociale në një dritare. Telefoni është i klikueshëm. Lidhjet sociale hapen në tab tjetër. Preferenca reduced-motion çaktivizon animacionin dhe shfaq listë statike. Kur nuk ka regjistrime aktive, shiriti nuk shfaqet.

Renditja është sipas numrit që vendosni, pastaj sipas emrit. Fushat e kontaktit janë opsionale; për rrjetet sociale vendosni URL të plotë HTTPS, jo vetëm @emrin. Emri dhe logoja kërkohen gjatë shtimit.

## Ruajtja dhe dukshmëria
Të dhënat ruhen në koleksionin MongoDB partners. Logot ruhen si PNG i optimizuar në të njëjtin regjistrim, jo në /tmp të Vercel-it; nuk varen nga disku i përkohshëm i instancës. Nuk kërkohet shërbim i ri storage ose variabël e re environment. Aplikacioni duhet të ketë MONGO_URL dhe DB_NAME ekzistuese të sakta.

Lista është globale: regjistrimet aktive janë publike në faqet e hyrjes të DataPOS dhe të firmave. Nuk kopjohen automatikisht të dhënat e firmave ekzistuese. Formulari paralajmëron për publikimin; shtoni vetëm informacion që keni leje ta publikoni. Shembujt e preview-t janë sintetikë dhe nuk mbillen në databazën tuaj.

API-ja publike jep vetëm emrin, llojin, kontaktet e lejuara dhe URL-në e logos. Ndryshimet, ngarkimet dhe të dhënat e regjistrimeve të fshehura kërkojnë superadministrator. Lidhjet e rrjeteve sociale kontrollohen sipas platformës. Logot riekodohen për të hequr metadata dhe përmbajtje aktive. Logoja e ndryshuar ka version të ri URL-je; lista dhe imazhet publike nuk cache-ohen. Nuk u ndryshuan shitjet, resetimi ose llogaritja e raporteve.

## Instalimi
Shpaketojeni ZIP-in në Desktop si Datapos-sponsors dhe përdorni:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\Desktop\Datapos-sponsors\APLIKO_SPONSORAT.ps1"
```

Për repository në vend tjetër shtoni -RepoPath. Skripti kontrollon versionin dhe skedarët me CRLF të Windows, nuk mbishkruan ndryshime lokale, aplikon patch-in dhe bën commit/push në main pa force-push.

**Publikoni BACKEND-in dhe FRONTEND-in në Vercel nga i njëjti commit.** Vetëm frontend-i nuk mjafton: rrugët e reja të sponsorëve duhet të ekzistojnë në backend. Pritni që të dy deployment-et të jenë Ready, pastaj Ctrl+Shift+R. Pas publikimit krijoni një regjistrim prove dhe kontrolloni që logoja/detajet mbeten pas refresh-it. Nëse shfaqet 404, kontrolloni së pari backend deployment-in.

## Verifikimi dhe kufizimet
- 16 teste të reja backend: krijimi/ruajtja PNG, lista publike dhe filtrimi, fshehja, ndryshimi pa humbur logo, fshirja, lejet super-admin, ngarkimi, URL të pasigurta, transparenca dhe regjistrimi i rrugëve. Përdorin funksione reale me DB në memorie, jo HTTP/JWT/MongoDB real.
- Kaluan 59 testet backend ekzistuese: gjithsej 75. Kaluan 31 kontrollet JS ekzistuese. 93 skedarët JS/JSX u parsuan dhe Python compileall/diff-check kaluan.
- 14 kontrolle viewport për Login/Partners nga 320 në 1920px dhe 11 kontrolle interaktive me API/auth/UI të simuluara: animacioni djathtas-majtas, klikimi/detajet, ndalimi, reduced-motion, upload/krijimi, single-flight, ndryshimi/fshehja, fshirja, ruajtja e draft-it në dështim dhe ndalimi i roleve të tjera.
- U inspektuan individualisht katër screenshot-e: hyrja desktop me shirit, detajet në telefon, editori desktop dhe lista në telefon. Dosja preview dhe raportet dokumentojnë prova me të dhëna sintetike, jo firmat tuaja live.
- Nuk u krye build i plotë i aplikacionit, test me MongoDB tuaj, autentikim HTTP real, Safari në pajisje reale ose deployment live. Kryeni provën përfundimtare pas publikimit të të dy pjesëve.
