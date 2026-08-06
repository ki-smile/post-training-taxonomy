import { test } from 'node:test';
import assert from 'node:assert';
import { buildOutputs } from '../docs/js/wizard.js';

const LAYER = {
  technique: {
    slug: 'peft', name: 'PEFT (LoRA, adapters)',
    d1: ['parametric-update'],
    d2: ['task-specialization', 'computational-efficiency'],
    d3: ['small-labeled'], d4: ['ad-hoc-permanent'],
    d5: ['partial', 'modular'], d6: ['dl', 'fm', 'llm', 'mllm'],
  },
  instance: {
    d1: ['parametric-update'], d2: ['drift-remediation'],
    d3: ['small-labeled'], d4: ['ad-hoc-permanent'],
    d5: ['modular'], d6: ['llm'],
  },
};

test('records a goal outside the canonical profile rather than rejecting it', () => {
  const o = buildOutputs([LAYER]);
  assert.deepEqual(o.json.layers[0].outside_canonical, ['d2']);
  assert.deepEqual(o.json.layers[0].d2, ['drift-remediation']);
  assert.deepEqual(o.json.layers[0].canonical_reference.d2,
    ['task-specialization', 'computational-efficiency']);
});

test('disclaimer travels inside the pasteable prose', () => {
  const o = buildOutputs([LAYER]);
  assert.ok(/not a regulatory determination/i.test(o.prose));
  assert.ok(/arXiv:/.test(o.prose));
});

test('JSON output carries disclaimer and generator fields', () => {
  const o = buildOutputs([LAYER]);
  assert.ok(o.json.disclaimer && o.json.generator);
});

test("prose uses only the paper's modal verbs", () => {
  const o = buildOutputs([LAYER]);
  assert.ok(!/\b(triggers|constitutes|requires|must)\b/i.test(o.prose));
});

test('layered stacks document each layer separately', () => {
  const o = buildOutputs([LAYER, LAYER]);
  assert.equal(o.json.layers.length, 2);
  assert.ok(/Layer 1/.test(o.prose) && /Layer 2/.test(o.prose));
});

test('a fully canonical instance flags nothing', () => {
  const canon = { technique: LAYER.technique,
    instance: { ...LAYER.instance, d2: ['task-specialization'] } };
  assert.deepEqual(buildOutputs([canon]).json.layers[0].outside_canonical, []);
});
