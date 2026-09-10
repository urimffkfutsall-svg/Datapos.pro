const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Silent printing
  silentPrint: (options) => ipcRenderer.invoke('silent-print', options),
  
  // Get available printers
  getPrinters: () => ipcRenderer.invoke('get-printers'),
  
  // Print to PDF
  printToPDF: (options) => ipcRenderer.invoke('print-to-pdf', options),
  
  // Check if running in Electron
  isElectron: true,
  
  // Platform info
  platform: process.platform,
});
