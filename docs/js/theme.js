// Theme toggle. Honours prefers-color-scheme until the reader chooses.
const KEY = 'ptt-theme';

const saved = localStorage.getItem(KEY);
if (saved) document.documentElement.setAttribute('data-theme', saved);

function current() {
  return document.documentElement.getAttribute('data-theme')
    || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
}

export function toggleTheme() {
  const next = current() === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem(KEY, next);
  syncLabel();
}

function syncLabel() {
  document.querySelectorAll('[data-theme-toggle]').forEach((b) => {
    const dark = current() === 'dark';
    b.textContent = dark ? 'light' : 'dark';
    b.setAttribute('aria-label', `Switch to ${dark ? 'light' : 'dark'} theme`);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-theme-toggle]').forEach((b) =>
    b.addEventListener('click', toggleTheme));
  syncLabel();
});
