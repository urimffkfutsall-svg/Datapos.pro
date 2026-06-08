cd C:/Users/urim5/Desktop/datapos12-main/frontend

$bogus = Join-Path $PWD "srcindex.css"
$real  = Join-Path $PWD "src/index.css"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

if (Test-Path $bogus) {
  $cssToAdd = [System.IO.File]::ReadAllText($bogus)
  Write-Host ("Gjeta CSS bogus me {0} karaktere" -f $cssToAdd.Length) -ForegroundColor Cyan

  if (Test-Path $real) {
    $existing = [System.IO.File]::ReadAllText($real)
    if ($existing -notmatch "MODERN DESIGN SYSTEM v2") {
      [System.IO.File]::WriteAllText($real, $existing + $cssToAdd, $utf8NoBom)
      Write-Host "OK: u bashkua me src/index.css" -ForegroundColor Green
    } else {
      Write-Host "Tashme i aplikuar - pa ndryshime" -ForegroundColor Yellow
    }
  } else {
    Write-Host "ERROR: src/index.css mungon!" -ForegroundColor Red
  }

  Remove-Item $bogus -Force
  Write-Host "File bogus u fshi" -ForegroundColor Green
} else {
  Write-Host "S'gjet file bogus 'srcindex.css'" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Verifikim final:" -ForegroundColor Cyan
$tw = Select-String -Path "tailwind.config.js" -Pattern "brand:" -SimpleMatch -Quiet
$css = Select-String -Path "src/index.css" -Pattern "MODERN DESIGN SYSTEM v2" -SimpleMatch -Quiet
if ($tw)  { Write-Host "  tailwind brand: OK"  -ForegroundColor Green } else { Write-Host "  tailwind brand: MUNGON"  -ForegroundColor Red }
if ($css) { Write-Host "  index.css modern: OK" -ForegroundColor Green } else { Write-Host "  index.css modern: MUNGON" -ForegroundColor Red }