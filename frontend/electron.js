/**
 * DataPOS - Electron main process
 * ---------------------------------------------------------------------------
 * Karakteristikat:
 *  - Puna offline: nese serveri nuk arrihet, hapet kopja lokale (build/).
 *  - Kycja e firmes ne PC: ruhet ne device-lock.json ne dosjen e app-it.
 *  - Ruajtja offline: offline-store.json (rezerve per te dhena te medha).
 *  - Njoftimi i rrjetit: dergon net:status ne UI kur lidhja bie/kthehet.
 *  - Vetem nje instance e aplikacionit njeheresh.
 */
const {
  app,
  BrowserWindow,
  Menu,
  ipcMain,
  shell,
  session,
  net,
} = require('electron');
const path = require('path');
const fs = require('fs');

let mainWindow;
let lastOnline = null;
let netTimer = null;

const PRODUCTION_URL = 'https://www.datapos.pro';
const isDev = process.env.NODE_ENV === 'development';

/* ------------------------------------------------------------------ */
/* Ruajtja lokale e skedareve                                          */
/* ------------------------------------------------------------------ */

const dataFile = (name) => path.join(app.getPath('userData'), name);

const readJson = (name, fallback = null) => {
  try {
    const file = dataFile(name);
    if (!fs.existsSync(file)) return fallback;
    return JSON.parse(fs.readFileSync(file, 'utf-8'));
  } catch (e) {
    return fallback;
  }
};

const writeJson = (name, data) => {
  try {
    fs.writeFileSync(dataFile(name), JSON.stringify(data, null, 2), 'utf-8');
    return true;
  } catch (e) {
    return false;
  }
};

/* ------------------------------------------------------------------ */
/* Kontrolli i lidhjes                                                 */
/* ------------------------------------------------------------------ */

const checkServerReachable = (timeoutMs = 4000) =>
  new Promise((resolve) => {
    let done = false;
    const finish = (value) => {
      if (!done) {
        done = true;
        resolve(value);
      }
    };
    try {
      const request = net.request({ method: 'HEAD', url: PRODUCTION_URL });
      request.on('response', () => finish(true));
      request.on('error', () => finish(false));
      request.end();
      setTimeout(() => finish(false), timeoutMs);
    } catch (e) {
      finish(false);
    }
  });

const notifyNetwork = (online) => {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('net:status', { online });
  }
};

const startNetworkWatch = () => {
  if (netTimer) clearInterval(netTimer);
  netTimer = setInterval(async () => {
    const online = await checkServerReachable();
    if (online !== lastOnline) {
      lastOnline = online;
      notifyNetwork(online);
    }
  }, 15000);
};

/* ------------------------------------------------------------------ */
/* Dritarja kryesore                                                   */
/* ------------------------------------------------------------------ */

