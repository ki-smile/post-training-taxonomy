import { loadStore, separator, containment, profileStrip, escapeHtml, DIMS } from './store.js';

/** Prose for a pair. Only disjoint dimensions separate; containment is named
 *  as containment rather than dressed up as separation. */
export function describeSeparator(sep, nameA, nameB, dimNames = {}) {
  const label = (k) => `${k.toUpperCase()} ${dimNames[k] || ''}`.trim();
  const list = (ks) => ks.map(label).join(', ');
  const out = [];
  out.push(sep.identical.length
    ? `<strong>${escapeHtml(nameA)}</strong> and <strong>${escapeHtml(nameB)}</strong> are identical on ${list(sep.identical)}.`
    : `<strong>${escapeHtml(nameA)}</strong> and <strong>${escapeHtml(nameB)}</strong> share no dimension exactly.`);
  out.push(sep.disjoint.length
    ? `They are separated by ${list(sep.disjoint)}.`
    : 'No dimension separates them — one strictly extends the other.');
  if (sep.overlapping.length) out.push(`They partially overlap on ${list(sep.overlapping)}.`);
  return out.join(' ');
}

const hasDom = typeof document !== 'undefined';
const selA = hasDom ? document.getElementById('sel-a') : null;
const selB = hasDom ? document.getElementById('sel-b') : null;
const out = hasDom ? document.getElementById('compare-out') : null;

if (selA && selB && out) {
  loadStore().then((store) => {
    const names = Object.fromEntries(DIMS.map((d) => [d, store.dims[d].name]));

    const params = new URLSearchParams(location.search);
    const picked = (params.get('t') || '').split(',').filter(Boolean);
    selA.value = picked[0] || 'partft';
    selB.value = picked[1] || 'peft';

    function render() {
      const a = store.bySlug[selA.value];
      const b = store.bySlug[selB.value];
      if (!a || !b) return;
      const sep = separator(a, b);
      const c = containment(a, b);
      const note = c === 'a-in-b'
        ? `<p class="callout">${escapeHtml(b.name)} strictly extends ${escapeHtml(a.name)}.</p>`
        : c === 'b-in-a'
          ? `<p class="callout">${escapeHtml(a.name)} strictly extends ${escapeHtml(b.name)}.</p>`
          : '';
      out.innerHTML = `
        <p class="computed">${describeSeparator(sep, a.name, b.name, names)}</p>
        ${note}
        <div class="grid grid--2">
          <div class="stack"><h3>${escapeHtml(a.name)}</h3>${profileStrip(store, a, { up: '../' })}</div>
          <div class="stack"><h3>${escapeHtml(b.name)}</h3>${profileStrip(store, b, { up: '../' })}</div>
        </div>
        <p class="provenance">Computed from the taxonomy data</p>`;
      history.replaceState(null, '', `?t=${a.slug},${b.slug}`);
    }
    selA.addEventListener('change', render);
    selB.addEventListener('change', render);
    render();
  });
}
