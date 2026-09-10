# KOMANDAT PËR DEPLOY — DataPOS

Repo është gati me `git init` + commit i parë i bërë. Hapi projektin te VS Code (File → Open Folder → `Datapos.pro-main`), hap një terminal (Ctrl+`) dhe ndiq hapat.

---

## 1) (Opsionale, por e rekomanduar) Puno në GitHub

```bash
# krijo repo bosh në github.com fillimisht, pastaj:
git remote add origin https://github.com/USERNAME/datapos.git
git branch -M main
git push -u origin main
```

Nëse s'do GitHub fare, mund të kërcesh direkt te hapi 3 (Cloudflare Pages lejon deploy direkt nga kompjuteri me `wrangler`, pa Git).

---

## 2) Backend → Render (kërkon GitHub, hap një herë në browser)

Render s'ka CLI për krijim service-i pa lidhur repo, prandaj kjo pjesë bëhet një herë në dashboard:

1. Push kodin te GitHub (hapi 1).
2. Shko te https://dashboard.render.com → **New +** → **Blueprint** → zgjidh repo `datapos`.
3. Render lexon automatikisht `render.yaml`-in që është në rrënjë të projektit.
4. Plotëso variablat kur të kërkohen:
   - `MONGO_URL` — connection string nga MongoDB Atlas
   - `DB_NAME` — p.sh. `datapos`
   - `JWT_SECRET` — një string i rastësishëm i gjatë (mund ta gjenerosh vetë me `openssl rand -hex 32`)
   - `GEMINI_API_KEY` — çelësi yt i Gemini
5. Pas ~2 minutash do të marrësh një URL si `https://datapos-backend.onrender.com`.

Testo shpejt në terminal pasi të marrësh URL-in:

```bash
curl https://datapos-backend.onrender.com/api/health   # ose endpoint-in që ke për health-check
```

---

## 3) Frontend → Cloudflare Pages (plotësisht me komanda, pa dashboard)

```bash
cd frontend

# instalo Wrangler globalisht (një herë)
npm install -g wrangler

# login në Cloudflare (hap browser për autorizim)
wrangler login

# instalo varësitë e frontend-it
npm install --legacy-peer-deps

# vendos URL-in e backend-it (nga hapi 2) PARA build-it
# në Linux/Mac:
export REACT_APP_BACKEND_URL=https://datapos-backend.onrender.com
# në Windows PowerShell:
# $env:REACT_APP_BACKEND_URL="https://datapos-backend.onrender.com"

# build prodhimi
npm run build

# deploy te Cloudflare Pages
wrangler pages deploy build --project-name=datapos
```

Wrangler do të krijojë projektin `datapos` automatikisht herën e parë dhe do të japë një URL si `https://datapos.pages.dev`.

**Për deploy-e të mëvonshme** (pasi ke bërë ndryshime):

```bash
export REACT_APP_BACKEND_URL=https://datapos-backend.onrender.com
npm run build
wrangler pages deploy build --project-name=datapos
```

---

## 4) Domain-i vetjak (p.sh. www.datapos.pro) — opsionale

```bash
wrangler pages project list
```

Pastaj në Cloudflare Dashboard → Pages → `datapos` → **Custom domains** → shto domain-in tënd (nëse domain-i tashmë është në Cloudflare, propagohet brenda pak minutash).

---

## Shënime

- `frontend/public/_redirects` dhe `frontend/wrangler.toml` janë shtuar tashmë — s'kërkohet konfigurim shtesë.
- Aplikacioni përdor `HashRouter` (jo `BrowserRouter`), prandaj routing-u i faqeve funksionon pa probleme edhe pa server-side rewrites.
- CORS në backend tashmë lejon të gjitha origjinat (`allow_origins=["*"]`) — s'duhet ndryshim.
- Build-i u testua lokalisht dhe kalon me sukses (vetëm disa warning ESLint të padëmshme për `useEffect` dependencies).
- Mos e commit-o kurrë `.env` — variablat e fshehta vendosen vetëm në Render/Cloudflare dashboard.
