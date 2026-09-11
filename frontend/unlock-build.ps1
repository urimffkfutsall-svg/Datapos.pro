<#
===========================================================================
 DataPOS - Lirimi i skedareve te bllokuar PA RINISJE
---------------------------------------------------------------------------
 Zgjidh gabimin:
   "remove ...\resources\app.asar: The process cannot access the file
    because it is being used by another process"

 Si punon:
  1. Perdor Windows Restart Manager (RstrtMgr.dll) - i njejti mekanizem qe
     perdor Windows Update - per te zbuluar SAKTESISHT cilat procese mbajne
     te hapur app.asar dhe skedaret e tjere.
  2. Mbyll vetem ato procese (jo me hamendje).
  3. Rinis Windows Explorer, i cili shpesh mban handle mbi dosjet e daljes.
  4. Fshin dosjet dist/release me metoda te shumefishta.

 Perdorimi:
   powershell -ExecutionPolicy Bypass -File .\unlock-build.ps1
===========================================================================
#>

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "=== Lirimi i skedareve te bllokuar (pa rinisje) ===" -ForegroundColor Cyan
Write-Host ""

# --------------------------------------------------------------------------
# Restart Manager - zbulon proceset qe mbajne skedarin
# --------------------------------------------------------------------------
$rmCode = @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

public static class FileLocker
{
    [StructLayout(LayoutKind.Sequential)]
    struct RM_UNIQUE_PROCESS
    {
        public int dwProcessId;
        public System.Runtime.InteropServices.ComTypes.FILETIME ProcessStartTime;
    }

    const int RmRebootReasonNone = 0;
    const int CCH_RM_MAX_APP_NAME = 255;
    const int CCH_RM_MAX_SVC_NAME = 63;

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    struct RM_PROCESS_INFO
    {
        public RM_UNIQUE_PROCESS Process;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = CCH_RM_MAX_APP_NAME + 1)]
        public string strAppName;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = CCH_RM_MAX_SVC_NAME + 1)]
        public string strServiceShortName;
        public int ApplicationType;
        public uint AppStatus;
        public uint TSSessionId;
        [MarshalAs(UnmanagedType.Bool)]
        public bool bRestartable;
    }

    [DllImport("rstrtmgr.dll", CharSet = CharSet.Unicode)]
    static extern int RmRegisterResources(uint pSessionHandle, uint nFiles,
        string[] rgsFilenames, uint nApplications, [In] RM_UNIQUE_PROCESS[] rgApplications,
        uint nServices, string[] rgsServiceNames);

    [DllImport("rstrtmgr.dll", CharSet = CharSet.Auto)]
    static extern int RmStartSession(out uint pSessionHandle, int dwSessionFlags, string strSessionKey);

    [DllImport("rstrtmgr.dll")]
    static extern int RmEndSession(uint pSessionHandle);

    [DllImport("rstrtmgr.dll")]
    static extern int RmGetList(uint dwSessionHandle, out uint pnProcInfoNeeded,
        ref uint pnProcInfo, [In, Out] RM_PROCESS_INFO[] rgAffectedApps, ref uint lpdwRebootReasons);

    public static List<int> WhoIsLocking(string path)
    {
        uint handle;
        string key = Guid.NewGuid().ToString();
        List<int> pids = new List<int>();

        int res = RmStartSession(out handle, 0, key);
        if (res != 0) return pids;

        try
        {
            uint pnProcInfoNeeded = 0, pnProcInfo = 0, lpdwRebootReasons = RmRebootReasonNone;
            string[] resources = new string[] { path };
            res = RmRegisterResources(handle, (uint)resources.Length, resources, 0, null, 0, null);
            if (res != 0) return pids;

            res = RmGetList(handle, out pnProcInfoNeeded, ref pnProcInfo, null, ref lpdwRebootReasons);
            if (res == 234)
            {
                RM_PROCESS_INFO[] processInfo = new RM_PROCESS_INFO[pnProcInfoNeeded];
                pnProcInfo = pnProcInfoNeeded;
                res = RmGetList(handle, out pnProcInfoNeeded, ref pnProcInfo, processInfo, ref lpdwRebootReasons);
                if (res == 0)
                {
                    for (int i = 0; i < pnProcInfo; i++)
                        pids.Add(processInfo[i].Process.dwProcessId);
                }
            }
        }
        finally
        {
            RmEndSession(handle);
        }
        return pids;
    }
}
'@

try {
    Add-Type -TypeDefinition $rmCode -Language CSharp -ErrorAction Stop
    $rmReady = $true
} catch {
    Write-Host "Restart Manager nuk u ngarkua - kalojme ne metoden e dyte." -ForegroundColor DarkYellow
    $rmReady = $false
}

# --------------------------------------------------------------------------
# 1. Mbyll proceset qe mbajne skedaret e ndertimit
# --------------------------------------------------------------------------
Write-Host "[1/5] Zbulimi i proceseve qe bllokojne skedaret..." -ForegroundColor Yellow

$targets = @()
foreach ($dir in @("dist", "release")) {
    if (Test-Path $dir) {
        $targets += Get-ChildItem -Path $dir -Recurse -File -ErrorAction SilentlyContinue |
                    Where-Object { $_.Name -match "app\.asar|\.exe$|\.dll$|\.node$|\.pak$" } |
                    Select-Object -ExpandProperty FullName
    }
}
$targets += Get-ChildItem -Path . -Filter "release-*" -Directory -ErrorAction SilentlyContinue |
            ForEach-Object { Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match "app\.asar|\.exe$" } | Select-Object -ExpandProperty FullName }

