// js/components/status-banner.js
// Manages the full-screen "API not running" banner.
// The banner is an element already in the HTML; this just shows/hides it.

import { store } from '/static/js/store.js';

export function initStatusBanner() {
  const banner      = document.getElementById('offline-banner');
  const retryBtn    = document.getElementById('offline-retry-btn');
  const urlEl       = document.getElementById('offline-api-url');

  if (urlEl) {
    urlEl.textContent = `${window.location.protocol}//${window.location.host}`;
  }

  // React to store changes
  store.subscribe('apiOnline', (online) => {
    if (online === false) {
      banner?.classList.add('visible');
    } else if (online === true) {
      banner?.classList.remove('visible');
    }
    // null = still checking; leave banner hidden initially
  });

  retryBtn?.addEventListener('click', () => {
    // Signal a recheck - health polling in main.js handles it
    store.set('apiOnline', null);
    retryBtn.disabled = true;
    retryBtn.textContent = 'Checking…';
    setTimeout(() => {
      retryBtn.disabled = false;
      retryBtn.textContent = 'Retry';
    }, 3000);
  });
}
