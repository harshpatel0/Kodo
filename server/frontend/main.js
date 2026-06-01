// main.js
// Entry point. Imports and initialises all modules.

import { checkHealth }       from './js/api.js';
import { store }             from './js/store.js';
import { initRouter }        from './js/router.js';
import { initStatusBanner }  from './js/components/status-banner.js';
import { initLogViewer }     from './js/components/log-viewer.js';
import { initRunPage }       from './js/pages/run.js';
import { initSettingsPage }  from './js/pages/settings.js';

const HEALTH_INTERVAL_MS = 5000;

async function pollHealth() {
  const online = await checkHealth();
  const prev   = store.get('apiOnline');

  store.set('apiOnline', online);

  // Update sidebar dot
  const dot    = document.getElementById('sidebar-status-dot');
  const label  = document.getElementById('sidebar-status-label');
  if (dot) {
    dot.className = `status-dot ${online ? 'online' : 'offline'}`;
  }
  if (label) {
    label.textContent = online ? 'API online' : 'API offline';
  }
}

async function init() {
  initRouter();
  initStatusBanner();
  initLogViewer();
  initRunPage();
  initSettingsPage();

  // Initial check (mark as "checking" first)
  const dot   = document.getElementById('sidebar-status-dot');
  const label = document.getElementById('sidebar-status-label');
  if (dot)   dot.className  = 'status-dot checking';
  if (label) label.textContent = 'Checking…';

  await pollHealth();

  // Poll every 5 seconds
  setInterval(pollHealth, HEALTH_INTERVAL_MS);
}

document.addEventListener('DOMContentLoaded', init);
