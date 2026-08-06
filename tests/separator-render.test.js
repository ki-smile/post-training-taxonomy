import { test } from 'node:test';
import assert from 'node:assert';
import { describeSeparator } from '../docs/js/compare.js';

test('describes containment without claiming separation', () => {
  const s = { identical: ['d1', 'd3', 'd4', 'd6'], overlapping: ['d2', 'd5'], disjoint: [] };
  const txt = describeSeparator(s, 'FT (partial)', 'PEFT');
  assert.ok(!/separated by/i.test(txt));
  assert.ok(/strictly extends/i.test(txt));
});

test('names only disjoint dimensions as separating', () => {
  const s = { identical: ['d1', 'd4', 'd5', 'd6'], overlapping: [], disjoint: ['d2', 'd3'] };
  const txt = describeSeparator(s, 'Training', 'Retraining');
  assert.ok(/separated by/i.test(txt));
  assert.ok(/D2/.test(txt) && /D3/.test(txt));
});

test('reports when no dimension is identical', () => {
  const s = { identical: [], overlapping: ['d2'], disjoint: ['d1', 'd4'] };
  const txt = describeSeparator(s, 'FSL', 'ICL');
  assert.ok(/share no dimension exactly/i.test(txt));
});
