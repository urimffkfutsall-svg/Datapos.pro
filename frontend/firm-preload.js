const { contextBridge, ipcRenderer } = require('electron')

// Preload i dritares se konfigurimit te firmes (hera e pare pas instalimit)
contextBridge.exposeInMainWorld('firmAPI', {
  get: () => ipcRenderer.invoke('firm:get'),
  check: (subdomain) => ipcRenderer.invoke('firm:check', subdomain),
  save: (subdomain) => ipcRenderer.invoke('firm:save', subdomain),
})
