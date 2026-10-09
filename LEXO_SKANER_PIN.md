# Skanimi i menjëhershëm dhe regjistrimi me miratim të administratorit

## Sjellja
- Fusha “Kërko produktet ose skano barkod” merr fokus automatik kur hyni në POS, kur hapni arkën dhe kur mbyllni dritaret/shitjen. Rifreskimi pas shitjes bëhet në sfond: fusha nuk zhduket gjatë ngarkimit.
- Nuk merret fokusi nga fusha e pagesës, sasia, PIN-i, formularët apo dritaret e hapura. Pas mbylljes së tyre kthehet te skanimi.
- Skaneri USB/Bluetooth duhet të punojë si tastierë dhe të dërgojë Enter pas barkodit. Nuk kërkohet klik në fushë. Një skaner në modalitet tjetër duhet konfiguruar nga pajisja.
- Barkodi i njohur shton produktin. Për barkod të panjohur serveri verifikon mungesën: vetëm 404 “Produkti nuk u gjet” hap formularin. Gabimi i rrjetit nuk konsiderohet produkt i panjohur.
- “Regjistro këtë produkt”: emri, çmimi i shitjes/blerjes, TVSH-ja, njësia dhe kategoria. Pastaj “Regjistro produktin” hap PIN-in e administratorit; nuk ruan ende asgjë.
- PIN-i verifikohet për çdo produkt nga serveri, kundrejt një administratori aktiv të së njëjtës firmë. PIN-i i arkatarit/menaxherit, firmës tjetër, administratorit të çaktivizuar ose PIN i dyfishuar refuzohet. PIN 4–12 shifra, unik: vendoseni te përdoruesi me rol Administrator nga faqja e përdoruesve. Nuk ju kërkohet ta ndani PIN-in në chat.
- Sesioni mbetet i arkatarit. Regjistrimi ka audit për arkatarin dhe administratorin miratues, pa PIN. PIN-i nuk ruhet në storage apo radhën offline; kërkohet internet. Pesë tentativa të gabuara për arkatar brenda një intervali 5-minutësh kufizohen; ka edhe kufi të përbashkët për firmën.
- Stoku i produktit të ri është 0; furnizimin e regjistroni te produktet. Pas ruajtjes skanoni përsëri barkodin për ta shtuar në shitje. Politika ekzistuese e shitjes pa stok nuk ndryshon.
- GET i profileve/listës së përdoruesve nuk kthen PIN-et. Cache-i i vjetër i listës së përdoruesve hiqet kur ngarkohet versioni i ri.

## Instalimi
Shpaketoni ZIP-in në Desktop jashtë repository-t. Mbajeni APLIKO_SKANER_PIN.ps1 pranë profiles.json dhe patch-eve. Instaluesi bën kontroll versioni, git apply, commit dhe push nga PC-ja juaj, pa force dhe pa mbishkrim të ndryshimeve lokale. Ndryshon vetëm skanimin/regjistrimin/miratimin, mbrojtjen e PIN-eve dhe rifreskimin e POS-it në sfond. Ruhet pamja milky white, pozicioni i përmbledhjes së pagesës që keni dhe varianti ekzistues i përpunimit të shitjeve (me/pa fazën 1).

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\APLIKO_SKANER_PIN.ps1 -RepoPath "C:\Users\urim5\Desktop\Datapos.pro-fixed\Datapos.pro"
```

Duhet të publikoni backend-in DHE frontend-in e këtij përditësimi. Prisni që të dy të jenë Ready, pastaj Ctrl+Shift+R. Nëse backend-i ka projekt/deployment të veçantë në Vercel, kontrollojeni atë veçmas: publikimi vetëm i frontend-it nuk mjafton. Pa endpoint-in e ri regjistrimi refuzohet; nuk ruhet lokalisht si i miratuar. Përdorni backup/staging përpara prodhimit. Në dështim të push-it pas commit-it mos e riaplikoni paketën; commit-i mbetet lokalisht.

ZIP-i përmban edhe burimin e plotë më të fundit (me fazën 1 të dërguar më herët). Përdorni instaluesin për këtë ndryshim: mos kopjoni manualisht gjithë backend-in nëse nuk keni konfirmuar kushtet e LEXO_FAZA_1.md. Instaluesi nuk shton fazën 1 aty ku nuk është instaluar.

## Verifikimi dhe kufijtë
107 teste lokale backend: 95 regresione ekzistuese + 12 teste të miratimit/modeleve reale me DB të simuluar. 49 grupe regresionesh JavaScript. 99 skedarë JS/JSX parsuar dhe backend-i kompilohet. POS-i i plotë, formulari dhe hook-et reale u provuan në Chromium lokal me UI primitive/API të simuluara: fokus fillestar, skanim, shitje dhe skanim gjatë rifreskimit të ngadaltë, barkod i panjohur, të dhëna pastaj PIN, gabim PIN/ruajtje e vetme/anulim, mosndryshim sesioni dhe mosruajtje PIN-i. U kontrolluan formulari dhe miratimi në laptop/telefon. Regresionet e pagesës/katalogut kaluan në 8 madhësi ekrani. Patch-et aplikohen në kopje të varianteve të mbështetura.

Nuk është test live në serverin tuaj, build i plotë React, test fizik skaneri, Safari apo MongoDB/HTTP real. Testet e vjetra live që kërkojnë pytest/shërbim aktiv nuk u ekzekutuan në këtë mjedis; mos e lexoni këtë si audit të plotë sigurie. Pranimi në staging: hap arka → skano produkt → shitje → skano pa klik → barkod i ri → të dhëna → PIN i gabuar → PIN i administratorit → skano produktin e ri. Provoni edhe PIN të firmës tjetër dhe internet të shkëputur.
