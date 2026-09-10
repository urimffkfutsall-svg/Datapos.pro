/**
 * DataPOS - preload
 * ---------------------------------------------------------------------------
 * Ekspozon vetem funksionet e nevojshme te Electron-it ne dritaren e faqes,
 * me contextIsolation te aktivizuar (pa qasje te drejtperdrejte ne Node).
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // ---- Printimi ----
  silentPrint: (options) => ipcRenderer.invoke('silent-print', options),
  getPrinters: () => ipcRenderer.invoke('get-printers'),
  printToPDF: (options) => ipcRenderer.invoke('print-to-pdf', options),

  // ---- Kycja e firmes ne kete PC ----
  getDeviceLock: () => ipcRenderer.invoke('device-lock:get'),
  setDeviceLock: (lock) => ipcRenderer.invoke('device-lock:set', lock),
  clearDeviceLock: () => ipcRenderer.invoke('device-lock:clear'),

  // ---- Ruajtja offline ----
  offlineRead: () => ipcRenderer.invoke('offline:read'),
  offlineWrite: (data) => ipcRenderer.invoke('offline:write', data),

  // ---- Rrjeti ----
  checkNetwork: () => ipcRenderer.invoke('net:check'),
  onNetworkStatus: (callback) => {
    const handler = (event, status) => callback(status);
    ipcRenderer.on('net:status', handler);
    return () => ipcRenderer.removeListener('net:status', handler);
  },

  // ---- Informacion ----
  isElectron: true,
  platform: process.platform,
});
