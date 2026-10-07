import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';

const workflow = JSON.parse(readFileSync(new URL('../examples/retrieve-tenant-sample.json', import.meta.url), 'utf8'));
const code = workflow.nodes.find((node) => node.type === 'n8n-nodes-base.code').parameters.jsCode;
const source = readFileSync(new URL('../src/tenant_retrieval.js', import.meta.url), 'utf8');

function run(request) {
  const context = { $input: { first: () => ({ json: request }) } };
  // n8n executes Code node text inside a function; mirror that wrapper here.
  return JSON.parse(JSON.stringify(vm.runInNewContext(`(function () {\n${code}\n})()`, context, { timeout: 1000 })[0].json));
}

test('the committed workflow contains the tested source', () => {
  assert.equal(code, source);
});

test('tenant A sees only its published matching documents', () => {
  const result = run({ tenant_id: 'demo-a', query: 'shipping policy' });
  assert.equal(result.status, 'ok');
  assert.deepEqual(result.results.map((document) => document.id), ['A-001']);
});

test('tenant B cannot receive tenant A documents', () => {
  const result = run({ tenant_id: 'demo-b', query: 'shipping policy' });
  assert.deepEqual(result.results.map((document) => document.id), ['B-001']);
});

test('unknown tenant is rejected', () => {
  assert.deepEqual(run({ tenant_id: 'unknown', query: 'shipping' }), {
    status: 'rejected', reason: 'invalid_sample_scope',
  });
});

test('blank and oversized queries are rejected', () => {
  for (const query of ['', '  ', 'a'.repeat(121)]) {
    assert.equal(run({ tenant_id: 'demo-a', query }).status, 'rejected');
  }
});

test('no match returns a bounded empty result', () => {
  const result = run({ tenant_id: 'demo-a', query: 'nonexistent' });
  assert.deepEqual(result.results, []);
});

test('the result is deterministic and read-only', () => {
  const request = { tenant_id: 'demo-a', query: 'returns guide' };
  assert.deepEqual(run(request), run(request));
  assert.deepEqual(request, { tenant_id: 'demo-a', query: 'returns guide' });
});
