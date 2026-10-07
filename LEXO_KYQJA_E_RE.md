# DataPOS — hyrja e ridizajnuar

Ky është udhëzimi kryesor për këtë paketë. ZIP-i përmban aplikacionin e plotë, përfshirë përmirësimet responsive dhe korrigjimet e mëparshme.

## Çfarë ndryshoi
- Kartë hyrjeje e pastër, me sipërfaqe të bardha, hije të lehta, tipografi të lexueshme dhe ngjyra të përmbajtura.
- Zgjedhje e qartë midis hyrjes me PIN dhe administratorit, me etiketa në shqip.
- Tastierë numerike me butona të mëdhenj, gjendje aktive/disabled të dallueshme dhe mesazhe gabimi të lexueshme.
- Logoja e firmës nuk vendoset mbi sfond të gjelbër, nuk recolorohet, nuk pritet dhe nuk ka hije/kornizë me ngjyrë. Edhe ikona rezervë shfaqet pa katror të gjelbër. Nëse logoja dështon të ngarkohet shfaqet ikona rezervë.
- Për një logo plotësisht transparente përdorni PNG/WebP/SVG me transparencë. CSS nuk heq një sfond që është pjesë e vetë figurës/JPG-së.
- U hoq carousel-i nga hyrja për të shmangur shpërqendrimin; modulet paraqiten me ikonat e tyre në desktop. Telefoni shfaq firmën dhe formularin pa bllokun promocional të desktop-it.
- U ruajtën funksionet e hyrjes me PIN/Enter, hyrja e administratorit, tastiera virtuale, shfaqja e fjalëkalimit, device-lock dhe abonimi. Nuk u ndryshuan endpoint-et ose backend-i për këtë ridizajnim.
- Checkbox-i i vjetër Remember me dhe butoni Recover password nuk kishin funksion të lidhur me autentikimin; nuk paraqiten më si veprime të rreme.

## Instalimi dhe publikimi
Shpaketojeni ZIP-in në Desktop si Datapos-login-design dhe përdorni:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\Desktop\Datapos-login-design\APLIKO_KYQJA.ps1"
```

Për repository në rrugë tjetër shtoni -RepoPath "C:\rruga\e\repository". Skripti kontrollon versionin me gjurmë skedarësh (përfshirë CRLF të Windows), nuk mbishkruan ndryshime lokale, zgjedh patch-in e versionit të njohur dhe bën commit/push në main. Nuk përdor token të ruajtur në paketë dhe nuk bën force-push.

Pritni deployment-in FRONTEND në Vercel të jetë Ready dhe bëni Ctrl+Shift+R. Ridizajnimi i hyrjes është vetëm frontend. Nëse korrigjimet e vjetra të backend-it nuk janë publikuar ende, publikoni edhe backend-in nga paketa e plotë.

## Verifikimi
- 32 kontrolle të paraqitjes së JSX real të hyrjes në 8 madhësi: 320, 390, 768, 820, 1024, 1366, 1920 dhe landscape 844 px. U testuan PIN, administrator, gabim dhe logo prove transparente. Nuk pati overflow horizontal të faqes.
- 7 kontrolle interaktive të komponentit: tastiera/PIN/fshirja, argumentet e login-it, ndryshimi i mënyrës, shfaqja e fjalëkalimit, hyrja admin, tastiera virtuale dhe Enter/navigimi POS.
- Preview-t dhe kontrollet përdorin shims për auth/router/komponentët UI dhe një logo prove, jo databazën tuaj. Nuk janë test i autentikimit live ose i build-it të plotë.
- U inspektuan individualisht 5 pamje: laptop, telefon, formular administratori, logo pa sfond dhe gabim PIN-i. Kaluan edhe 31 kontrollet JS ekzistuese (23 sjellje, 8 responsive), parsimi i 90 skedarëve JS/JSX dhe git diff --check.
- Nuk u bë test në iPhone/iPad real/Safari ose deployment-in tuaj Vercel. Pas publikimit provoni të dy mënyrat e hyrjes dhe logon tuaj reale.

Pamjet në dosjen preview janë pamje testimi të dizajnit, jo screenshot nga firma juaj live. VERIFIKIMI_KYQJES.json dokumenton kontrollet me varësi të simuluara.
