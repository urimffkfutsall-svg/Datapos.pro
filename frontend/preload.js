const { contextBridge, ipcRenderer } = require('electron')

// ---------------------------------------------------------------------------
// Adresa e firmes se ketij kompjuteri.
// Lexohet SINKRON perpara se te niset React-i, qe thirrjet drejt API-t
// te shkojne te subdomaini i firmes (jo te www.datapos.pro).
// ---------------------------------------------------------------------------
let firmSubdomain = null
try {
  firmSubdomain = ipcRenderer.sendSync('firm:get-sync')
} catch (e) {
  firmSubdomain = null
}

const apiBase = firmSubdomain
  ? 'https://' + firmSubdomain + '.datapos.pro'
  : null

contextBridge.exposeInMainWorld('__DATAPOS_FIRM__', firmSubdomain)
contextBridge.exposeInMainWorld('__DATAPOS_API__', apiBase)

// ---------------------------------------------------------------------------
// API e aplikacionit desktop
// ---------------------------------------------------------------------------
contextBridge.exposeInMainWorld('electronAPI', {
  // Printimi
  silentPrint: (options) => ipcRenderer.invoke('silent-print', options),
  getPrinters: () => ipcRenderer.invoke('get-printers'),
  printToPDF: (options) => ipcRenderer.invoke('print-to-pdf', options),

  // Kycja e firmes ne kete PC
  getDeviceLock: () => ipcRenderer.invoke('device-lock:get'),
  setDeviceLock: (lock) => ipcRenderer.invoke('device-lock:set', lock),
  clearDeviceLock: () => ipcRenderer.invoke('device-lock:clear'),

  // Ruajtja offline
  offlineRead: () => ipcRenderer.invoke('offline:read'),
  offlineWrite: (data) => ipcRenderer.invoke('offline:write', data),

  // Rrjeti
  checkNetwork: () => ipcRenderer.invoke('net:check'),
  onNetworkStatus: (callback) => {
    const handler = (event, payload) => callback(payload)
    ipcRenderer.on('net:status', handler)
    return () => ipcRenderer.removeListener('net:status', handler)
  },

  // Informacion
  firm: firmSubdomain,
  apiBase: apiBase,
  isElectron: true,
  platform: process.platform,
})
