// js/pages/run.js
// Handles the Run page: task input, mode selection, start/stop, status display.

import { startRun }    from '/static/js/api.js';
import { store }       from '/static/js/store.js';
import { toast }       from '/static/js/components/toast.js';
import { appendLog }   from '/static/js/components/log-viewer.js';

export function initRunPage() {
  const taskInput    = document.getElementById('run-task-input');
  const modeSelect   = document.getElementById('run-mode-select');
  const startBtn     = document.getElementById('run-start-btn');
  const stopBtn      = document.getElementById('run-stop-btn');
  const statusBar    = document.getElementById('run-status-bar');
  const statusText   = document.getElementById('run-status-text');
  const logViewer    = document.getElementById('log-viewer');

  // Keyboard shortcut: Ctrl+Enter to start
  taskInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      if (!startBtn.disabled) startBtn.click();
    }
  });

  startBtn?.addEventListener('click', () => {
    const task = taskInput?.value?.trim();
    if (!task) {
      toast.error('Please enter a task description.');
      taskInput?.focus();
      return;
    }

    if (store.get('apiOnline') === false) {
      toast.error('API is not reachable.');
      return;
    }

    const modeOverride = modeSelect?.value || null;

    // Clear previous logs
    store.set('runLogs', []);
    store.set('runStatus', 'running');
    updateRunUI('running');

    logViewer?.classList.add('log-viewer-running');

    const handle = startRun({
      task,
      modeOverride: modeOverride === 'default' ? null : modeOverride,
      onMessage(frame) {
        appendLog(frame);
      },
      onDone(message) {
        store.set('runStatus', 'done');
        store.set('activeRun', null);
        updateRunUI('done');
        logViewer?.classList.remove('log-viewer-running');
        toast.success(message ?? 'Run completed.');
        appendLog({ type: 'status', level: 'INFO', message: '─── Run completed ───', ts: new Date().toISOString() });
      },
      onError(message) {
        store.set('runStatus', 'error');
        store.set('activeRun', null);
        updateRunUI('error', message);
        logViewer?.classList.remove('log-viewer-running');
        toast.error(message ?? 'Run failed.');
        appendLog({ type: 'status', level: 'ERROR', message: `─── Error: ${message} ───`, ts: new Date().toISOString() });
      },
      onClose() {
        // If still running when socket closes unexpectedly
        if (store.get('runStatus') === 'running') {
          store.set('runStatus', 'error');
          store.set('activeRun', null);
          updateRunUI('error', 'Connection closed unexpectedly.');
          logViewer?.classList.remove('log-viewer-running');
        }
      },
    });

    store.set('activeRun', handle);
  });

  stopBtn?.addEventListener('click', () => {
    const activeRun = store.get('activeRun');
    if (activeRun) {
      activeRun.cancel();
      store.set('activeRun', null);
      store.set('runStatus', 'idle');
      updateRunUI('idle');
      logViewer?.classList.remove('log-viewer-running');
      toast.info('Run cancelled.');
    }
  });
}

function updateRunUI(status, message = '') {
  const startBtn   = document.getElementById('run-start-btn');
  const stopBtn    = document.getElementById('run-stop-btn');
  const statusBar  = document.getElementById('run-status-bar');
  const statusText = document.getElementById('run-status-text');
  const spinner    = document.getElementById('run-spinner');
  const statusDot  = document.getElementById('run-status-dot');

  const isRunning = status === 'running';

  if (startBtn) startBtn.disabled = isRunning;
  if (stopBtn)  stopBtn.style.display = isRunning ? '' : 'none';

  if (statusBar) statusBar.style.display = status !== 'idle' ? '' : 'none';
  if (spinner)   spinner.style.display   = isRunning ? '' : 'none';

  const texts = {
    running: 'Running…',
    done:    'Completed successfully',
    error:   message || 'Run failed',
    idle:    '',
  };

  const dotColors = {
    running: 'checking',
    done:    'online',
    error:   'offline',
    idle:    '',
  };

  if (statusText)  statusText.textContent = texts[status] ?? '';
  if (statusDot)   statusDot.className    = `status-dot ${dotColors[status] ?? ''}`;
}
