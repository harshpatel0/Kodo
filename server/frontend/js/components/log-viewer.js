// js/components/log-viewer.js
// Renders log frames into the log viewer panel.
// Supports level filtering and auto-scroll.

import { store } from '../store.js';

const VISIBLE_LEVELS = new Set(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'stdout']);

let _autoScroll = true;

export function initLogViewer() {
  const body       = document.getElementById('log-body');
  const clearBtn   = document.getElementById('log-clear-btn');
  const scrollBtn  = document.getElementById('log-autoscroll-btn');
  const filterBtns = document.querySelectorAll('.log-filter-btn');

  // Filter buttons
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const level = btn.dataset.level;
      btn.classList.toggle('active');
      if (btn.classList.contains('active')) {
        VISIBLE_LEVELS.delete(level);
      } else {
        VISIBLE_LEVELS.add(level);
      }
      rerenderLogs();
    });
  });

  // Clear
  clearBtn?.addEventListener('click', () => {
    store.set('runLogs', []);
    renderLogs([]);
  });

  // Auto-scroll toggle
  scrollBtn?.addEventListener('click', () => {
    _autoScroll = !_autoScroll;
    scrollBtn.classList.toggle('active', _autoScroll);
    scrollBtn.title = _autoScroll ? 'Auto-scroll ON' : 'Auto-scroll OFF';
  });

  // Detect manual scroll (disable auto-scroll)
  body?.addEventListener('scroll', () => {
    if (!body) return;
    const atBottom = body.scrollHeight - body.scrollTop - body.clientHeight < 40;
    if (!atBottom) _autoScroll = false;
    else           _autoScroll = true;
    scrollBtn?.classList.toggle('active', _autoScroll);
  });

  // Subscribe to log updates
  store.subscribe('runLogs', rerenderLogs);
}

/**
 * Append a single log frame to the viewer (and store).
 * @param {object} frame
 */
export function appendLog(frame) {
  const logs = [...store.get('runLogs'), frame];
  store.set('runLogs', logs);
}

function rerenderLogs() {
  renderLogs(store.get('runLogs') ?? []);
}

function renderLogs(logs) {
  const body = document.getElementById('log-body');
  if (!body) return;

  const filtered = logs.filter(l => VISIBLE_LEVELS.has(l.level));

  if (filtered.length === 0) {
    body.innerHTML = '<div class="log-empty">No log output yet…</div>';
    return;
  }

  body.innerHTML = filtered.map(renderLine).join('');

  if (_autoScroll) {
    body.scrollTop = body.scrollHeight;
  }
}

function renderLine(frame) {
  const ts     = frame.ts ? frame.ts.split('T')[1]?.slice(0, 12) ?? '' : '';
  const level  = frame.level ?? 'INFO';
  const module = frame.module ?? (frame.type === 'stdout' ? 'stdout' : '');
  const msg    = escapeHtml(frame.message ?? '');

  return `<div class="log-line" data-level="${level}">
    <span class="log-ts text-mono">${ts}</span>
    <span class="log-level">${level}</span>
    <span class="log-module">${module}</span>
    <span class="log-msg">${msg}</span>
  </div>`;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}
