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
    'schemas/round-experiment.schema.json',
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


test('diagnostic download names the same version as the package builder', async () => {
  const fs = await import('node:fs/promises');
  const pkg = JSON.parse(await fs.readFile(new URL('../package.json', import.meta.url), 'utf8'));
  const html = await fs.readFile(new URL('../public/index.html', import.meta.url), 'utf8');
  const init = await fs.readFile(new URL('../../../src/bflabs_readiness/__init__.py', import.meta.url), 'utf8');
  assert.ok(init.includes(`"${pkg.version}"`));
  assert.ok(html.includes(`/downloads/bflabs-agent-readiness-skillhub-${pkg.version}.zip`));
});
