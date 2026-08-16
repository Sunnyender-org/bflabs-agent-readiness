import assert from 'node:assert/strict';
import test from 'node:test';
import { normalizeTarget } from '../src/safety-worker.mjs';

test('worker target normalization rejects private-style and literal targets', () => {
  for (const value of ['localhost', 'service.internal', '127.0.0.1', '[::1]', 'https://example.com:8443']) {
    assert.throws(() => normalizeTarget(value));
  }
});

test('worker target normalization keeps only a public origin', () => {
  assert.equal(normalizeTarget('https://Example.com/path?q=secret#fragment').toString(), 'https://example.com/');
});
