// js/pages/settings.js
// Loads settings from the API, binds them to the form, and saves on submit.
// The form field IDs map directly to settings paths (dot-notation).

import { getSettings, postSettings } from '/static/js/api.js';
import { toast }                     from '/static/js/components/toast.js';

// Map of field ID → path in the settings object (dot-notation)
const FIELDS = [
  // Models - global
  { id: 'cfg-ollama-server',       path: 'models.ollama_server',       type: 'text' },

  // Skill installation model
  { id: 'cfg-skill-model',         path: 'models.skill_installation.model_name',  type: 'text' },
  { id: 'cfg-skill-temp',          path: 'models.skill_installation.temperature', type: 'number' },
  { id: 'cfg-skill-keepalive',     path: 'models.skill_installation.keep_alive',  type: 'number' },

  // Planner model
  { id: 'cfg-planner-model',       path: 'models.planner.model_name',  type: 'text' },
  { id: 'cfg-planner-temp',        path: 'models.planner.temperature', type: 'number' },
  { id: 'cfg-planner-keepalive',   path: 'models.planner.keep_alive',  type: 'number' },
  { id: 'cfg-planner-thinking',    path: 'models.planner.thinking',    type: 'bool' },

  // Actor model
  { id: 'cfg-actor-model',         path: 'models.actor.model_name',   type: 'text' },
  { id: 'cfg-actor-temp',          path: 'models.actor.temperature',  type: 'number' },
  { id: 'cfg-actor-keepalive',     path: 'models.actor.keep_alive',   type: 'number' },
  { id: 'cfg-actor-thinking',      path: 'models.actor.thinking',     type: 'bool' },
  { id: 'cfg-actor-screenshot',    path: 'models.actor.attach_screenshot_of_active_window', type: 'bool' },

  // Autonomy actor model
  { id: 'cfg-auto-model',          path: 'models.autonomy_actor.model_name',  type: 'text' },
  { id: 'cfg-auto-temp',           path: 'models.autonomy_actor.temperature', type: 'number' },
  { id: 'cfg-auto-keepalive',      path: 'models.autonomy_actor.keep_alive',  type: 'number' },
  { id: 'cfg-auto-thinking',       path: 'models.autonomy_actor.thinking',    type: 'bool' },
  { id: 'cfg-auto-screenshot',     path: 'models.autonomy_actor.attach_screenshot_of_active_window', type: 'bool' },

  // Orchestrator
  { id: 'cfg-settle-time',             path: 'orchestrator.action_settle_time',                          type: 'number' },
  { id: 'cfg-use-autonomy',            path: 'orchestrator.use_autonomy_mode',              type: 'bool' },
  { id: 'cfg-max-iter-per-step',       path: 'orchestrator.planner_architecture.max_iterations_per_step',type: 'number' },
  { id: 'cfg-max-autonomy-steps',      path: 'orchestrator.planner_architecture.max_autonomy_steps',     type: 'number' },
  { id: 'cfg-max-replan-loop',         path: 'orchestrator.planner_architecture.max_replan_loop',        type: 'number' },
  { id: 'cfg-enforce-max-iter',        path: 'orchestrator.autonomy_orchestrator.enforce_max_total_iterations', type: 'bool' },
  { id: 'cfg-max-total-iter',          path: 'orchestrator.autonomy_orchestrator.max_total_iterations',  type: 'number' },

  // Context provider
  { id: 'cfg-ctx-waiting',         path: 'context_provider.waiting_period',  type: 'number' },
  { id: 'cfg-ctx-skip-ticks',      path: 'context_provider.skip_after_ticks', type: 'number' },
];

// ── Deep get/set helpers ──────────────────────────────────────────────────────

function deepGet(obj, path) {
  return path.split('.').reduce((cur, key) => cur?.[key], obj);
}

function deepSet(obj, path, value) {
  const keys = path.split('.');
  let cur = obj;
  for (let i = 0; i < keys.length - 1; i++) {
    if (cur[keys[i]] === undefined) cur[keys[i]] = {};
    cur = cur[keys[i]];
  }
  cur[keys[keys.length - 1]] = value;
}

// ── Init ──────────────────────────────────────────────────────────────────────

export function initSettingsPage() {
  const loadBtn    = document.getElementById('settings-load-btn');
  const saveBtn    = document.getElementById('settings-save-btn');
  const rawToggle  = document.getElementById('settings-raw-toggle');
  const rawArea    = document.getElementById('settings-raw-area');
  const formArea   = document.getElementById('settings-form-area');

  loadBtn?.addEventListener('click', loadSettings);
  saveBtn?.addEventListener('click', saveSettings);

  // Raw JSON toggle
  rawToggle?.addEventListener('change', (e) => {
    const showRaw = e.target.checked;
    rawArea.style.display  = showRaw ? '' : 'none';
    formArea.style.display = showRaw ? 'none' : '';
    if (showRaw) syncFormToRaw();
  });

  rawArea?.addEventListener('input', syncRawToForm);

  // Load on page visit
  loadSettings();
}

async function loadSettings() {
  const loadBtn = document.getElementById('settings-load-btn');
  if (loadBtn) { loadBtn.disabled = true; loadBtn.textContent = 'Loading…'; }

  try {
    const data = await getSettings();
    populateForm(data);
    syncFormToRaw();
    toast.success('Settings loaded.');
  } catch (err) {
    toast.error(`Failed to load settings: ${err.message}`);
  } finally {
    if (loadBtn) { loadBtn.disabled = false; loadBtn.textContent = 'Reload'; }
  }
}

async function saveSettings() {
  const saveBtn   = document.getElementById('settings-save-btn');
  const rawToggle = document.getElementById('settings-raw-toggle');

  if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = 'Saving…'; }

  try {
    let data;
    if (rawToggle?.checked) {
      // Save from raw JSON editor
      const rawArea = document.getElementById('settings-raw-area');
      data = JSON.parse(rawArea.value);
    } else {
      data = readForm();
    }

    await postSettings(data);
    toast.success('Settings saved successfully.');
  } catch (err) {
    toast.error(`Failed to save: ${err.message}`);
  } finally {
    if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = 'Save Settings'; }
  }
}

// ── Form population & reading ─────────────────────────────────────────────────

function populateForm(data) {
  FIELDS.forEach(({ id, path, type }) => {
    const el  = document.getElementById(id);
    if (!el) return;

    const val = deepGet(data, path);
    if (val === undefined || val === null) return;

    if (type === 'bool') {
      el.checked = !!val;
    } else {
      el.value = val;
    }
  });
}

function readForm() {
  const data = {};
  FIELDS.forEach(({ id, path, type }) => {
    const el = document.getElementById(id);
    if (!el) return;

    let value;
    if (type === 'bool')   value = el.checked;
    else if (type === 'number') value = parseFloat(el.value);
    else                   value = el.value;

    deepSet(data, path, value);
  });
  return data;
}

function syncFormToRaw() {
  const rawArea = document.getElementById('settings-raw-area');
  if (!rawArea) return;
  try {
    rawArea.value = JSON.stringify(readForm(), null, 2);
  } catch { /* ignore */ }
}

function syncRawToForm() {
  const rawArea = document.getElementById('settings-raw-area');
  if (!rawArea) return;
  try {
    const data = JSON.parse(rawArea.value);
    populateForm(data);
  } catch { /* JSON not valid yet, ignore */ }
}
