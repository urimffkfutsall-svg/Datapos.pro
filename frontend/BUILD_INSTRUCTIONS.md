# 📦 Udhëzues për Ndërtimin e DataPOS Desktop

## Kërkesat Paraprake

### Për Windows:
- Node.js 18+ (https://nodejs.org)
- Yarn (npm install -g yarn)
- Git (https://git-scm.com)

### Për Mac:
- Node.js 18+ (https://nodejs.org)
- Yarn (npm install -g yarn)
- Xcode Command Line Tools (`xcode-select --install`)

### Për Linux:
- Node.js 18+
- Yarn
- Build tools: `sudo apt-get install build-essential`

---

## 🔧 Hapat për Ndërtimin

### 1. Shkarkoni Kodin

```bash
# Shkarkoni kodin nga Github (pas Save to Github)
git clone https://github.com/[your-username]/datapos.git
cd datapos/frontend
```

### 2. Instaloni Varësitë

```bash
yarn install
```

### 3. Ndërtoni Aplikacionin

#### Për Windows (setup.exe):
```bash
yarn electron:build:win
```
Rezultati: `frontend/dist/DataPOS Setup 1.0.0.exe`

#### Për Mac (.dmg):
```bash
yarn electron:build:mac
```
Rezultati: `frontend/dist/DataPOS-1.0.0.dmg` dhe `DataPOS-1.0.0-arm64.dmg`

#### Për Linux (.AppImage):
```bash
yarn electron:build:linux
```
Rezultati: `frontend/dist/DataPOS-1.0.0.AppImage`

#### Për të gjitha platformat:
```bash
yarn electron:build:all
```

---

## 📁 Skedarët e Gjeneruar

Pas ndërtimit, skedarët do të jenë në folder-in `frontend/dist/`:

| Platforma | Skedari | Përshkrimi |
|-----------|---------|------------|
| Windows | `DataPOS Setup 1.0.0.exe` | Instaluesi NSIS |
| Mac Intel | `DataPOS-1.0.0.dmg` | DMG për Mac Intel |
| Mac Apple Silicon | `DataPOS-1.0.0-arm64.dmg` | DMG për M1/M2/M3 |
| Linux | `DataPOS-1.0.0.AppImage` | AppImage portable |

---

## 🔐 Për Nënshkrimin e Aplikacionit (Opsional por i Rekomanduar)

### Windows:
Për të shmangur paralajmërimet e Windows Defender, duhet të nënshkruani aplikacionin:
1. Blini një certifikatë Code Signing (Comodo, DigiCert, etj.)
2. Shtoni në package.json nën `win`:
```json
"certificateFile": "path/to/certificate.pfx",
"certificatePassword": "your-password"
```

### Mac:
Për shpërndarje në Mac App Store ose pa paralajmërime:
1. Regjistrohuni në Apple Developer Program ($99/vit)
2. Krijoni certifikata dhe provisioning profiles
3. Nënshkruani dhe notarizoni aplikacionin

---

## ⚙️ Konfigurimi

Aplikacioni desktop lidhet automatikisht me:
- **URL**: https://datapos.pro

Për të ndryshuar URL-në, editoni `electron.js`:
```javascript
const PRODUCTION_URL = 'https://your-domain.com';
```

---

## 🖨️ Printimi i Heshtur

Aplikacioni desktop mbështet printim të heshtur (pa dialogun e printimit).
Kjo funksionon automatikisht kur përdorni aplikacionin Electron.

---

## ❓ Problemet e Zakonshme

### "App can't be opened because it is from an unidentified developer" (Mac)
```bash
# Hapni Terminal dhe ekzekutoni:
xattr -cr /Applications/DataPOS.app
```

### Windows Defender bllokon instalimin
- Klikoni "More info" → "Run anyway"
- Ose nënshkruani aplikacionin me certifikatë Code Signing

### Gabime gjatë ndërtimit
```bash
# Pastroni cache dhe provoni përsëri
rm -rf node_modules dist
yarn install
yarn electron:build:win  # ose :mac ose :linux
```

---

## 📞 Mbështetje

Për ndihmë, kontaktoni administratorin e sistemit ose vizitoni:
https://datapos.pro
