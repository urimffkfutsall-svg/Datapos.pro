// ---- DATAPOS: LIDHJA ME SUBDOMAIN-IN ----------------------------------
// Cdo kerkese drejt API-t e mban me vete firmen (subdomain-in).
// Serveri e lexon koken X-Tenant-Subdomain dhe e gjen firmen edhe kur
// backend-i ndodhet ne nje host tjeter nga *.datapos.pro
(function () {
  if (typeof window === 'undefined') return
  if (window.__DATAPOS_HDR__) return
  window.__DATAPOS_HDR__ = true

  function firmSub() {
    try {
      if (window.__DATAPOS_FIRM__) return String(window.__DATAPOS_FIRM__)
      var h = (window.location && window.location.hostname) || ''
      var m = h.match(/^([a-z0-9-]+)\.datapos\.pro$/i)
      if (m && m[1] !== 'www' && m[1] !== 'app') return m[1].toLowerCase()
    } catch (e) {}
    return ''
  }

  // XMLHttpRequest (axios e perdor kete)
  try {
    var XHR = window.XMLHttpRequest.prototype
    var origSend = XHR.send
    XHR.send = function () {
      try {
        var s = firmSub()
        if (s) this.setRequestHeader('X-Tenant-Subdomain', s)
      } catch (e) {}
      return origSend.apply(this, arguments)
    }
  } catch (e) {}

  // fetch
  try {
    var origFetch = window.fetch
    if (origFetch) {
      window.fetch = function (input, init) {
        try {
          var s = firmSub()
          if (s) {
            init = init || {}
            var hd = new Headers(
              init.headers || (input && input.headers) || {},
            )
            hd.set('X-Tenant-Subdomain', s)
            init.headers = hd
          }
        } catch (e) {}
        return origFetch.call(this, input, init)
      }
    }
  } catch (e) {}
})()
// ---- FUND: LIDHJA ME SUBDOMAIN-IN -------------------------------------

import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
