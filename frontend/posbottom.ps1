$path = 'src\pages\POS.jsx'
$abs = (Resolve-Path $path).Path
Copy-Item $abs "$abs.bakbottom" -Force

$enc = New-Object System.Text.UTF8Encoding $false
$t = [System.IO.File]::ReadAllText($abs, [System.Text.Encoding]::UTF8)

$old = 'className="border-t border-[#00a79d]/15 bg-gradient-to-r from-[#00a79d] to-[#007a73] p-4"'
$new = 'className="mt-auto border-t border-[#00a79d]/15 bg-gradient-to-r from-[#00a79d] to-[#007a73] p-4"'
$cnt = ([regex]::Matches($t, [regex]::Escape($old))).Count
Write-Host ("Replacements: {0}" -f $cnt)
$t = $t.Replace($old, $new)
[System.IO.File]::WriteAllText($abs, $t, $enc)
Write-Host "OK: totali u shty ne fund" -ForegroundColor Green