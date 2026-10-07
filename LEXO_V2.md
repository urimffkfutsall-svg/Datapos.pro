# DataPOS – Paneli vetëm për shitjet (V2)

Ky version zëvendëson panelin dhe faqen Raportet të versionit të mëparshëm.

## Ndryshimet

- Paneli i firmës shfaq vetëm shitjet ditore, mujore dhe vjetore, totalet dhe listën e periudhës. Janë hequr kartat e transaksioneve, produkteve, stokut të ulët, klientëve, fitimit dhe të gjithë grafiqet/numrat demonstrues.
- Te lista ditore administratori mund të fshijë një shitje. Ajo fshihet në server dhe nuk hyn në totalet ditore/mujore/vjetore ose në raportet e printuara.
- Resetimi i ditës ose muajit fshin shitjet e periudhës aktuale, me backup para fshirjes. Serveri verifikon se dokumentet e kapura janë hequr para se të konfirmojë suksesin. Totali i periudhës së resetuar mbetet 0 pas leximit të ri, për sa kohë nuk bëhet një shitje e re. Resetimi i ditës nuk zeron shitjet e ditëve të tjera të muajit/vitit; resetimi i muajit nuk zeron muajt e mëparshëm të vitit.
- Krahasimet e datave në MongoDB përdorin data të konvertuara, jo krahasim tekstesh: mbulohen timestamp-et legacy me Z, offset dhe BSON Date.
- Përgjigjet e shitjeve/raporteve nuk cache-ohen. Nuk lejohet një raport financiar i vjetër nga offline cache.
- Ndërfaqja kërkon versionin e ri të backend-it. Nëse është publikuar vetëm frontend-i, shfaqet gabim i qartë, jo sukses i rremë ose shifra të vjetra. Kjo është veçanërisht e rëndësishme për instalimin me Vercel.
- Faqja Raportet ka vetëm zgjedhjen e datës dhe katër butona: printo ditën, javën, muajin dhe vitin. Printimi merr të gjithë rreshtat në një përgjigje, jo vetëm faqen e parë. Mund të përdorni Save as PDF në dialogun e printimit.
- Muaji/viti/java përcaktohen nga data e zgjedhur. Java fillon të hënën. Zona e backend-it është BUSINESS_TIMEZONE, parazgjedhja Europe/Tirane.
- Ndryshimet e arkës F2/Enter nga versioni i parë janë ruajtur.

## Testimi dhe kufijtë

21 teste backend me Mongo-style fake kaluan, duke përfshirë resetimin/leximin përsëri, datat legacy, izolimin e firmave, fshirjen nga të gjitha raportet, shitjet e reja pas resetimit dhe printimin me më shumë se 100 rreshta. Kaluan edhe 7 kontrollet JavaScript të pagesës/offline. Sintaksa e 87 skedarëve JS/JSX dhe sintaksa Python u kontrolluan. Pamjet e reja u renderuan lokalisht me komponentët realë prezantues dhe të dhëna test.

Nuk është bërë test end-to-end me MongoDB reale ose me domain-in live. Pamjet që dërgoi përdoruesi nuk përmbanin Response/Request URL të reset-data; shkaku specifik në instalimin live nuk është konfirmuar. Build-i i plotë mbetet i paverifikuar sepse varësitë nuk mund të shkarkohen në këtë mjedis. Ky ZIP nuk do të thotë se faqja live është ndryshuar.

## Aplikimi mbi commit-in e mëparshëm 038b548

1. Shpaketoni ZIP-in në Desktop në mënyrë që skripti të jetë te C:\Users\urim5\Desktop\Datapos-sales-v2\APLIKO_V2.ps1.
2. Ekzekutoni në PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\Desktop\Datapos-sales-v2\APLIKO_V2.ps1"
```

Skripti përdor repository-n ekzistues C:\Users\urim5\Desktop\Datapos.pro-fixed\Datapos.pro, kontrollon që ai të jetë pa ndryshime lokale, kontrollon patch-in, aplikon ndryshimet, krijon commit dhe bën push në origin/main. Nuk bën clone, reset ose force-push. Nëse repository ndodhet tjetërkund, shtoni -RepoPath "RRUGA_E_REPO". Nëse patch-i nuk përputhet, ndaloni dhe dërgoni gabimin.

3. Publikoni backend-in dhe frontend-in bashkë. Nëse Vercel ndërton vetëm frontend/, backend-i i veçantë duhet të publikohet nga i njëjti commit. Në kod ekziston render.yaml për backend-in; kjo nuk provon ku është hostuar instalimi live.
4. Prisni publikimin e suksesshëm. Nëse paneli tregon “Backend-i i ri ... nuk është publikuar”, mos resetoni sërish: kontrolloni publikimin e backend-it dhe adresën e konfigurimit REACT_APP_BACKEND_URL.
5. Provoni në firmë test: shitje → reset ditor → refresh; pastaj muajin. Provoni një fshirje dhe printoni secilën periudhë. Firma tjetër nuk duhet të preket.

Paketa ka edhe kodin e plotë dhe patch-in datapos-panel-v2.patch. Mos ngarkoni patch/bundle si pjesë e varësive të aplikacionit.

## Kujdes

Sinkronizoni të gjitha pajisjet offline para resetimit. Pas resetimit hapeni përsëri arkën. Resetimi dhe fshirja nuk rikthejnë stokun. Dobësitë ekzistuese te inicializimi i super-adminit të përmendura në dokumentin e parë nuk janë pjesë e këtij ndryshimi dhe duhet të mbrohen para publikimit në prodhim.
