import { filter, fromQuery, toQuery, DIMS } from './store.js';

const rows = [...document.querySelectorAll('#results tbody tr')];
const count = document.getElementById('count');
const search = document.getElementById('q');
const reset = document.getElementById('reset');

// The table is already in the HTML; JS filters it and never builds it, so the
// full 49 rows stay readable with scripting disabled.
const data = rows.map((tr) => ({ slug: tr.dataset.technique, tr }));
let profiles = [];

function readState() {
  const s = {};
  document.querySelectorAll('input[data-facet]:checked').forEach((i) => {
    (s[i.dataset.facet] ||= []).push(i.value);
  });
  if (search.value.trim()) s.q = search.value.trim();
  return s;
}

function apply(push = true) {
  const s = readState();
  const keep = new Set(filter(profiles, s).map((t) => t.slug));
  data.forEach(({ slug, tr }) => { tr.hidden = !keep.has(slug); });
  count.textContent = `${keep.size} of ${data.length} techniques`;
  const q = toQuery(s);
  if (push) history.replaceState(null, '', q ? `?${q}` : location.pathname);
}

function restore() {
  const s = fromQuery(location.search.slice(1));
  for (const key of [...DIMS, 'family']) {
    (s[key] || []).forEach((v) => {
      const el = document.querySelector(`input[data-facet="${key}"][value="${CSS.escape(v)}"]`);
      if (el) { el.checked = true; el.closest('details')?.setAttribute('open', ''); }
    });
  }
  if (s.q) search.value = s.q;
}

fetch(new URL('../data/taxonomy.json', import.meta.url))
  .then((r) => r.json())
  .then((tax) => {
    profiles = tax.techniques;
    restore();
    apply(false);
  });

document.addEventListener('change', (e) => {
  if (e.target.matches('input[data-facet]')) apply();
});
search?.addEventListener('input', () => apply());
reset?.addEventListener('click', () => {
  document.querySelectorAll('input[data-facet]:checked').forEach((i) => (i.checked = false));
  search.value = '';
  apply();
});
