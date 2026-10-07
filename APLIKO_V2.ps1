param(
    [string]$RepoPath = "C:\Users\urim5\Desktop\Datapos.pro-fixed\Datapos.pro"
)
$ErrorActionPreference = "Stop"
$patch = Join-Path $PSScriptRoot "datapos-panel-v2.patch"
if (!(Test-Path $patch)) { throw "Patch-i V2 nuk u gjet pranë këtij skripti." }
if (!(Test-Path (Join-Path $RepoPath '.git'))) { throw "Repository nuk u gjet. Përdorni parametrin -RepoPath me rrugën e saktë." }
Set-Location $RepoPath
$changes = git status --porcelain
if ($LASTEXITCODE -ne 0) { throw "Git status dështoi." }
if ($changes) { throw "Repository ka ndryshime lokale. Ruajini para aplikimit; asgjë nuk u ndryshua." }
git apply --check $patch
if ($LASTEXITCODE -ne 0) { throw "Patch-i nuk përputhet. Ndalo këtu; mos përdor force." }
git apply $patch
if ($LASTEXITCODE -ne 0) { throw "Aplikimi i patch-it dështoi." }
git add .
if ($LASTEXITCODE -ne 0) { throw "Git add dështoi." }
git commit -m "Redesign sales-only dashboard, verified resets and print-only reports"
if ($LASTEXITCODE -ne 0) { throw "Commit-i nuk u krye." }
git push origin main
if ($LASTEXITCODE -ne 0) { throw "Push-i dështoi. Commit-i është ruajtur lokalisht; kontrolloni autentikimin ose lidhjen." }
Write-Host "Push-i u krye. Publikoni edhe backend-in e këtij versioni, jo vetëm frontend-in në Vercel." -ForegroundColor Green
