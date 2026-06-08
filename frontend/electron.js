const { app, BrowserWindow, Menu, ipcMain, shell, session } = require('electron');
const path = require('path');

let mainWindow;

// Production URL - Deployed URL (always active 24/7)
const PRODUCTION_URL = 'https://www.datapos.pro';

// Determine if we're in development or production
const isDev = process.env.NODE_ENV === 'development';

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 768,
    title: 'DataPOS',
    icon: path.join(__dirname, 'public/favicon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: true,
      allowRunningInsecureContent: false,
    },
    autoHideMenuBar: true,
  });

  // Remove menu bar for cleaner look
  Menu.setApplicationMenu(null);

  // Clear cache on start to avoid stale data issues
  session.defaultSession.clearCache();

  if (isDev) {
    // In development, load from React dev server
    mainWindow.loadURL('http://localhost:3000/#/login');
    mainWindow.webContents.openDevTools();
  } else {
    // In production, ALWAYS load from deployed domain - directly to login page
    const loginURL = PRODUCTION_URL + '/#/login';
    console.log('Loading production URL:', loginURL);
    mainWindow.loadURL(loginURL);
  }

  // Handle external links - open in default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http') && !url.includes('datapos.pro')) {
      shell.openExternal(url);
      return { action: 'deny' };
    }
    return { action: 'allow' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Maximize on start for POS usage
  mainWindow.maximize();

  // Handle offline mode
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.log('Failed to load:', errorDescription);
    // Show offline page or retry
    if (errorCode === -106) { // ERR_INTERNET_DISCONNECTED
      mainWindow.loadFile(path.join(__dirname, 'offline.html'));
    }
  });

  // Debug: Log when page finishes loading
  mainWindow.webContents.on('did-finish-load', () => {
    console.log('Page loaded successfully');
  });
}

// Silent printing handler
ipcMain.handle('silent-print', async (event, options) => {
  try {
    const win = BrowserWindow.getFocusedWindow();
    if (!win) {
      return { success: false, error: 'No window found' };
    }

    // Get available printers
    const printers = await win.webContents.getPrintersAsync();
    
    // Find the default printer or specified printer
    let targetPrinter = printers.find(p => p.isDefault);
    if (options.printerName) {
      const specificPrinter = printers.find(p => p.name === options.printerName);
      if (specificPrinter) {
        targetPrinter = specificPrinter;
      }
    }

    if (!targetPrinter) {
      return { success: false, error: 'No printer available' };
    }

    // Print silently
    await win.webContents.print({
      silent: true,
      printBackground: true,
      deviceName: targetPrinter.name,
      margins: {
        marginType: 'none'
      },
      pageSize: options.pageSize || 'A4',
      ...options.printOptions
    });

    return { success: true, printer: targetPrinter.name };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Get available printers
ipcMain.handle('get-printers', async () => {
  try {
    const win = BrowserWindow.getFocusedWindow();
    if (!win) {
      return [];
    }
    const printers = await win.webContents.getPrintersAsync();
    return printers.map(p => ({
      name: p.name,
      displayName: p.displayName,
      isDefault: p.isDefault,
      status: p.status
    }));
  } catch (error) {
    console.error('Error getting printers:', error);
    return [];
  }
});

// Print to PDF (for preview)
ipcMain.handle('print-to-pdf', async (event, options) => {
  try {
    const win = BrowserWindow.getFocusedWindow();
    if (!win) {
      return { success: false, error: 'No window found' };
    }

    const pdfData = await win.webContents.printToPDF({
      printBackground: true,
      margins: {
        top: 0,
        bottom: 0,
        left: 0,
        right: 0
      },
      pageSize: options.pageSize || 'A4',
    });

    return { success: true, data: pdfData.toString('base64') };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
