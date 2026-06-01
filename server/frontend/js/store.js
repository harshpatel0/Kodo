// js/store.js
// Minimal reactive state store.
// Components subscribe to keys; the store notifies them on change.
//
// Usage:
//   store.set('apiOnline', true)
//   store.get('apiOnline')          // → true
//   store.subscribe('apiOnline', v => console.log(v))

const _state = {
  apiOnline:   null,    // null = unknown, true/false = checked
  currentPage: 'run',
  runStatus:   'idle',  // 'idle' | 'running' | 'done' | 'error'
  runLogs:     [],
  activeRun:   null,    // { cancel: fn } | null
};

const _listeners = {};

function get(key) {
  return _state[key];
}

function set(key, value) {
  _state[key] = value;
  (_listeners[key] ?? []).forEach(fn => fn(value));
}

function subscribe(key, fn) {
  if (!_listeners[key]) _listeners[key] = [];
  _listeners[key].push(fn);
  // Return unsubscribe function
  return () => {
    _listeners[key] = _listeners[key].filter(f => f !== fn);
  };
}

export const store = { get, set, subscribe };
