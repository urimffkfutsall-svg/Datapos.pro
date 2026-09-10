<#
===========================================================================
 DataPOS - Ndertimi i setup.exe (PowerShell)
---------------------------------------------------------------------------
 Zgjidh problemin:
   "remove ...\resources\app.asar: The process cannot access the file
    because it is being used by another process"

 Si e zgjidh:
  1. Mbyll te gjitha procesat qe mbajne app.asar te hapur.
  2. Mbyll dritaret e Explorer-it te hapura ne dosjet e daljes.
  3. Ndertimi shkon ne dosje TE RE me stamp kohor - edhe nese dosja e vjeter
     mbetet e bllokuar nga Defender-i, ndertimi vazhdon pa gabim.
  4. Fshin dosjet e vjetra vetem nese jane te lira.

 Perdorimi:
   powershell -ExecutionPolicy Bypass -File .\build-setup.ps1
===========================================================================
#>

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "=== DataPOS - ndertimi i instaluesit ===" -ForegroundColor Cyan
Write-Host ""

# --------------------------------------------------------------------------
# 1. Mbyllja e proceseve qe bllokojne skedaret
# --------------------------------------------------------------------------
Write-Host "[1/6] Mbyllja e proceseve..." -ForegroundColor Yellow
$procs = @("DataPOS", "electron", "app-builder", "nsis", "makensis", "7z")
foreach ($p in $procs) {
    Get-Process -Name $p -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "      mbyllet: $($_.ProcessName) (PID $($_.Id))"
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep -Seconds 2

# --------------------------------------------------------------------------
# 2. Mbyllja e dritareve te Explorer-it ne dosjet e daljes
# --------------------------------------------------------------------------
Write-Host "[2/6] Kontrolli i dritareve te Explorer-it..." -ForegroundColor Yellow
try {
    $shell = New-Object -ComObject Shell.Application
    $shell.Windows() | Where-Object {
        $_.LocationURL -match "dist|release|win-unpacked"
    } | ForEach-Object {
        Write-Host "      mbyllet dritarja: $($_.LocationName)"
        $_.Quit()
    }
} catch {
    Write-Host "      (nuk u kontrollua - vazhdojme)"
}

# --------------------------------------------------------------------------
# 3. Dosja e daljes - gjithmone e re, pa konflikt
# --------------------------------------------------------------------------
$stamp  = Get-Date -Format "yyyyMMdd-HHmm"
$outDir = "release-$stamp"
Write-Host "[3/6] Dosja e daljes: $outDir" -ForegroundColor Yellow

# Fshi dosjet e vjetra nese jane te lira (nese jo, thjeshte vazhdo)
foreach ($old in @("dist", "release")) {
    if (Test-Path $old) {
        try {
            Remove-Item $old -Recurse -Force -ErrorAction Stop
            Write-Host "      u fshi dosja e vjeter: $old"
        } catch {
            Write-Host "      dosja '$old' e bllokuar - anashkalohet" -ForegroundColor DarkYellow
        }
    }
}

# --------------------------------------------------------------------------
# 4. Varesite
# --------------------------------------------------------------------------
Write-Host "[4/6] Instalimi i varesive..." -ForegroundColor Yellow
if (-not (Test-Path "node_modules")) {
    yarn install
} else {
    Write-Host "      node_modules ekziston - anashkalohet"
}

# --------------------------------------------------------------------------
# 5. Ndertimi i React-it
# --------------------------------------------------------------------------
Write-Host "[5/6] Ndertimi i aplikacionit React..." -ForegroundColor Yellow
yarn build
if ($LASTEXITCODE -ne 0) {
    Write-Host "GABIM: ndertimi i React-it deshtoi." -ForegroundColor Red
    exit 1
}

# --------------------------------------------------------------------------
# 6. Ndertimi i instaluesit NSIS
# --------------------------------------------------------------------------
Write-Host "[6/6] Ndertimi i setup.exe..." -ForegroundColor Yellow
npx electron-builder --win nsis --x64 -c.directories.output=$outDir

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Ndertimi deshtoi. Provo keto hapa:" -ForegroundColor Red
    Write-Host "  1. Rinis kompjuterin (liron skedaret e bllokuar)"
    Write-Host "  2. Shto perjashtim ne Windows Defender per dosjen e projektit:"
    Write-Host "     Add-MpPreference -ExclusionPath '$PSScriptRoot'" -ForegroundColor Gray
    Write-Host "  3. Ekzekuto perseri: .\build-setup.ps1"
    exit 1
}

# --------------------------------------------------------------------------
# Rezultati
# --------------------------------------------------------------------------
Write-Host ""
$setup = Get-ChildItem -Path $outDir -Filter "*Setup*.exe" -ErrorAction SilentlyContinue |
         Select-Object -First 1
if ($setup) {
    $mb = [math]::Round($setup.Length / 1MB, 1)
    Write-Host "=== GATI ===" -ForegroundColor Green
    Write-Host "Instaluesi: $($setup.FullName)" -ForegroundColor Green
    Write-Host "Madhesia:   $mb MB" -ForegroundColor Green
    Write-Host ""
    Write-Host "Kopjoje ne cdo PC dhe ekzekutoje per instalim."
} else {
    Write-Host "Ndertimi perfundoi, por setup.exe nuk u gjet ne '$outDir'." -ForegroundColor Yellow
}
