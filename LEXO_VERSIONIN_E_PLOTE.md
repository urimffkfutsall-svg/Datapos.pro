# DataPOS — versioni i korrigjuar, 7 tetor 2026

## Çfarë u korrigjua
- Menaxhimi global i firmave nuk varet më nga ekzistenca e firmës së domain-it të hapur, pasi verifikohet JWT dhe llogaria reale Super Admin.
- Identifikimi i firmës është i përbashkët për login/API me backend në Vercel; header-i i dubluar identik pranohet, firma të ndryshme refuzohen.
- Butonat e firmave tani mbështillen në ekrane të ngushta, në vend që të dalin jashtë pamjes. Domain-et e paraqitura janë .datapos.pro, jo .app.com.
- Krijimi validon subdomain-in/fushat dhe ruan planin e abonimit. Fjalëkalimi përpunohet para krijimit të firmës; dështimi i krijimit të adminit anulon firmën e sapokrijuar.
- Fshirja arkivon firmën dhe regjistrimet e koleksioneve që kanë tenant_id përpara heqjes. Backup-et në tenant_deletion_backups ruhen, auditimi historik ruhet. Nëse backup-i dështon, nuk fillon fshirja. Nëse mbeten të dhëna nga shkrime konkurrente, firma mbetet e pezulluar dhe kthehet gabim, jo sukses i rremë. Riprovoni nga Super Admin pasi të ndalen pajisjet e firmës.
- Gabimet e API-së shfaqen qartë; validimet 422 shfaqen si tekst. Klikimet e përsëritura nuk dërgojnë të njëjtin veprim të menaxhimit paralelisht.
- Te Përdoruesit → Edito mund të vendosni fjalëkalim të ri për administratorin e një firme. Bosh do të thotë pa ndryshim. Nuk dërgohet hash/fjalëkalim në përgjigje/auditim.
- Nisja e serverit nuk ndryshon më kredencialet ekzistuese të Super Admin. Endpoint-i i vjetër publik që i rivendoste ato është çaktivizuar.
- Përdoruesit joaktivë/firmat e pezulluara nuk vazhdojnë me sesione të vjetra; administratori i firmës nuk mund të krijojë/promovojë Super Admin.
- Përfshihen të gjitha korrigjimet e mëparshme: reset ditor/mujor në server, raporte pa cache të vjetër, panel vetëm shitjesh, produkte në vend të RCP, fshirje shitjesh dhe konfirmimi me Enter në POS.

## Instalimi në repository ekzistues
Shpaketoni ZIP-in në Desktop si Datapos-full-fixed. Ekzekutoni:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\Desktop\Datapos-full-fixed\APLIKO_PLOTE.ps1"
```

Skripti kontrollon që repository është pa ndryshime lokale dhe e përputh versionin me fingerprint-et e skedarëve para zgjedhjes së patch-it. Nuk bën force-push, nuk fshin ndryshime lokale dhe nuk përdor kredenciale nga chat-i. Rruga standarde është repository që keni përdorur më parë. Për rrugë tjetër përdorni -RepoPath. Nëse versioni nuk përputhet, ndalon; mos kopjoni verbërisht skedarë mbi një repository me ndryshime të tjera.

## Publikimi
1. Publikoni BACKEND-in dhe frontend-in nga i njëjti commit. Backend-i përdor backend/server.py dhe backend/vercel.json; frontend-i përdor root directory frontend, npm ci --legacy-peer-deps dhe npm run build.
2. Kontrolloni që REACT_APP_BACKEND_URL tregon te projekti real API në Vercel. Pritni Ready te të dy projektet; pastaj rifreskoni.
3. Mbani MONGO_URL, DB_NAME dhe JWT_SECRET e saktë në backend. Vendosni një JWT_SECRET privat dhe të fortë; nëse e ndërroni, të gjithë duhet të kyçen sërish. Nuk ka sekrete në këtë paketë.
4. Llogaritë ekzistuese Super Admin nuk ndryshojnë. Vetëm në databazë të re, BOOTSTRAP_ADMIN_USERNAME dhe BOOTSTRAP_ADMIN_PASSWORD mund të krijojnë llogarinë fillestare. Mos përdorni endpoint-in e vjetër init për rikuperim fjalëkalimi.
5. Për menaxhim global përdorni datapos.pro ose www.datapos.pro dhe llogarinë Super Admin. Për shitjet/resetimin përdorni subdomain-in dhe administratorin e firmës. Resetimi kërkon fjalëkalimin e asaj llogarie, jo PIN-in.

## Çfarë u verifikua dhe çfarë jo
59 teste Python offline (21 firma/siguri, 17 routing/autentikim, 21 reset/raporte), 23 kontrolle JS për menaxhim, sesion dhe POS/offline; 90 skedarë JS/JSX u parsuan dhe të gjithë skedarët Python u kontrolluan/kompiluan. Testet ushtrojnë trupat realë të funksioneve me databazë/JWT decode të simuluara; nuk janë integrim real MongoDB ose FastAPI HTTP.

Nuk u përfundua build-i i plotë frontend dhe nuk u nis serveri i plotë: varësitë e FastAPI/Motor/React toolchain mungojnë dhe instalimi nuk i gjeti paketat në këtë mjedis. Nuk u bë provë në Vercel/MongoDB tuaj. Modulet shtesë HealthPRO, BookPRO, shipping dhe Mobilshop u kontrolluan për sintaksë, jo për çdo rrjedhë funksionale. Kjo nuk është garanci se çdo gabim i mundshëm është eliminuar.

## Prova pas publikimit
- Krijoni një firmë testimi dhe verifikoni planin/përdoruesin; editoni dhe fshijeni vetëm pasi të mos ketë të dhëna reale.
- Hyni si administratori i firmës, realizoni një shitje testimi dhe bëni reset ditor me fjalëkalimin e saktë. Prisni mesazhin e konfirmimit të serverit; pastaj bëni refresh.
- Verifikoni që firma tjetër dhe produktet/stoku nuk janë ndryshuar nga resetimi.
- Nëse një kërkesë dështon, dërgoni vetëm URL/status/Response; mos përfshini Authorization, PIN ose fjalëkalime.
