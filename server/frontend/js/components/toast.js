// js/components/toast.js
// Simple toast notification system.
//
// Usage:
//   import { toast } from './toast.js'
//   toast.success('Settings saved')
//   toast.error('Something went wrong')
//   toast.info('Run started')

const ICONS = {
  success: `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="var(--green)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="2,8 6,12 14,4"/></svg>`,
  error:   `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="var(--red)" stroke-width="1.8" stroke-linecap="round"><line x1="4" y1="4" x2="12" y2="12"/><line x1="12" y1="4" x2="4" y2="12"/></svg>`,
  info:    `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="var(--amber)" stroke-width="1.8" stroke-linecap="round"><circle cx="8" cy="8" r="6"/><line x1="8" y1="6" x2="8" y2="8"/><line x1="8" y1="10" x2="8" y2="11"/></svg>`,
};

function show(message, type = 'info', duration = 3500) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `
    <span class="toast-icon">${ICONS[type] ?? ''}</span>
    <span>${message}</span>
  `;

  container.appendChild(el);

  const remove = () => {
    el.classList.add('toast-out');
    el.addEventListener('animationend', () => el.remove(), { once: true });
  };

  setTimeout(remove, duration);
}

export const toast = {
  success: (msg, duration) => show(msg, 'success', duration),
  error:   (msg, duration) => show(msg, 'error',   duration),
  info:    (msg, duration) => show(msg, 'info',     duration),
};
