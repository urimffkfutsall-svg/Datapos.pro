# Hyrja vetëm me logon dhe emrin e firmës

U hoqën Hapësira juaj e punës, ME DATAPOS, titulli Punë më e thjeshtë/Kontroll më i plotë, përshkrimi, lista Arka POS/Produkte/Raporte/Klientët/Stoku dhe firma Powered by nga paneli i majtë.

Paneli tani shfaq vetëm logon e firmës të qendruar dhe më të madhe, me emrin e firmës poshtë. Në telefon vendosen sipër formularit. Merren automatikisht nga logo_url/company_name e firmës së atij domain-i; nuk përdoret logo e sponsorëve si logo e firmës. Logoja ruan transparencën, ngjyrën dhe proporcionet. Nëse mungon ose nuk ngarkohet, mbetet ikona rezervë dhe emri.

Ruhen dark green, PIN/Administrator, sponsori kompakt dhe të gjitha rregullimet e pagesës, katalogut, raporteve dhe backend-it.

## Instalimi
Shpaketoni ZIP-in në Desktop si Datapos-company-login dhe ekzekutoni:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\Desktop\Datapos-company-login\APLIKO_LOGO_FIRMA.ps1"
```

Skripti kontrollon ndryshimet lokale/versionin dhe bën commit/push nga PC-ja juaj pa force-push. Pritni frontend-in në Vercel të jetë Ready dhe bëni Ctrl+Shift+R. Ky ndryshim është vetëm frontend; në këtë hap nuk kërkohet ndryshim backend-i nga versioni i mëparshëm.

## Kontrollet
Komponenti real Login u provua me API/auth/UI të simuluara në 8 madhësi nga 320 në 1920px. U kontrolluan heqja e teksteve nga DOM-i, logo transparente/proporcionale/me ngjyra, mungesa e tejkalimit horizontal, PIN/Administrator dhe emri i gjatë pa logo. U inspektuan individualisht pamjet desktop, telefon dhe administrator në telefon. Preview-t përdorin logo sintetike prove, jo logon tuaj reale. Nuk u krye build i plotë ose provë live Vercel/Safari/pajisje reale.
