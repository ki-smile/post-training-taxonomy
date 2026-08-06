import { test } from 'node:test';
import assert from 'node:assert';
import {
  filter, toQuery, fromQuery, separator, matchBands, containment,
} from '../docs/js/store.js';

const T = [
  { slug: 'peft', name: 'PEFT', family: 'Knowledge Transfer',
    d1: ['parametric-update'],
    d2: ['task-specialization', 'computational-efficiency'],
    d3: ['small-labeled'], d4: ['ad-hoc-permanent'],
    d5: ['partial', 'modular'], d6: ['dl', 'fm', 'llm', 'mllm'] },
  { slug: 'rag', name: 'RAG', family: 'Inference-Time Adaptation',
    d1: ['context-injection'], d2: ['knowledge-update'],
    d3: ['external-corpus'], d4: ['version-persistent'],
    d5: ['input-output-space'], d6: ['llm', 'mllm'] },
  { slug: 'partft', name: 'FT (partial)', family: 'Knowledge Transfer',
    d1: ['parametric-update'], d2: ['task-specialization'],
    d3: ['small-labeled'], d4: ['ad-hoc-permanent'],
    d5: ['partial'], d6: ['dl', 'fm', 'llm', 'mllm'] },
];

test('OR within a facet', () => {
  const r = filter(T, { d2: ['knowledge-update', 'task-specialization'] });
  assert.deepEqual(r.map((x) => x.slug).sort(), ['partft', 'peft', 'rag']);
});

test('AND across facets', () => {
  const r = filter(T, { d1: ['context-injection'], d6: ['llm'] });
  assert.deepEqual(r.map((x) => x.slug), ['rag']);
});

test('set-valued cells match on any member', () => {
  assert.deepEqual(filter(T, { d5: ['modular'] }).map((x) => x.slug), ['peft']);
});

test('empty state returns everything', () => {
  assert.equal(filter(T, {}).length, 3);
});

test('no match returns empty, not everything', () => {
  assert.deepEqual(filter(T, { d6: ['ml'] }), []);
});

test('family facet filters', () => {
  const r = filter(T, { family: ['Inference-Time Adaptation'] });
  assert.deepEqual(r.map((x) => x.slug), ['rag']);
});

test('query round-trips', () => {
  const s = { d6: ['llm'], d2: ['alignment', 'safety'], q: 'lora' };
  assert.deepEqual(fromQuery(toQuery(s)), s);
});

test('separator reports three states; PEFT strictly extends Partial FT', () => {
  const s = separator(T[2], T[0]);
  assert.deepEqual(s.identical.sort(), ['d1', 'd3', 'd4', 'd6']);
  assert.deepEqual(s.overlapping.sort(), ['d2', 'd5']);
  assert.deepEqual(s.disjoint, []);
});

test('containment identifies which technique extends the other', () => {
  assert.equal(containment(T[2], T[0]), 'a-in-b');
  assert.equal(containment(T[0], T[1]), null);
});

test('matchBands never eliminates on D2 — Table 10 uses PEFT for drift remediation', () => {
  const b = matchBands(T, { d6: ['llm'], d2: ['drift-remediation'] });
  const all = [...b.canonical, ...b.byIntent].map((x) => x.slug);
  assert.ok(all.includes('peft'), 'PEFT must remain reachable');
  assert.ok(b.byIntent.some((x) => x.slug === 'peft'));
});

test('matchBands hard-filters on D6 only', () => {
  const b = matchBands(T, { d6: ['ml'] });
  assert.equal(b.canonical.length + b.byIntent.length, 0);
});

test('matchBands bands a canonical goal correctly', () => {
  const b = matchBands(T, { d6: ['llm'], d2: ['task-specialization'] });
  assert.ok(b.canonical.some((x) => x.slug === 'peft'));
  assert.ok(b.byIntent.some((x) => x.slug === 'rag'));
  assert.equal(b.feasibleCount, 3);
});
