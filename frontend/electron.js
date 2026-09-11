const { app, BrowserWindow, ipcMain, net, Menu, shell } = require('electron')
const path = require('path')
const fs = require('fs')

// ---------------------------------------------------------------------------
// Konfigurimi
// ---------------------------------------------------------------------------
const APEX = 'datapos.pro'

let mainWindow = null
let setupWindow = null
let netWatch = null
let lastOnline = true

// ---------------------------------------------------------------------------
// Ruajtja lokale (AppData\Roaming\DataPOS)
// ---------------------------------------------------------------------------
function storePath(name) {
  return path.join(app.getPath('userData'), name)
}

function readJson(name, fallback) {
  try {
    const p = storePath(name)
    if (!fs.existsSync(p)) return fallback
    return JSON.parse(fs.readFileSync(p, 'utf8'))
  } catch (e) {
    return fallback
  }
}

function writeJson(name, data) {
  try {
    fs.mkdirSync(app.getPath('userData'), { recursive: true })
    fs.writeFileSync(storePath(name), JSON.stringify(data, null, 2), 'utf8')
    return true
  } catch (e) {
    return false
  }
}

// ---------------------------------------------------------------------------
// Adresa e firmes per kete kompjuter
// ---------------------------------------------------------------------------
// Konfigurimi i firmes ruhet pergjithmone ne kete kompjuter.
// Kerkohet perseri VETEM pas cinstalimit dhe instalimit te ri:
// ate pune e ben instaluesi (installer.nsh), i cili fshin firm.json.
function getFirm() {
  const cfg = readJson('firm.json', null)
  if (cfg && cfg.subdomain) return cfg
  return null
}

function normalizeSubdomain(input) {
  let s = String(input || '').trim().toLowerCase()
  s = s.replace(/^https?:\/\//, '')
  s = s.replace(/\/.*$/, '')
  s = s.replace(/\.datapos\.pro$/, '')
  s = s.replace(/[^a-z0-9-]/g, '')
  return s
}

function firmUrl(subdomain) {
  return 'https://' + subdomain + '.' + APEX
}

// ---------------------------------------------------------------------------
// Kontrolli i rrjetit
// ---------------------------------------------------------------------------
function checkReachable(url) {
  return new Promise((resolve) => {
    let done = false
    const finish = (ok) => {
      if (!done) {
        done = true
        resolve(ok)
      }
    }
    try {
      const request = net.request({ method: 'HEAD', url: url })
      request.on('response', () => finish(true))
      request.on('error', () => finish(false))
      request.end()
      setTimeout(() => finish(false), 5000)
    } catch (e) {
      finish(false)
    }
  })
}

function notifyNetwork(online) {
  lastOnline = online
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('net:status', { online: online })
  }
}

function startNetworkWatch(url) {
  if (netWatch) clearInterval(netWatch)
  netWatch = setInterval(async () => {
    const ok = await checkReachable(url)
    if (ok !== lastOnline) notifyNetwork(ok)
  }, 15000)
}

