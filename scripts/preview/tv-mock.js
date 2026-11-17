/* Development only: simulates the public Tizen boundary that app/device.js uses
   (tizen.application, tizen.systeminfo and tizen.tvwindow) for the browser preview and
   scripts/check-browser.mjs. It is never packaged, never contacts a TV, and a simulated
   input switch is not evidence that a TV switched inputs. */
(function () {
  'use strict';
  var DEFAULT_SOURCES = { connected: [{ type: 'HDMI', number: 2 }], disconnected: [{ type: 'HDMI', number: 1 }, { type: 'HDMI', number: 3 }] };
  var PREVIEW_CATALOG = [
    ['IkWsFHtOY9.Stremio', 'Stremio'], ['org.tizen.netflix-app', 'Netflix'], ['MCmYXNxgcu.DisneyPlus', 'Disney+'],
    ['9Ur5IzDKqV.TizenYouTube', 'YouTube'], ['com.samsung.tv.aria-video', 'Apple TV'], ['org.tizen.primevideo', 'Prime Video'],
    ['mWK87Xghap.ABCiview', 'ABC iview'], ['OyE7OuxlUi.SBSOnDemand', 'SBS On Demand'], ['org.tizen.apple.apple-music', 'Apple Music'],
    ['rJeHak5zRg.Spotify', 'Spotify'], ['3KA0pm7a7V.TubiTV', 'Tubi']
  ].map(function (a) { return { id: a[0], name: a[1], show: true, iconPath: '' }; });
  function clone(value) { return JSON.parse(JSON.stringify(value)); }

  function install(options) {
    var o = options || {};
    var tv = window.__tv = { catalog: o.catalog || PREVIEW_CATALOG, catalogFailure: !!o.catalogFailure, launchFailure: false, holdCatalog: false, pending: [], calls: [], catalogCalls: 0, listeners: [] };
    function record(call) {
      tv.calls.push(call);
      tv.listeners.forEach(function (listener) { try { listener(call); } catch (e) { /* A preview listener must not break the simulated API. */ } });
    }
    window.tizen = {
      ApplicationControlData: function (key, value) { this.key = key; this.value = value; },
      ApplicationControl: function (operation, uri, mime, category, data) { this.operation = operation; this.uri = uri; this.mime = mime; this.category = category; this.data = data; },
      application: {
        getCurrentApplication: function () { return { appInfo: { id: o.currentAppId || 'nClrkHome1.FrameHome' } }; },
        getAppsInfo: function (ok, fail) {
          tv.catalogCalls++;
          var finish = function () { if (tv.catalogFailure) fail({ name: 'UnknownError', message: 'Catalogue unavailable for QA' }); else ok(tv.catalog.map(function (a) { return Object.assign({}, a); })); };
          if (tv.holdCatalog) tv.pending.push({ ok: ok, fail: fail }); else setTimeout(finish, 0);
        },
        launch: function (id, ok, fail) {
          record({ method: 'launch', id: id });
          setTimeout(function () { if (tv.launchFailure) fail({ name: 'NotFoundError', message: 'App unavailable for QA' }); else ok(); }, 0);
        },
        launchAppControl: function (control, id, ok, fail) {
          record({ method: 'launchAppControl', id: id, control: control });
          setTimeout(function () { if (tv.launchFailure) fail({ name: 'UnknownError', message: 'Screen unavailable for QA' }); else ok(); }, 0);
        }
      }
    };
    if (o.inputUnavailable) return tv;
    tv.inputRequests = []; tv.sourceFailure = false; tv.inputDiscoveryFailure = false; tv.holdInputs = false;
    tv.currentInput = o.currentInput === undefined ? 2 : o.currentInput;
    tv.videoSources = clone(o.videoSources || DEFAULT_SOURCES);
    window.tizen.systeminfo = { getPropertyValue: function (name, ok, fail) {
      var finish = function () { if (tv.inputDiscoveryFailure) fail({ name: 'SecurityError' }); else ok(clone(tv.videoSources)); };
      if (tv.holdInputs) tv.inputRequests.push(finish); else setTimeout(finish, 0);
    } };
    window.tizen.tvwindow = {
      getSource: function () { return { type: 'HDMI', number: tv.currentInput }; },
      setSource: function (source, ok, fail) {
        record({ method: 'setSource', number: source.number });
        setTimeout(function () { if (tv.sourceFailure) fail({ name: 'SecurityError' }); else { tv.currentInput = source.number; ok(source); } }, 0);
      }
    };
    return tv;
  }

  /* Preview panel: ports cycle Connected → Standby (reported as disconnected) → Not reported. */
  var STORE = 'cleanframe.preview.tv-mock', STATES = ['connected', 'standby', 'absent'];
  var STATE_NAMES = { connected: 'Verbunden', standby: 'Standby', absent: 'Nicht gemeldet' };
  function loadConfig() {
    var config = { ports: { 1: 'standby', 2: 'connected', 3: 'standby', 4: 'absent' }, sourceFailure: false, discoveryFailure: false, apiUnavailable: false, open: false };
    try { var saved = JSON.parse(localStorage.getItem(STORE) || 'null'); if (saved && typeof saved === 'object') Object.keys(saved).forEach(function (k) { config[k] = saved[k]; }); } catch (e) { /* Use the defaults. */ }
    return config;
  }
  function saveConfig(config) { try { localStorage.setItem(STORE, JSON.stringify(config)); } catch (e) { /* Preview only. */ } }
  function sourcesFor(config) {
    var out = { connected: [], disconnected: [] };
    Object.keys(config.ports).sort().forEach(function (n) {
      if (config.ports[n] === 'connected') out.connected.push({ type: 'HDMI', number: Number(n) });
      else if (config.ports[n] === 'standby') out.disconnected.push({ type: 'HDMI', number: Number(n) });
    });
    return out;
  }
  function preview() {
    var config = loadConfig(), tv = install({ inputUnavailable: config.apiUnavailable, videoSources: sourcesFor(config) }), panel, log = [];
    function apply() {
      saveConfig(config);
      if (tv.videoSources) { tv.videoSources = sourcesFor(config); tv.sourceFailure = config.sourceFailure; tv.inputDiscoveryFailure = config.discoveryFailure; }
      render();
    }
    function note(text) { log.unshift(new Date().toLocaleTimeString('de-DE') + '  ' + text); log = log.slice(0, 6); render(); }
    tv.listeners.push(function (call) {
      if (call.method === 'setSource') note('setSource HDMI ' + call.number + (tv.sourceFailure ? ' → simulierter Fehler' : ' → simuliert umgeschaltet'));
      else if (call.method === 'launch' && call.id === 'org.tizen.tv-viewer') note('TV-Ansicht geöffnet (simuliert). Am Fernseher erschiene jetzt der Eingang.');
      else if (call.method === 'launch') note('App-Start simuliert: ' + call.id);
      else note('Samsung-Aufruf simuliert: ' + call.id);
    });
    function button(label, action, on) { return '<button type="button" tabindex="-1" data-mock="' + action + '"' + (on ? ' class="on"' : '') + '>' + label + '</button>'; }
    function escape(text) { return text.replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
    /* Expanded, the panel is two short rows in the empty band below the launcher's OK hint
       (stage y 1004–1080), so it covers no launcher text. The full log is in its tooltip. */
    function render() {
      if (!panel) return;
      var html = '<div class="mock-row">' + button(config.open ? 'TV-Simulation ▾' : 'TV-Simulation ▸', 'toggle') + '<span class="mock-note">Vorschau – kein TV-Test</span>';
      if (config.open) {
        html += Object.keys(config.ports).sort().map(function (n) {
          return '<span class="mock-port">HDMI ' + n + (tv.currentInput === Number(n) && tv.videoSources ? ' ●' : '') + '</span>' + button(STATE_NAMES[config.ports[n]], 'port.' + n);
        }).join('') + '</div><div class="mock-row">'
          + button('Umschalten schlägt fehl', 'sourceFailure', config.sourceFailure) + button('Erkennung schlägt fehl', 'discoveryFailure', config.discoveryFailure)
          + button('Schnittstelle fehlt (Neu laden)', 'apiUnavailable', config.apiUnavailable)
          + '<span class="mock-log" title="' + escape(log.join('\n')) + '">' + escape(log[0] || 'Noch keine simulierten Aufrufe.') + '</span>';
      }
      panel.innerHTML = html + '</div>';
      panel.className = config.open ? 'is-open' : '';
    }
    function mount() {
      var style = document.createElement('style');
      style.textContent = '#tvMock{position:fixed;left:8px;bottom:2px;z-index:100;max-width:calc(100vw - 16px);box-sizing:border-box;padding:2px 8px;border-radius:8px;background:rgba(20,18,16,.88);color:#f6f1e7;font:11px/16px system-ui,sans-serif;box-shadow:0 2px 12px rgba(0,0,0,.4)}'
        + '#tvMock .mock-row{display:flex;align-items:center;white-space:nowrap;min-width:0}#tvMock .mock-row+.mock-row{margin-top:2px}'
        + '#tvMock button{flex:none;margin:0 6px 0 0;padding:0 6px;border:1px solid rgba(246,241,231,.4);border-radius:5px;background:none;color:inherit;font:inherit;cursor:pointer}#tvMock button.on{background:#c2572b;border-color:#c2572b}'
        + '#tvMock .mock-note{flex:none;margin-right:12px;opacity:.75}#tvMock .mock-port{flex:none;margin:0 4px 0 6px}#tvMock .mock-log{flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;margin-left:6px;opacity:.85}';
      document.head.appendChild(style);
      panel = document.createElement('aside'); panel.id = 'tvMock'; panel.setAttribute('aria-label', 'TV-Simulation der Vorschau');
      panel.addEventListener('mousedown', function (ev) { ev.preventDefault(); });
      panel.addEventListener('click', function (ev) {
        var action = ev.target.getAttribute && ev.target.getAttribute('data-mock'), stage = document.getElementById('stage');
        if (!action) return;
        if (action === 'toggle') config.open = !config.open;
        else if (action.indexOf('port.') === 0) { var n = action.slice(5); config.ports[n] = STATES[(STATES.indexOf(config.ports[n]) + 1) % STATES.length]; }
        else if (action === 'apiUnavailable') { config.apiUnavailable = !config.apiUnavailable; saveConfig(config); location.reload(); return; }
        else config[action] = !config[action];
        apply();
        // Return input focus to the TV stage so the arrow keys keep driving the launcher.
        if (stage && !(document.activeElement && document.activeElement.className === 'hdmi-name-field')) stage.focus();
      });
      document.body.appendChild(panel); apply();
    }
    if (document.body) mount(); else document.addEventListener('DOMContentLoaded', mount);
  }
  window.CleanFrameTVMock = { install: install, preview: preview, defaultSources: clone(DEFAULT_SOURCES) };
}());
