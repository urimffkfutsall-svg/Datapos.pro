cd C:\Users\urim5\Desktop\datapos12-main\frontend

Copy-Item tailwind.config.js tailwind.config.js.backup -Force
Copy-Item src\index.css src\index.css.backup -Force

$tailwindConfig = @'
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
        '4xl': '2rem',
        '5xl': '2.5rem'
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Manrope', 'system-ui', 'sans-serif']
      },
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: { DEFAULT: 'hsl(var(--card))', foreground: 'hsl(var(--card-foreground))' },
        popover: { DEFAULT: 'hsl(var(--popover))', foreground: 'hsl(var(--popover-foreground))' },
        primary: { DEFAULT: 'hsl(var(--primary))', foreground: 'hsl(var(--primary-foreground))' },
        secondary: { DEFAULT: 'hsl(var(--secondary))', foreground: 'hsl(var(--secondary-foreground))' },
        muted: { DEFAULT: 'hsl(var(--muted))', foreground: 'hsl(var(--muted-foreground))' },
        accent: { DEFAULT: 'hsl(var(--accent))', foreground: 'hsl(var(--accent-foreground))' },
        destructive: { DEFAULT: 'hsl(var(--destructive))', foreground: 'hsl(var(--destructive-foreground))' },
        border: 'hsl(var(--border))',
        ring: 'hsl(var(--ring))',
        chart: {
          '2': 'hsl(var(--chart-2))',
          '3': 'hsl(var(--chart-3))',
          '4': 'hsl(var(--chart-4))',
          '5': 'hsl(var(--chart-5))'
        },
        brand: {
          50:  '#e6f7f6',
          100: '#c2ebe8',
          200: '#8dd9d4',
          300: '#5cc7c0',
          400: '#33b5ac',
          500: '#00a79d',
          600: '#008f86',
          700: '#007a73',
          800: '#005f59',
          900: '#003e3a'
        }
      },
      boxShadow: {
        'soft':       '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.02)',
        'soft-md':    '0 4px 16px -2px rgba(0,0,0,0.05), 0 2px 6px -2px rgba(0,0,0,0.04)',
        'soft-lg':    '0 12px 32px -8px rgba(0,0,0,0.08), 0 4px 12px -4px rgba(0,0,0,0.05)',
        'soft-xl':    '0 24px 48px -12px rgba(0,0,0,0.12), 0 8px 16px -8px rgba(0,0,0,0.06)',
        'glow':       '0 0 0 1px rgba(0,167,157,0.15), 0 8px 24px -8px rgba(0,167,157,0.3)',
        'glow-lg':    '0 0 0 1px rgba(0,167,157,0.2), 0 16px 40px -12px rgba(0,167,157,0.35)',
        'inner-soft': 'inset 0 1px 2px rgba(0,0,0,0.04)'
      },
      keyframes: {
        'accordion-down': { from: { height: '0' }, to: { height: 'var(--radix-accordion-content-height)' } },
        'accordion-up':   { from: { height: 'var(--radix-accordion-content-height)' }, to: { height: '0' } },
        'fade-in':        { from: { opacity: '0', transform: 'translateY(8px)' },  to: { opacity: '1', transform: 'translateY(0)' } },
        'fade-in-up':     { from: { opacity: '0', transform: 'translateY(16px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        'scale-in':       { from: { opacity: '0', transform: 'scale(0.96)' },      to: { opacity: '1', transform: 'scale(1)' } },
        'shimmer':        { '0%': { backgroundPosition: '-1000px 0' }, '100%': { backgroundPosition: '1000px 0' } },
        'pulse-soft':     { '0%, 100%': { opacity: '1' }, '50%': { opacity: '0.6' } }
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up':   'accordion-up 0.2s ease-out',
        'fade-in':        'fade-in 0.4s ease-out',
        'fade-in-up':     'fade-in-up 0.5s ease-out',
        'scale-in':       'scale-in 0.3s ease-out',
        'shimmer':        'shimmer 2s linear infinite',
        'pulse-soft':     'pulse-soft 2s ease-in-out infinite'
      },
      backdropBlur: { 'xs': '2px' }
    }
  },
  plugins: [require("tailwindcss-animate")]
};
'@

[System.IO.File]::WriteAllText("$PWD\tailwind.config.js", $tailwindConfig, (New-Object System.Text.UTF8Encoding $false))
Write-Host "OK 1/2: tailwind.config.js u rishkrua" -ForegroundColor Green

$cssAdditions = @'
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
box-shadow:
0 0 0 1px rgba(0, 167, 157, 0.08),
0 8px 24px -8px rgba(0, 167, 157, 0.15);
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
$existingCss = [System.IO.File]::ReadAllText("$PWDsrcindex.css")
$combinedCss = $existingCss + $cssAdditions
[System.IO.File]::WriteAllText("$PWDsrcindex.css", $combinedCss, (New-Object System.Text.UTF8Encoding $false))
Write-Host "OK 2/2: srcindex.css u zgjerua" -ForegroundColor Green
Write-Host ""
Write-Host "Verifikim:" -ForegroundColor Cyan
if (Select-String -Path tailwind.config.js -Pattern "brand:" -SimpleMatch -Quiet) { Write-Host "  tailwind brand palette: OK" -ForegroundColor Green } else { Write-Host "  tailwind brand palette: MUNGON" -ForegroundColor Red }
if (Select-String -Path srcindex.css -Pattern "MODERN DESIGN SYSTEM v2" -SimpleMatch -Quiet) { Write-Host "  index.css modern system: OK" -ForegroundColor Green } else { Write-Host "  index.css modern system: MUNGON" -ForegroundColor Red }
Write-Host ""
Write-Host "Faza 1 perfundoi! Tani me dergo MainLayout.jsx:" -ForegroundColor Yellow
Write-Host "  cat srccomponentsMainLayout.jsx" -ForegroundColor White