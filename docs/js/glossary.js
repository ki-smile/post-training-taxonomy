const q = document.getElementById('gq');
const rows = [...document.querySelectorAll('.glossary-entry')];
const count = document.getElementById('gcount');

q?.addEventListener('input', () => {
  const needle = q.value.trim().toLowerCase();
  let shown = 0;
  rows.forEach((tr) => {
    const hit = !needle || tr.dataset.term.includes(needle);
    tr.hidden = !hit;
    if (hit) shown += 1;
  });
  count.textContent = `${shown} entr${shown === 1 ? 'y' : 'ies'}`;
});
