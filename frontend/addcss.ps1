$realCss  = "C:/Users/urim5/Desktop/datapos12-main/frontend/src/index.css"
$bogusOne = "C:/Users/urim5/Desktop/datapos12-main/.css"
$bogusTwo = "C:/Users/urim5/Desktop/datapos12-main/frontendsrcindex.css"
$bogusTri = "C:/Users/urim5/Desktop/datapos12-main/frontend/srcindex.css"
$utf8     = New-Object System.Text.UTF8Encoding $false

foreach ($b in @($bogusOne, $bogusTwo, $bogusTri)) {
  if (Test-Path $b) { Remove-Item $b -Force; Write-Host "Fshira: $b" -ForegroundColor Yellow }
}

if (-not (Test-Path $realCss)) { Write-Host "FATAL: src/index.css mungon" -ForegroundColor Red; exit }

$existing = [System.IO.File]::ReadAllText($realCss)
if ($existing -match "MODERN DESIGN SYSTEM v2") { Write-Host "Tashme i modernizuar" -ForegroundColor Yellow; exit }

$add = @'
​
/* ============================================
MODERN DESIGN SYSTEM v2 - AI Professional
============================================ */
:root { --radius: 0.875rem; }
.glass {
background: rgba(255, 255, 255, 0.65);
backdrop-filter: blur(20px) saturate(180%);
-webkit-backdrop-filter: blur(20px) saturate(180%);
border: 1px solid rgba(255, 255, 255, 0.5);
}
.glass-strong {
background: rgba(255, 255, 255, 0.85);
backdrop-filter: blur(24px) saturate(180%);
-webkit-backdrop-filter: blur(24px) saturate(180%);
border: 1px solid rgba(255, 255, 255, 0.6);
}
.glass-dark {
background: rgba(15, 23, 42, 0.6);
backdrop-filter: blur(20px) saturate(180%);
-webkit-backdrop-filter: blur(20px) saturate(180%);
}
.bg-mesh {
background-color: #fafbfc;
background-image:
radial-gradient(at 12% 18%, hsla(175, 100%, 75%, 0.16) 0px, transparent 50%),
radial-gradient(at 85% 12%, hsla(190, 100%, 70%, 0.12) 0px, transparent 50%),
radial-gradient(at 72% 88%, hsla(175, 100%, 70%, 0.10) 0px, transparent 50%);
}
.bg-mesh-subtle {
background-color: #fafafa;
background-image:
radial-gradient(at 20% 30%, hsla(175, 60%, 85%, 0.20) 0px, transparent 50%),
radial-gradient(at 80% 70%, hsla(220, 50%, 90%, 0.18) 0px, transparent 50%);
}
.bg-grid {
background-image:
linear-gradient(rgba(0,0,0,0.04) 1px, transparent 1px),
linear-gradient(90deg, rgba(0,0,0,0.04) 1px, transparent 1px);
background-size: 24px 24px;
}
.card-modern {
background: white;
border-radius: 1rem;
border: 1px solid rgba(0,0,0,0.05);
box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.02);
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.card-modern:hover {
box-shadow: 0 12px 24px -8px rgba(0, 167, 157, 0.12), 0 4px 8px -2px rgba(0,0,0,0.04);
transform: translateY(-2px);
border-color: rgba(0, 167, 157, 0.2);
}
.card-glow {
background: white;
border-radius: 1.25rem;
box-shadow: 0 0 0 1px rgba(0, 167, 157, 0.08), 0 8px 24px -8px rgba(0, 167, 157, 0.15);
}
.input-modern {
width: 100%;
padding: 0.625rem 1rem;
border-radius: 0.75rem;
background: #f8fafc;
border: 1px solid #e2e8f0;
font-size: 0.875rem;
transition: all 0.2s;
outline: none;
}
.input-modern:focus {
background: white;
border-color: #00a79d;
box-shadow: 0 0 0 4px rgba(0, 167, 157, 0.1);
}
.btn-primary-modern {
display: inline-flex;
align-items: center;
justify-content: center;
gap: 0.5rem;
padding: 0.625rem 1.25rem;
border-radius: 0.75rem;
font-weight: 500;
color: white;
background: linear-gradient(135deg, #00a79d 0%, #008f86 100%);
box-shadow: 0 4px 12px -2px rgba(0, 167, 157, 0.35), inset 0 1px 0 rgba(255,255,255,0.15);
transition: all 0.2s;
cursor: pointer;
border: none;
}
.btn-primary-modern:hover {
background: linear-gradient(135deg, #008f86 0%, #007a73 100%);
box-shadow: 0 6px 18px -2px rgba(0, 167, 157, 0.45), inset 0 1px 0 rgba(255,255,255,0.15);
transform: translateY(-1px);
}
.btn-primary-modern:active { transform: translateY(0); }
.btn-primary-modern:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
.text-gradient-teal {
background: linear-gradient(135deg, #00a79d 0%, #007a73 100%);
-webkit-background-clip: text;
background-clip: text;
-webkit-text-fill-color: transparent;
}
.text-gradient-ai {
background: linear-gradient(135deg, #00a79d 0%, #2563eb 50%, #7c3aed 100%);
-webkit-background-clip: text;
background-clip: text;
-webkit-text-fill-color: transparent;
}
.metric-value {
font-family: 'Manrope', sans-serif;
font-size: 1.875rem;
font-weight: 700;
letter-spacing: -0.02em;
font-variant-numeric: tabular-nums;
line-height: 1.1;
}
.badge-modern {
display: inline-flex;
align-items: center;
gap: 0.375rem;
padding: 0.125rem 0.625rem;
border-radius: 9999px;
font-size: 0.75rem;
font-weight: 500;
border: 1px solid;
}
.badge-success { background:#ecfdf5; color:#047857; border-color:#a7f3d0; }
.badge-warning { background:#fffbeb; color:#b45309; border-color:#fde68a; }
.badge-danger  { background:#fef2f2; color:#b91c1c; border-color:#fecaca; }
.badge-info    { background:#eff6ff; color:#1d4ed8; border-color:#bfdbfe; }
.badge-teal    { background:#e6f7f6; color:#007a73; border-color:#8dd9d4; }
.badge-purple  { background:#faf5ff; color:#6b21a8; border-color:#e9d5ff; }
.nav-item {
display: flex;
align-items: center;
gap: 0.75rem;
padding: 0.625rem 0.875rem;
border-radius: 0.75rem;
font-size: 0.875rem;
font-weight: 500;
color: #475569;
transition: all 0.2s;
position: relative;
}
.nav-item:hover { background: rgba(0, 167, 157, 0.06); color: #00a79d; }
.nav-item.active {
background: linear-gradient(90deg, rgba(0, 167, 157, 0.12), rgba(0, 167, 157, 0.04));
color: #00a79d;
font-weight: 600;
}
.nav-item.active::before {
content: '';
position: absolute;
left: 0;
top: 25%;
bottom: 25%;
width: 3px;
border-radius: 0 3px 3px 0;
background: linear-gradient(180deg, #00a79d, #007a73);
}
.stagger > * { animation: fadeInUp 0.45s ease-out backwards; }
.stagger > *:nth-child(1) { animation-delay: 0.04s; }
.stagger > *:nth-child(2) { animation-delay: 0.08s; }
.stagger > *:nth-child(3) { animation-delay: 0.12s; }
.stagger > *:nth-child(4) { animation-delay: 0.16s; }
.stagger > *:nth-child(5) { animation-delay: 0.20s; }
.stagger > *:nth-child(6) { animation-delay: 0.24s; }
.stagger > *:nth-child(7) { animation-delay: 0.28s; }
.stagger > *:nth-child(8) { animation-delay: 0.32s; }
@keyframes fadeInUp {
from { opacity: 0; transform: translateY(12px); }
to   { opacity: 1; transform: translateY(0); }
}
.skeleton-shimmer {
background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
background-size: 1000px 100%;
animation: shimmer 2s linear infinite;
}
@keyframes shimmer {
0%   { background-position: -1000px 0; }
100% { background-position: 1000px 0; }
}
.hover-lift { transition: transform 0.25s, box-shadow 0.25s; }
.hover-lift:hover {
transform: translateY(-2px);
box-shadow: 0 12px 24px -8px rgba(0,0,0,0.1);
}
.spinner-modern {
width: 20px;
height: 20px;
border-radius: 50%;
border: 2px solid rgba(0, 167, 157, 0.2);
border-top-color: #00a79d;
animation: spin 0.7s linear infinite;
}
@keyframes sparklePulse {
0%, 100% { transform: scale(1) rotate(0deg); opacity: 1; }
50%      { transform: scale(1.1) rotate(180deg); opacity: 0.8; }
}
.sparkle-animate { animation: sparklePulse 3s ease-in-out infinite; }
::-webkit-scrollbar-thumb { background: rgba(0, 167, 157, 0.25); border-radius: 8px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0, 167, 157, 0.5); }
[role="dialog"] > div[role="document"],
[data-radix-popper-content-wrapper] [role="dialog"] {
border-radius: 1.25rem !important;
}
.page-content { animation: pageEnter 0.4s ease-out; }
@keyframes pageEnter {
from { opacity: 0; transform: translateY(8px); }
to   { opacity: 1; transform: translateY(0); }
}
.section-heading {
display: flex;
align-items: center;
gap: 0.625rem;
font-family: 'Manrope', sans-serif;
font-weight: 700;
letter-spacing: -0.01em;
}
.section-heading-icon {
width: 2rem;
height: 2rem;
border-radius: 0.625rem;
display: flex;
align-items: center;
justify-content: center;
background: rgba(0, 167, 157, 0.1);
color: #00a79d;
}
.divider-text {
display: flex;
align-items: center;
gap: 0.75rem;
font-size: 0.75rem;
font-weight: 500;
color: #94a3b8;
text-transform: uppercase;
letter-spacing: 0.05em;
}
.divider-text::before, .divider-text::after {
content: '';
flex: 1;
height: 1px;
background: #e2e8f0;
}
kbd, .kbd {
display: inline-flex;
align-items: center;
padding: 0.125rem 0.375rem;
border-radius: 0.375rem;
background: #f1f5f9;
border: 1px solid #e2e8f0;
border-bottom-width: 2px;
font-family: 'Inter', monospace;
font-size: 0.75rem;
font-weight: 500;
color: #475569;
}
'@
[System.IO.File]::WriteAllText($realCss, $existing + $add, $utf8)
Write-Host "OK: u shtua sistemi modern te src/index.css" -ForegroundColor Green
$check = Select-String -Path $realCss -Pattern "MODERN DESIGN SYSTEM v2" -SimpleMatch -Quiet
if ($check) { Write-Host "Verifikim: OK" -ForegroundColor Green } else { Write-Host "Verifikim: DESHTOI" -ForegroundColor Red }