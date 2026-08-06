// Shared data and filter layer. Every interactive page reads through this,
// so the filter semantics live here and nowhere else.
//
// Filter semantics: OR within a facet, AND across facets. A technique matches
// a facet if ANY of its values for that dimension is selected — set-valued
// cells are the normal case, not the exception.

import { DATA_BASE } from './config.js';

export const DIMS = ['d1', 'd2', 'd3', 'd4', 'd5', 'd6'];

export async function loadStore(base = DATA_BASE) {
  const names = ['taxonomy.json', 'dimensions.json', 'derived.json',
                 'relations.json', 'glossary.json'];
  const [tax, dims, derived, relations, glossary] = await Promise.all(
    names.map((f) => fetch(base + f).then((r) => r.json()))
  );
  return {
    techniques: tax.techniques,
    meta: tax.meta,
    dims,
    derived,
    relations: relations.relations,
    glossary: glossary.entries,
    bySlug: Object.fromEntries(tax.techniques.map((t) => [t.slug, t])),
  };
}

const hits = (vals, sel) => !sel || !sel.length || vals.some((v) => sel.includes(v));

export function filter(techniques, state) {
  const q = (state.q || '').trim().toLowerCase();
  return techniques.filter(
    (t) =>
      DIMS.every((d) => hits(t[d], state[d])) &&
      (!state.family || !state.family.length || state.family.includes(t.family)) &&
      (!q ||
        `${t.name} ${t.abbrev || ''} ${t.full_name || ''} ${t.definition_verbatim || ''}`
          .toLowerCase()
          .includes(q))
  );
}

// Three states. Only `disjoint` dimensions actually separate a pair; some
// pairs have none, and calling containment "separation" would be wrong.
export function separator(a, b) {
  const out = { identical: [], overlapping: [], disjoint: [] };
  for (const d of DIMS) {
    const A = new Set(a[d]);
    const B = new Set(b[d]);
    const inter = [...A].filter((x) => B.has(x));
    if (A.size === B.size && inter.length === A.size) out.identical.push(d);
    else if (inter.length) out.overlapping.push(d);
    else out.disjoint.push(d);
  }
  return out;
}

// Which of a and b strictly extends the other, if either does.
export function containment(a, b) {
  let aSubset = true;
  let bSubset = true;
  for (const d of DIMS) {
    const A = new Set(a[d]);
    const B = new Set(b[d]);
    if (![...A].every((x) => B.has(x))) aSubset = false;
    if (![...B].every((x) => A.has(x))) bSubset = false;
  }
  if (aSubset && !bSubset) return 'a-in-b';
  if (bSubset && !aSubset) return 'b-in-a';
  return null;
}

/**
 * The wizard's matching rule.
 *
 * D6 hard-filters: the paper endorses model-type-first elimination.
 * D2 and D3 RANK ONLY — they never remove a candidate. Canonical profiles
 * describe the typical case, not the permitted set: the paper's own Table 10
 * documents PEFT applied for Drift Remediation, which is outside PEFT's
 * canonical D2. Hard-filtering on D2 would make that scenario unreachable.
 */
export function matchBands(techniques, state) {
  const feasible = techniques.filter((t) => hits(t.d6, state.d6));
  const canonical = [];
  const byIntent = [];
  for (const t of feasible) {
    const ok = ['d2', 'd3'].every((d) => hits(t[d], state[d]));
    (ok ? canonical : byIntent).push(t);
  }
  return { canonical, byIntent, feasibleCount: feasible.length };
}

export function toQuery(state) {
  const p = new URLSearchParams();
  for (const d of DIMS) if (state[d] && state[d].length) p.set(d, state[d].join(','));
  if (state.family && state.family.length) p.set('family', state.family.join(','));
  if (state.q) p.set('q', state.q);
  return p.toString();
}

export function fromQuery(str) {
  const p = new URLSearchParams(str);
  const s = {};
  for (const d of DIMS) if (p.get(d)) s[d] = p.get(d).split(',');
  if (p.get('family')) s.family = p.get('family').split(',');
  if (p.get('q')) s.q = p.get('q');
  return s;
}

// ---- rendering helpers shared by every page ----

/**
 * The profile strip. Must render identically to the build-time version in
 * scripts/render.py -- values are chip links to their dimension category, so
 * a strip drawn by JS is as navigable as one drawn at build time.
 */
export function profileStrip(store, technique, opts = {}) {
  const outside = new Set(opts.outsideCanonical || []);
  const up = opts.up !== undefined ? opts.up : '';
  const cells = DIMS.map((d) => {
    const values = technique[d].map((slug) => {
      const cat = store.dims[d].categories.find((c) => c.slug === slug);
      const label = cat ? cat.abbr : slug;
      return `<span><a class="chip" data-dim="${d}" ` +
        `href="${up}dimensions/${d}/#${slug}">${escapeHtml(label)}</a></span>`;
    }).join('');
    const cls = outside.has(d) ? ' profile-cell--outside' : '';
    return `<div class="profile-cell${cls}">` +
      `<span class="profile-cell__dim">${d.toUpperCase()}</span>` +
      `<span class="profile-cell__values">${values}</span></div>`;
  }).join('');
  return `<div class="profile-strip${opts.compact ? ' profile-strip--compact' : ''}" ` +
    `role="group" aria-label="Six-dimensional profile">${cells}</div>`;
}

export function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
