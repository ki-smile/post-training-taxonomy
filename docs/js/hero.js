// The hero's one job: show that a common phrase resolves to a coordinate.
//
// Deliberately user-driven rather than a carousel. An auto-cycling hero is
// motion for its own sake; letting someone pick the phrase makes the point
// once, on their terms, and leaves the page still.

import { loadStore, profileStrip, escapeHtml, DIMS } from './store.js';

const hero = document.getElementById('hero');
if (hero) {
  const stripBox = document.getElementById('hero-strip');
  const caption = document.getElementById('hero-caption');
  const tabs = [...hero.querySelectorAll('.hero__tab')];
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

  const NOTE = {
    peft: 'one of six readings of “fine-tuned”',
    rag: 'nothing here says how the corpus is maintained',
    icl: 'no weights change, and nothing is versioned',
  };

  loadStore().then((store) => {
    // Reveal the cells left to right once, so the coordinate assembles
    // rather than simply appearing.
    function paint(slug, animate) {
      const t = store.bySlug[slug];
      if (!t) return;
      stripBox.innerHTML = profileStrip(store, t);
      caption.innerHTML =
        `<a href="techniques/${t.slug}/">${escapeHtml(t.name)}</a> — ${NOTE[slug] || ''}.`;
      if (animate && !reduced) {
        stripBox.querySelectorAll('.profile-cell').forEach((cell, i) => {
          cell.style.animation = 'hero-cell 260ms both';
          cell.style.animationDelay = `${i * 45}ms`;
        });
      }
    }

    tabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        tabs.forEach((t) => t.setAttribute('aria-selected', String(t === tab)));
        paint(tab.dataset.slug, true);
      });
    });

    paint('peft', true);
  });
}
