; ==========================================================================
; DataPOS - skript shtese per instaluesin NSIS
; --------------------------------------------------------------------------
; Sa here qe aplikacioni instalohet (edhe rishtazi ne te njejtin kompjuter),
; fshihet konfigurimi i firmes dhe kycja e pajisjes, qe instalimi te nise
; gjithmone me dritaren e konfigurimit.
; ==========================================================================

!macro customInstall
  ; Konfigurimi i firmes per kete PC
  Delete "$APPDATA\DataPOS\firm.json"
  Delete "$APPDATA\DataPOS\device-lock.json"

  ; Nese aplikacioni eshte instaluar per te gjithe perdoruesit,
  ; pastrohet edhe profili i perdoruesit aktual.
  Delete "$LOCALAPPDATA\DataPOS\firm.json"
  Delete "$LOCALAPPDATA\DataPOS\device-lock.json"
!macroend

!macro customUnInstall
  ; Gjate cinstalimit hiqet vetem konfigurimi, jo te dhenat offline.
  Delete "$APPDATA\DataPOS\firm.json"
  Delete "$APPDATA\DataPOS\device-lock.json"
!macroend