$lockPids = @()
if ($rmReady -and $targets.Count -gt 0) {
    foreach ($file in ($targets | Select-Object -First 60)) {
        try { $lockPids += [FileLocker]::WhoIsLocking($file) } catch { }
    }
    $lockPids = $lockPids | Sort-Object -Unique | Where-Object { $_ -ne $PID }
}

if ($lockPids.Count -gt 0) {
    foreach ($procId in $lockPids) {
        $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
        if ($p) {
            Write-Host "      bllokuar nga: $($p.ProcessName) (PID $procId) -> mbyllet" -ForegroundColor Magenta
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
} else {
    Write-Host "      nuk u zbulua bllokues i drejtperdrejte"
}

# Mbyll gjithashtu proceset e njohura te ndertimit
Write-Host "[2/5] Mbyllja e proceseve te ndertimit..." -ForegroundColor Yellow
foreach ($name in @("DataPOS", "electron", "app-builder", "makensis", "nsis", "7z", "node")) {
    Get-Process -Name $name -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.Id -ne $PID) {
            Write-Host "      mbyllet: $($_.ProcessName) (PID $($_.Id))"
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
    }
}
Start-Sleep -Seconds 2

# --------------------------------------------------------------------------
# 3. Rinis Windows Explorer - liron handle-t mbi dosjet
# --------------------------------------------------------------------------
Write-Host "[3/5] Rinisja e Windows Explorer..." -ForegroundColor Yellow
try {
    $shell = New-Object -ComObject Shell.Application
    $shell.Windows() | Where-Object { $_.LocationURL -match "dist|release|win-unpacked|Datapos" } |
        ForEach-Object { $_.Quit() }
} catch { }

Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3
if (-not (Get-Process -Name explorer -ErrorAction SilentlyContinue)) {
    Start-Process explorer
    Start-Sleep -Seconds 2
}
Write-Host "      Explorer u rinis (dritaret e hapura u mbyllen)"

# --------------------------------------------------------------------------
# 4. Perjashtimi ne Defender (nese kemi te drejta administratori)
# --------------------------------------------------------------------------
Write-Host "[4/5] Perjashtimi ne Windows Defender..." -ForegroundColor Yellow
$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(`
    [Security.Principal.WindowsBuiltInRole]::Administrator)

if ($isAdmin) {
    try {
        Add-MpPreference -ExclusionPath $PSScriptRoot -ErrorAction Stop
        Write-Host "      u shtua perjashtimi: $PSScriptRoot" -ForegroundColor Green
    } catch {
        Write-Host "      nuk u shtua (Defender jo aktiv ose i menaxhuar)"
    }
} else {
    Write-Host "      pa te drejta admin - anashkalohet" -ForegroundColor DarkYellow
    Write-Host "      (opsionale: hap PowerShell si Administrator dhe ekzekuto perseri)"
}

# --------------------------------------------------------------------------
# 5. Fshirja e dosjeve te daljes
# --------------------------------------------------------------------------
Write-Host "[5/5] Fshirja e dosjeve te daljes..." -ForegroundColor Yellow

function Remove-Stubborn($dir) {
    if (-not (Test-Path $dir)) { return $true }

    # Provo fshirjen normale
    try {
        Remove-Item $dir -Recurse -Force -ErrorAction Stop
        Write-Host "      u fshi: $dir" -ForegroundColor Green
        return $true
    } catch { }

    # Provo me cmd (trajton rruge te gjata me mire)
    cmd /c "rmdir /s /q `"$dir`"" 2>$null
    if (-not (Test-Path $dir)) {
        Write-Host "      u fshi me cmd: $dir" -ForegroundColor Green
        return $true
    }

    # Provo riemertimin - shpesh punon kur fshirja nuk punon
    try {
        $bak = "$dir-locked-$(Get-Random)"
        Rename-Item $dir $bak -ErrorAction Stop
        Write-Host "      u riemertua ne: $bak (fshije me vone)" -ForegroundColor DarkYellow
        return $true
    } catch { }

    Write-Host "      NUK u fshi: $dir" -ForegroundColor Red
    return $false
}

$allClear = $true
foreach ($d in @("dist", "release")) {
    if (-not (Remove-Stubborn $d)) { $allClear = $false }
}

Write-Host ""
if ($allClear) {
    Write-Host "=== GATI - skedaret u liruan ===" -ForegroundColor Green
    Write-Host "Vazhdo me ndertimin:" -ForegroundColor Green
    Write-Host "   .\build-setup.ps1" -ForegroundColor White
} else {
    Write-Host "Dosjet mbeten te bllokuara, por ndertimi mund te vazhdoje:" -ForegroundColor Yellow
    Write-Host "build-setup.ps1 ndertohet ne dosje te re me stamp kohor," -ForegroundColor Yellow
    Write-Host "prandaj dosja e vjeter e bllokuar nuk e ndalon me." -ForegroundColor Yellow
    Write-Host "   .\build-setup.ps1" -ForegroundColor White
}
Write-Host ""
