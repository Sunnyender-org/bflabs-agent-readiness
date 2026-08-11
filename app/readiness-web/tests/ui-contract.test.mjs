import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const html = fs.readFileSync(path.join(root, 'public/index.html'), 'utf8');
const css = fs.readFileSync(path.join(root, 'public/styles.css'), 'utf8');
const app = fs.readFileSync(path.join(root, 'public/app.js'), 'utf8');

test('uses the committed BFLabs Grok prototype as the formal web shell', () => {
  assert.match(html, /BF LABS/);
  assert.match(html, /你的网站，AI 读得懂吗？/);
  assert.match(html, /报告/);
  assert.match(html, /交付示例/);
  assert.doesNotMatch(html, /别先问 AI 会不会推荐你/);
  assert.doesNotMatch(css, /Iowan Old Style|folio/);
});

test('keeps the real scanner and protocol actions wired into the visual shell', () => {
  for (const id of [
    'scan-form',
    'axis-rail',
    'findings',
    'evidence-body',
    'download-report',
    'copy-agent-prompt',
    'skill-routes',
  ]) {
    assert.match(html, new RegExp(`id="${id}"`));
    assert.match(app, new RegExp(`#${id}`));
  }
});