const loadLocalBuild = () => {
  const localIndex = path.join(__dirname, 'build', 'index.html');
  if (fs.existsSync(localIndex)) {
    mainWindow.loadFile(localIndex, { hash: '/login' });
  } else {
    mainWindow.loadFile(path.join(__dirname, 'offline.html'));
  }
};

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 768,
    title: 'DataPOS',
    icon: path.join(__dirname, 'public/icon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: true,
      allowRunningInsecureContent: false,
    },
    autoHideMenuBar: true,
  });

  Menu.setApplicationMenu(null);
  session.defaultSession.clearCache();

  if (isDev) {
    mainWindow.loadURL('http://localhost:3000/#/login');
    mainWindow.webContents.openDevTools();
  } else {
    // Offline-first: kontrollo serverin, perndryshe hap kopjen lokale
    const online = await checkServerReachable();
    lastOnline = online;
    if (online) {
      mainWindow.loadURL(PRODUCTION_URL + '/#/login');
    } else {
      loadLocalBuild();
    }
  }

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http') && !url.includes('datapos.pro')) {
      shell.openExternal(url);
      return { action: 'deny' };
    }
    return { action: 'allow' };
  });

  // Nese ngarkimi deshton (pa internet), kalo ne kopjen lokale
  mainWindow.webContents.on('did-fail-load', (event, errorCode, desc, url, isMainFrame) => {
    if (!isMainFrame) return;
    console.log('Ngarkimi deshtoi:', errorCode, desc);
    lastOnline = false;
    notifyNetwork(false);
    loadLocalBuild();
  });

  mainWindow.webContents.on('did-finish-load', () => {
    notifyNetwork(lastOnline !== false);
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  mainWindow.maximize();
  startNetworkWatch();
}

/* ------------------------------------------------------------------ */
/* IPC: kycja e firmes ne PC                                           */
/* ------------------------------------------------------------------ */

ipcMain.handle('device-lock:get', () => readJson('device-lock.json', null));

ipcMain.handle('device-lock:set', (event, lock) => {
  const existing = readJson('device-lock.json', null);
  // Nese PC-ja eshte kycur me pare, mos e mbishkruaj me firme tjeter
  if (existing && existing.tenant_id && lock?.tenant_id !== existing.tenant_id) {
    return { success: false, lock: existing, error: 'PC-ja eshte kycur per firme tjeter' };
  }
  const ok = writeJson('device-lock.json', lock);
  return { success: ok, lock };
});

ipcMain.handle('device-lock:clear', () => {
  try {
    const file = dataFile('device-lock.json');
    if (fs.existsSync(file)) fs.unlinkSync(file);
    return { success: true };
  } catch (e) {
    return { success: false, error: e.message };
  }
});

/* ------------------------------------------------------------------ */
/* IPC: ruajtja offline dhe rrjeti                                     */
/* ------------------------------------------------------------------ */

ipcMain.handle('offline:read', () => readJson('offline-store.json', {}));
ipcMain.handle('offline:write', (event, data) => ({
  success: writeJson('offline-store.json', data || {}),
}));
ipcMain.handle('net:check', async () => {
  const online = await checkServerReachable();
  lastOnline = online;
  return { online };
});

/* ------------------------------------------------------------------ */
/* IPC: printimi                                                       */
/* ------------------------------------------------------------------ */

ipcMain.handle('silent-print', async (event, options = {}) => {
  try {
    const win = BrowserWindow.getFocusedWindow() || mainWindow;
    if (!win) return { success: false, error: 'Nuk u gjet dritarja' };

    const printers = await win.webContents.getPrintersAsync();
    let targetPrinter = printers.find((p) => p.isDefault);
    if (options.printerName) {
      const specific = printers.find((p) => p.name === options.printerName);
      if (specific) targetPrinter = specific;
    }
    if (!targetPrinter) return { success: false, error: 'Nuk ka printer' };

    await win.webContents.print({
      silent: true,
      printBackground: true,
      deviceName: targetPrinter.name,
      margins: { marginType: 'none' },
      pageSize: options.pageSize || 'A4',
      ...options.printOptions,
    });
    return { success: true, printer: targetPrinter.name };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-printers', async () => {
  try {
    const win = BrowserWindow.getFocusedWindow() || mainWindow;
    if (!win) return [];
    const printers = await win.webContents.getPrintersAsync();
    return printers.map((p) => ({
      name: p.name,
      displayName: p.displayName,
      isDefault: p.isDefault,
      status: p.status,
    }));
  } catch (error) {
    return [];
  }
});

ipcMain.handle('print-to-pdf', async (event, options = {}) => {
  try {
    const win = BrowserWindow.getFocusedWindow() || mainWindow;
    if (!win) return { success: false, error: 'Nuk u gjet dritarja' };
    const pdfData = await win.webContents.printToPDF({
      printBackground: true,
      margins: { top: 0, bottom: 0, left: 0, right: 0 },
      pageSize: options.pageSize || 'A4',
    });
    return { success: true, data: pdfData.toString('base64') };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

/* ------------------------------------------------------------------ */
/* Cikli i aplikacionit                                                */
/* ------------------------------------------------------------------ */

// Vetem nje instance - shmang bllokimin e skedareve dhe dritare te dyfishta
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(() => {
    createWindow();
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  });
}

app.on('window-all-closed', () => {
  if (netTimer) clearInterval(netTimer);
  if (process.platform !== 'darwin') app.quit();
});
