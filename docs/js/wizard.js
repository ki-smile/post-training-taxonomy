import { loadStore, matchBands, profileStrip, escapeHtml, DIMS } from './store.js';
import { ARXIV_ID, SITE_URL, TAX_VERSION } from './config.js';

const DISCLAIMER =
  'Technical specification vocabulary, not a regulatory determination.';

/**
 * Build the three outputs.
 *
 * A layer's `instance` values may legitimately fall outside the technique's
 * canonical profile — the paper's own worked example applies PEFT for drift
 * remediation, which is outside PEFT's canonical goal. Those dimensions are
 * recorded and marked, never rejected.
 */
export function buildOutputs(layers) {
  const json = {
    generator: `${SITE_URL}wizard/`,
    taxonomy_version: TAX_VERSION,
    layers: layers.map((l) => {
      const outside = DIMS.filter(
        (d) => l.technique[d] && !l.instance[d].every((v) => l.technique[d].includes(v))
      );
      const row = {
        technique_slug: l.technique.slug,
        technique_name: l.technique.name,
        ...Object.fromEntries(DIMS.map((d) => [d, l.instance[d]])),
        outside_canonical: outside,
      };
      if (outside.length) {
        row.canonical_reference = Object.fromEntries(
          outside.map((d) => [d, l.technique[d]])
        );
      }
      return row;
    }),
    citation: ARXIV_ID,
    disclaimer: DISCLAIMER,
  };

  const prose = layers.map((l, i) => {
    const outside = json.layers[i].outside_canonical;
    const vals = (d) => l.instance[d].join(', ');
    const flag = outside.length
      ? ` This layer's ${outside.map((d) => d.toUpperCase()).join(' and ')} ` +
        `falls outside the technique's canonical profile, which the taxonomy ` +
        `permits where engineering intent differs.`
      : '';
    return `Layer ${i + 1} — ${l.technique.name}. ` +
      `Mechanism: ${vals('d1')}. Goal: ${vals('d2')}. Data: ${vals('d3')}. ` +
      `Persistence: ${vals('d4')}. Scope: ${vals('d5')}. Model type: ${vals('d6')}.` +
      flag;
  }).join('\n\n') +
    `\n\nProfile vocabulary from ${ARXIV_ID}. ${DISCLAIMER}`;

  const tuple = layers.map((l) =>
    `(${DIMS.map((d) => `${d}=${l.instance[d].join('|')}`).join(', ')})`
  ).join(' ⊕ ');

  return { tuple, prose, json };
}

const results =
  typeof document === 'undefined' ? null : document.getElementById('wizard-results');
if (results) {
  loadStore().then((store) => {
    const count = document.getElementById('wizard-count');
    const outBox = document.getElementById('wizard-output');

    function state() {
      const s = {};
      for (const k of ['d6', 'd2', 'd3']) {
        const el = document.querySelector(`input[name="${k}"]:checked`);
        if (el) s[k] = [el.value];
      }
      return s;
    }

    function card(t, band) {
      return `<div class="card stack">
        <p class="eyebrow">${band}</p>
        <h3><a href="../techniques/${t.slug}/">${escapeHtml(t.name)}</a></h3>
        <p>${escapeHtml(t.summary_editorial)}</p>
        ${profileStrip(store, t, { compact: true, up: '../' })}
        <button class="btn" data-pick="${t.slug}" type="button">Use this</button>
      </div>`;
    }

    function render() {
      const s = state();
      if (!s.d6) {
        count.textContent = 'Choose a model type to begin.';
        results.innerHTML = '';
        return;
      }
      const b = matchBands(store.techniques, s);
      count.textContent =
        `${b.feasibleCount} techniques for ${s.d6[0].toUpperCase()} · ` +
        `${b.canonical.length} canonical match${b.canonical.length === 1 ? '' : 'es'}`;
      results.innerHTML = `
        <div class="grid grid--2">
          ${b.canonical.map((t) => card(t, 'Canonical match')).join('')}
        </div>
        ${b.byIntent.length ? `<details class="stack"><summary>
          ${b.byIntent.length} more applicable by engineering intent</summary>
          <p class="callout">Canonical profiles describe the typical case, not
          the permitted set. Flexible techniques can serve goals outside their
          usual profile when engineered to.</p>
          <div class="grid grid--2">
            ${b.byIntent.map((t) => card(t, 'Applicable by intent')).join('')}
          </div></details>` : ''}`;
    }

    document.addEventListener('change', (e) => {
      if (e.target.matches('input[name="d6"],input[name="d2"],input[name="d3"]')) render();
    });

    document.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-pick]');
      if (!btn) return;
      const t = store.bySlug[btn.dataset.pick];
      const s = state();
      const instance = Object.fromEntries(
        DIMS.map((d) => [d, s[d] ? s[d] : [t[d][0]]])
      );
      const out = buildOutputs([{ technique: t, instance }]);
      const outside = out.json.layers[0].outside_canonical;
      document.getElementById('wizard-profile').innerHTML =
        profileStrip(store, { ...t, ...instance },
          { outsideCanonical: outside, up: '../' }) +
        (outside.length
          ? `<p class="provenance">Dashed cells fall outside ${escapeHtml(t.name)}'s canonical profile</p>`
          : '');
      document.getElementById('wizard-prose').textContent = out.prose;
      document.getElementById('wizard-json').textContent =
        JSON.stringify(out.json, null, 2);
      outBox.hidden = false;
      outBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    render();
  });
}