// ---------------------------------------------------------------------------
// Dritarja e konfigurimit te firmes (hera e pare pas instalimit)
// ---------------------------------------------------------------------------
function createSetupWindow() {
  setupWindow = new BrowserWindow({
    width: 560,
    height: 640,
    resizable: false,
    center: true,
    title: 'DataPOS - Konfigurimi',
    autoHideMenuBar: true,
    icon: path.join(__dirname, 'public', 'icon.ico'),
    webPreferences: {
      preload: path.join(__dirname, 'firm-preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  setupWindow.loadFile(path.join(__dirname, 'firm-setup.html'))

  setupWindow.on('closed', () => {
    setupWindow = null
    if (!mainWindow) app.quit()
  })
}

// ---------------------------------------------------------------------------
// Dritarja kryesore
// ---------------------------------------------------------------------------
async function createMainWindow(firm) {
  const url = firmUrl(firm.subdomain)

  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    show: false,
    title: 'DataPOS - ' + firm.subdomain,
    autoHideMenuBar: true,
    icon: path.join(__dirname, 'public', 'icon.ico'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  mainWindow.maximize()
  mainWindow.show()

  const online = await checkReachable(url)

  if (online) {
    mainWindow.loadURL(url)
  } else {
    mainWindow.loadFile(path.join(__dirname, 'build', 'index.html'), {
      hash: '/login',
    })
    notifyNetwork(false)
  }

  mainWindow.webContents.on('did-fail-load', (e, code, desc, failedUrl) => {
    if (failedUrl && failedUrl.indexOf('http') === 0) {
      mainWindow.loadFile(path.join(__dirname, 'build', 'index.html'), {
        hash: '/login',
      })
      notifyNetwork(false)
    }
  })

  // Cdo kerkese drejt API-t e mban me vete firmen e ketij PC-je.
  mainWindow.webContents.on('dom-ready', () => {
    const sub = JSON.stringify(firm.subdomain)
    mainWindow.webContents
      .executeJavaScript(
        'window.__DATAPOS_FIRM__ = ' +
          sub +
          '; window.__DATAPOS_API__ = "https://" + ' +
          sub +
          ' + ".' +
          APEX +
          '";',
      )
      .catch(() => {})
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  try {
    const ses = mainWindow.webContents.session
    ses.webRequest.onBeforeSendHeaders((details, callback) => {
      const h = details.requestHeaders || {}
      h['X-Tenant-Subdomain'] = firm.subdomain
      callback({ requestHeaders: h })
    })
  } catch (e) {}

  startNetworkWatch(url)
  buildMenu(firm)
}

// ---------------------------------------------------------------------------
// Menuja
// ---------------------------------------------------------------------------
function buildMenu(firm) {
  const template = [
    {
      label: 'DataPOS',
      submenu: [
        { label: 'Firma: ' + (firm ? firm.subdomain : '-'), enabled: false },
        { type: 'separator' },
        {
          label: 'Rifresko',
          accelerator: 'F5',
          click: () => mainWindow && mainWindow.reload(),
        },
        {
          label: 'Ekran i plote',
          accelerator: 'F11',
          click: () =>
            mainWindow && mainWindow.setFullScreen(!mainWindow.isFullScreen()),
        },
        {
          label: 'Mjetet e zhvilluesit',
          accelerator: 'F12',
          click: () => mainWindow && mainWindow.webContents.toggleDevTools(),
        },
        { type: 'separator' },
        {
          label: 'Ndrysho firmen e ketij PC-je...',
          click: () => {
            writeJson('firm.json', {})
            writeJson('device-lock.json', {})
            app.relaunch()
            app.exit(0)
          },
        },
        { type: 'separator' },
        { label: 'Dil', role: 'quit' },
      ],
    },
  ]
  Menu.setApplicationMenu(Menu.buildFromTemplate(template))
}

// ---------------------------------------------------------------------------
// IPC - konfigurimi i firmes
// ---------------------------------------------------------------------------
ipcMain.handle('firm:get', () => getFirm())

// Lexim sinkron nga preload-i, perpara se te niset React-i
ipcMain.on('firm:get-sync', (e) => {
  const f = getFirm()
  e.returnValue = f && f.subdomain ? f.subdomain : null
})

ipcMain.handle('firm:check', async (e, raw) => {
  const sub = normalizeSubdomain(raw)
  if (!sub) return { ok: false, error: 'Shkruani adresen e firmes.' }
  const url = firmUrl(sub)
  const reachable = await checkReachable(url)
  return { ok: true, subdomain: sub, url: url, reachable: reachable }
})

ipcMain.handle('firm:save', async (e, raw) => {
  const sub = normalizeSubdomain(raw)
  if (!sub) return { ok: false, error: 'Adresa nuk eshte e vlefshme.' }

  writeJson('firm.json', {
    subdomain: sub,
    saved_at: new Date().toISOString(),
  })

  if (setupWindow && !setupWindow.isDestroyed()) {
    const w = setupWindow
    setupWindow = null
    w.close()
  }

  await createMainWindow({ subdomain: sub })
  return { ok: true, subdomain: sub }
})

// ---------------------------------------------------------------------------
// IPC - kycja e firmes ne kete PC (device lock)
// ---------------------------------------------------------------------------
ipcMain.handle('device-lock:get', () => readJson('device-lock.json', null))

ipcMain.handle('device-lock:set', (e, lock) => {
  const current = readJson('device-lock.json', null)
  if (current && current.tenant_id && lock && lock.tenant_id) {
    if (current.tenant_id !== lock.tenant_id) {
      return { ok: false, locked: current }
    }
  }
  writeJson('device-lock.json', lock || {})
  return { ok: true, locked: lock }
})

ipcMain.handle('device-lock:clear', () => {
  writeJson('device-lock.json', {})
  return { ok: true }
})

// ---------------------------------------------------------------------------
// IPC - ruajtja offline dhe rrjeti
// ---------------------------------------------------------------------------
ipcMain.handle('offline:read', () => readJson('offline-store.json', {}))

ipcMain.handle('offline:write', (e, data) => {
  writeJson('offline-store.json', data || {})
  return { ok: true }
})

ipcMain.handle('net:check', async () => {
  const firm = getFirm()
  const url = firm ? firmUrl(firm.subdomain) : 'https://www.' + APEX
  const online = await checkReachable(url)
  lastOnline = online
  return { online: online }
})

// ---------------------------------------------------------------------------
// IPC - printimi
// ---------------------------------------------------------------------------
ipcMain.handle('get-printers', async (event) => {
  try {
    const wc = event.sender
    if (typeof wc.getPrintersAsync === 'function') {
      return await wc.getPrintersAsync()
    }
    return wc.getPrinters ? wc.getPrinters() : []
  } catch (e) {
    return []
  }
})

ipcMain.handle('silent-print', async (event, options) => {
  const opts = options || {}
  return new Promise((resolve) => {
    try {
      event.sender.print(
        {
          silent: true,
          printBackground: true,
          deviceName: opts.printerName || '',
          margins: { marginType: 'none' },
        },
        (success, reason) => resolve({ success: success, reason: reason }),
      )
    } catch (err) {
      resolve({ success: false, reason: String(err) })
    }
  })
})

ipcMain.handle('print-to-pdf', async (event, options) => {
  try {
    const data = await event.sender.printToPDF(
      Object.assign({ printBackground: true }, options || {}),
    )
    return { success: true, data: data.toString('base64') }
  } catch (err) {
    return { success: false, error: String(err) }
  }
})

// ---------------------------------------------------------------------------
// Nisja
// ---------------------------------------------------------------------------
const gotLock = app.requestSingleInstanceLock()

if (!gotLock) {
  app.quit()
} else {
  app.on('second-instance', () => {
    const w = mainWindow || setupWindow
    if (w && !w.isDestroyed()) {
      if (w.isMinimized()) w.restore()
      w.focus()
    }
  })

  app.whenReady().then(() => {
    const firm = getFirm()
    if (firm && firm.subdomain) {
      createMainWindow(firm)
    } else {
      createSetupWindow()
    }

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        const f = getFirm()
        if (f && f.subdomain) createMainWindow(f)
        else createSetupWindow()
      }
    })
  })

  app.on('window-all-closed', () => {
    if (netWatch) clearInterval(netWatch)
    if (process.platform !== 'darwin') app.quit()
  })
}
