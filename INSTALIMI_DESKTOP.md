# t3next POS - Udhëzime për Instalim Desktop (.exe)

## Kërkesat për ndërtimin e .exe

Për të ndërtuar aplikacionin si .exe në kompjuterin tuaj, ju duhet:

1. **Node.js** (versioni 18 ose më i ri) - https://nodejs.org/
2. **Python** (versioni 3.9 ose më i ri) - https://www.python.org/
3. **MongoDB** - https://www.mongodb.com/try/download/community
4. **Git** - https://git-scm.com/

## Hapat për ndërtimin e .exe

### 1. Shkarkoni kodin
```bash
# Klononi ose shkarkoni projektin
git clone [url-e-projektit]
cd t3next-pos
```

### 2. Instaloni varësitë e frontend
```bash
cd frontend
npm install
# ose
yarn install
```

### 3. Instaloni varësitë e backend
```bash
cd ../backend
pip install -r requirements.txt
```

### 4. Ndërtoni aplikacionin .exe
```bash
cd ../frontend

# Për të ndërtuar installer-in .exe për Windows:
npm run electron:dist
# ose
yarn electron:dist
```

### 5. Gjeni skedarin .exe
Pas ndërtimit, skedari `.exe` do të gjendet në:
```
frontend/dist/t3next POS Setup 1.0.0.exe
```

## Instalimi në PC të tjerë

1. Kopjoni skedarin `t3next POS Setup 1.0.0.exe` në PC-në e destinacionit
2. Ekzekutoni skedarin për të instaluar aplikacionin
3. Sigurohuni që MongoDB është i instaluar dhe po funksionon në PC
4. Sigurohuni që Python është i instaluar me varësitë e backend-it

## Konfigurimi i bazës së të dhënave

Aplikacioni kërkon MongoDB për të ruajtur të dhënat. 

### Opsioni 1: MongoDB lokal
Instaloni MongoDB Community Edition dhe sigurohuni që serveri MongoDB po funksionon në `localhost:27017`.

### Opsioni 2: MongoDB Atlas (Cloud)
Krijoni një llogari falas në MongoDB Atlas dhe përdorni connection string-un në konfigurimin e aplikacionit.

## Struktura e projektit

```
t3next-pos/
├── frontend/           # Aplikacioni React + Electron
│   ├── src/           # Kodi burimor i React
│   ├── electron.js    # Skedari kryesor i Electron
│   ├── package.json   # Konfigurimi i projektit
│   └── dist/          # Skedarët e ndërtuar (.exe)
├── backend/           # API FastAPI
│   ├── server.py      # Serveri kryesor
│   └── requirements.txt
└── README.md
```

## Komandat e disponueshme

```bash
# Zhvillim (web)
yarn start              # Hap React në browser

# Zhvillim (desktop)  
yarn electron:dev       # Hap aplikacionin në Electron

# Ndërtim
yarn electron:dist      # Ndërton .exe installer për Windows
yarn electron:dist:all  # Ndërton për Windows dhe Linux
```

## Troubleshooting

### Gabim: MongoDB nuk lidhet
- Sigurohuni që MongoDB është i instaluar dhe po funksionon
- Kontrolloni nëse porta 27017 është e disponueshme

### Gabim: Python nuk gjendet
- Sigurohuni që Python është i instaluar dhe në PATH
- Në Windows, mund të duhet të shtoni Python manualisht në PATH

### Gabim gjatë ndërtimit
- Fshini dosjen `node_modules` dhe `dist`
- Ekzekutoni `yarn install` përsëri
- Provoni `yarn electron:build` para `yarn electron:dist`

## Licenca

© 2025 t3next. Të gjitha të drejtat e rezervuara.
