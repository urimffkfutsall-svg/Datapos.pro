<#
===========================================================================
 DataPOS - Ndertimi i setup.exe (PowerShell)
---------------------------------------------------------------------------
 Perdorimi:
   powershell -ExecutionPolicy Bypass -File .\build-setup.ps1

 RREGULLIM I RENDESISHEM:
   PowerShell-i e ndan argumentin "-c.directories.output=X" dhe
   electron-builder-i mendon se ".directories.output=X" eshte skedar
   konfigurimi -> gabimi ENOENT.
   Prandaj tani komanda ekzekutohet PERMES cmd.exe, i cili i dergon
   argumentet ashtu si duhet.
===========================================================================
#>

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "=== DataPOS - ndertimi i instaluesit ===" -ForegroundColor Cyan
Write-Host ""

# --------------------------------------------------------------------------
# 0. Lirimi i skedareve te bllokuar (pa rinisje)
# --------------------------------------------------------------------------
if (Test-Path "$PSScriptRoot\unlock-build.ps1") {
    Write-Host "[0/4] Lirimi i skedareve te bllokuar..." -ForegroundColor Yellow
    & powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\unlock-build.ps1"
}

# --------------------------------------------------------------------------
# 1. Varesite
# --------------------------------------------------------------------------
Write-Host ""
Write-Host "[1/4] Kontrolli i varesive..." -ForegroundColor Yellow
if (-not (Test-Path "node_modules")) {
    cmd /c "yarn install"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "GABIM: yarn install deshtoi." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "      node_modules ekziston - anashkalohet"
}

# --------------------------------------------------------------------------
# 2. Ndertimi i React-it
# --------------------------------------------------------------------------
Write-Host ""
Write-Host "[2/4] Ndertimi i aplikacionit React..." -ForegroundColor Yellow
if (Test-Path "build\index.html") {
    Remove-Item "build" -Recurse -Force -ErrorAction SilentlyContinue
}
cmd /c "yarn build"
if (-not (Test-Path "build\index.html")) {
    Write-Host "GABIM: dosja 'build' nuk u krijua." -ForegroundColor Red
    exit 1
}
Write-Host "      build/index.html u krijua" -ForegroundColor Green

# --------------------------------------------------------------------------
# 3. Ndertimi i instaluesit NSIS
# --------------------------------------------------------------------------
Write-Host ""
Write-Host "[3/4] Ndertimi i setup.exe..." -ForegroundColor Yellow

# Prova 1: dosja standarde 'release' (e caktuar ne package.json)
cmd /c "npx electron-builder --win nsis --x64"
$buildOk = ($LASTEXITCODE -eq 0)
$outDir  = "release"

# Prova 2: nese 'release' ishte e bllokuar, perdor dosje me stamp kohor.
# Argumenti kalon permes cmd.exe - keshtu shmanget gabimi ENOENT.
if (-not $buildOk) {
    $stamp  = Get-Date -Format "yyyyMMdd-HHmm"
    $outDir = "release-$stamp"
    Write-Host ""
    Write-Host "      Prova e dyte ne dosjen: $outDir" -ForegroundColor DarkYellow
    cmd /c "npx electron-builder --win nsis --x64 -c.directories.output=$outDir"
    $buildOk = ($LASTEXITCODE -eq 0)
}

if (-not $buildOk) {
    Write-Host ""
    Write-Host "Ndertimi deshtoi. Provo keto hapa:" -ForegroundColor Red
    Write-Host "  1. Hap PowerShell si Administrator dhe ekzekuto: .\unlock-build.ps1"
    Write-Host "  2. Shto perjashtim ne Windows Defender:"
    Write-Host "     Add-MpPreference -ExclusionPath '$PSScriptRoot'" -ForegroundColor Gray
    Write-Host "  3. Ekzekuto perseri: .\build-setup.ps1"
    exit 1
}

# --------------------------------------------------------------------------
# 4. Rezultati
# --------------------------------------------------------------------------
Write-Host ""
Write-Host "[4/4] Kontrolli i instaluesit..." -ForegroundColor Yellow

$setup = Get-ChildItem -Path . -Filter "*Setup*.exe" -Recurse -ErrorAction SilentlyContinue |
         Where-Object { $_.FullName -match "release" } |
         Sort-Object LastWriteTime -Descending | Select-Object -First 1

Write-Host ""
if ($setup) {
    $mb = [math]::Round($setup.Length / 1MB, 1)
    Write-Host "=== GATI ===" -ForegroundColor Green
    Write-Host "Instaluesi: $($setup.FullName)" -ForegroundColor Green
    Write-Host "Madhesia:   $mb MB" -ForegroundColor Green
    Write-Host ""
    Write-Host "Kopjoje ne cdo PC dhe ekzekutoje per instalim."
} else {
    Write-Host "Ndertimi perfundoi, por setup.exe nuk u gjet." -ForegroundColor Yellow
    Write-Host "Kontrollo dosjen: $outDir" -ForegroundColor Yellow
}
Write-Host ""
