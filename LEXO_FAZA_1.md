# Faza 1 — besueshmëria e shitjeve

KUJDES PARA PUBLIKIMIT: ky version kërkon MongoDB 4.4+ Atlas / replica set / cluster që mbështet transaksione. Një MongoDB standalone nuk mbështetet: shitja refuzohet pa ndryshuar stokun. Kërkohen leje për krijimin e koleksioneve ndihmëse. Mos e publikoni pa backup dhe provë në ambient testimi.

## Çfarë përfshin
- Ruajtjen në një transaksion të shitjes, stokut, lëvizjeve, arkës, përdorimit të kuponit dhe auditimit. Refuzimi ose dështimi nuk duhet të lërë një shitje pjesërisht të ruajtur.
- Kontrollin e të gjitha produkteve, sasive, pagesave dhe kuponit para ndryshimeve të të dhënave të biznesit.
- Identifikues të qëndrueshëm për kërkesën, të lidhur me firmën dhe përdoruesin. Përsëritja kthen rezultatin e ruajtur. Ndryshimi i të dhënave me të njëjtin identifikues refuzohet.
- Ruajtjen lokale të një kërkese të pakonfirmuar; pas refresh-it rikthehet shporta dhe pagesa e saj. Mos e ndryshoni atë pa verifikuar rezultatin.
- Numërim atomik për firmë/ditë në Europe/Tirane. Formati i ri RCP-YYYYMMDD-S-000001 nuk përplaset me formatin historik. Resetimi i ditës nuk fshin numëruesin ose identifikuesit e kërkesave.
- Llogaritje në Decimal në server dhe centë/racionalë në POS, me rrumbullakim HALF_UP për çdo rresht. Printimi përdor totalet e konfirmuara nga serveri.
- Ulje stoku me shtesa atomike, bashkim të sasive të të njëjtit produkt dhe përdorim të njësive reale kur shitet një pako.
- Pagesa të pjesshme të borxhit llogariten nga serveri dhe pjesa cash regjistrohet në arkë. Nuk ndryshohen automatikisht gjendjet historike të krijuara nga versionet e vjetra.
- Shitjet offline shënohen si të ruajtura në pajisje, jo të konfirmuara në server. Nuk shtypet një kupon i konfirmuar për një shitje ende në pritje.
- Radha ruan identifikuesin gjatë sinkronizimit; veprimet e refuzuara ruhen me gabimin dhe nuk hidhen poshtë. Butoni Provo përsëri përdor të njëjtin identifikues. Veprimet e reja që mbërrijnë gjatë sinkronizimit nuk humbin.
- Cache dhe radha lidhen me llogarinë/firmën. Një përdorues tjetër nuk i sinkronizon. Mungesa e hapësirës lokale nuk raportohet si ruajtje e suksesshme.
- Dështimi i printimit pas një shitjeje të konfirmuar nuk krijon shitje të re. Rihapeni kuponin nga Dokumentet.

Kjo fazë mbulon krijimin e shitjeve në Arka POS e përgjithshme. Nuk është konvertim i plotë i moduleve Mobilshop, PhoneSoftware, BookPRO, HealthPRO ose i pagesave të mëvonshme të borxhit në transaksione.

## PARA përditësimit
1. Sinkronizoni radhët offline me versionin e vjetër. Elementet e vjetra pa identitet llogarie nuk dërgohen automatikisht nga versioni i ri; mbeten në pajisje dhe kërkojnë verifikim manual. Mos pastroni localStorage/cache-in e shfletuesit.
2. Bëni backup të plotë të databazës dhe provoni rikthimin në ambient testimi.
3. Me varësitë e backend-it të instaluara dhe MONGO_URL/DB_NAME të konfiguruara lokalisht, ekzekutoni `python backend/scripts/check_transactions.py`. Kontrolli është vetëm lexim dhe nuk shtyp sekrete. Rezultati GATI kontrollon mbështetjen strukturore; nuk zëvendëson provën reale të shitjes/transaksionit.
4. Publikoni fillimisht në staging dhe provoni shitje, përsëritje, ndërprerje rrjeti, dy arka njëkohësisht, kupon të pavlefshëm, pako dhe pagesë borxhi. Për testimin e gabimeve përdorni të dhëna prove, jo shitje reale.
5. Publikoni backend-in, pastaj frontend-in nga i njëjti version. Backend-i ekspozon edhe GET /api/sales/readiness për një përdorues të kyçur; transaction_capable duhet të jetë true.

## Aplikimi në GitHub
Shpaketojeni ZIP-in në Desktop si Datapos-professional-phase1. Vetëm pasi plotësohen kushtet e mësipërme:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\Desktop\Datapos-professional-phase1\APLIKO_FAZA1.ps1"
```

Skripti kërkon konfirmim të kontrollit/backup-it, kontrollon versionin/ndryshimet lokale dhe bën commit/push nga PC-ja juaj, pa force-push. Pritni BACKEND dhe FRONTEND Ready, pastaj Ctrl+Shift+R. Nëse Vercel-i juaj publikon direkt në prodhim pas push-it, bëjeni staging-un dhe kontrollet përpara ekzekutimit të skriptit.

## Kufijtë dhe fazat pasuese
- Nuk ndryshohet politika e mëparshme që mund të lejojë stok negativ; përcaktimi i saj sipas firmës/roleve mbetet fazë tjetër.
- Fshirja nga raportet nuk bëhet kthim produkti. Procesi i kthimit dhe mbyllja profesionale e ditës mbeten faza tjetër; resetimi aktual mbetet i pandryshuar.
- 2FA, kufizimi i tentativave të hyrjes, çelësi JWT/CORS i prodhimit, lejet e imta, backup automatik dhe unifikimi i plotë i faqeve NUK janë përfunduar në këtë fazë.
- Numrat/llogaritjet historike nuk rishkruhen. API-të e vjetra që nuk dërgojnë request_id mbeten funksionale, por nuk kanë mbrojtje të plotë kundër përsëritjes; duhet publikuar frontend-i i ri.

## Testet e kryera
95 teste backend: 75 regresione dhe 20 teste të shërbimit të ri; 43 kontrolle JS dhe 97 skedarë JS/JSX të parsuar. Shërbimi real Decimal/ruajtje u testua me adapter transaksionesh në memorie: gabime në çdo shkrim, rollback, replay, izolim, kupon, borxh, pako dhe numërim. Adapteri serializon provat e njëkohësisë; nuk është provë e konfliktit real MongoDB. Motor/read-concern/commit-retry nuk u testuan me server real. UI e njoftimit u kontrollua me React dhe API/CSS të simuluara, me pamje desktop/telefon. Nuk u krye build i plotë, provë live Vercel, auditim i plotë sigurie apo test real MongoDB/Safari/pajisjeje. Paketa është për kontroll dhe publikim të kushtëzuar, jo pretendim se prodhimi është verifikuar.
