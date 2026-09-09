import assert from 'node:assert/strict';
import test from 'node:test';
import { contentTypeFor, isSafeRelativePath } from '../src/skill-resources.mjs';

test('isSafeRelativePath rejects traversal, encoded traversal, and disallowed names', () => {
  for (const value of [
    '',
    '../x',
    '/etc/passwd',
    'references/../../SKILL.md',
    '%2e%2e/x',
    'a\\b',
    '.env',
    'references/x.exe',
    'references//foo.md',
    'references/foo.md\0',
    'references/__pycache__/x.md',
    'references/.hidden.md',
  ]) {
    assert.equal(isSafeRelativePath(value), false, value);
  }
});

test('isSafeRelativePath accepts allowlisted companion paths', () => {
  for (const value of [
    'references/root-agent-contract.md',
    'templates/readiness-report.json',
    'examples/measurement-input.json',
    'scripts/verify_site_mcp.py',
    'templates/public-facts.yaml',
    'templates/observations.csv',
  ]) {
    assert.equal(isSafeRelativePath(value), true, value);
  }
});

test('contentTypeFor maps companion suffixes', () => {
  assert.equal(contentTypeFor('references/root-agent-contract.md'), 'text/markdown; charset=utf-8');
  assert.equal(contentTypeFor('templates/readiness-report.json'), 'application/json; charset=utf-8');
  assert.equal(contentTypeFor('templates/observations.csv'), 'text/csv; charset=utf-8');
  assert.equal(contentTypeFor('scripts/verify_site_mcp.py'), 'text/plain; charset=utf-8');
  assert.equal(contentTypeFor('assets/logo.svg'), 'image/svg+xml');
  assert.equal(contentTypeFor('templates/public-facts.yaml'), 'text/yaml; charset=utf-8');
  assert.equal(contentTypeFor('templates/public-facts.yml'), 'text/yaml; charset=utf-8');
});
