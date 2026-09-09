import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { ROOT_SKILL_ID, SKILL_IDS, listSkillResources, skillDirectory } from '../src/skill-resources.mjs';

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const PREFIXES = ['references/', 'templates/', 'examples/', 'scripts/'];

function stripLinkTarget(raw) {
  return raw.split('#', 1)[0].split('?', 1)[0].replace(/^\.\//, '');
}

function resolveCompanionPath(fromRelativePath, rawTarget, includeScripts) {
  const target = stripLinkTarget(rawTarget);
  if (!target || /^(https?:|mailto:|#|\/)/i.test(target)) return null;
  const prefixes = includeScripts ? PREFIXES : PREFIXES.filter((item) => item !== 'scripts/');
  if (prefixes.some((prefix) => target.startsWith(prefix))) return target;
  const directory = fromRelativePath.includes('/') ? fromRelativePath.slice(0, fromRelativePath.lastIndexOf('/')) : '';
  const joined = [directory, target].filter(Boolean).join('/');
  const parts = [];
  for (const segment of joined.split('/')) {
    if (segment === '' || segment === '.') continue;
    if (segment === '..') {
      if (!parts.length) return null;
      parts.pop();
      continue;
    }
    parts.push(segment);
  }
  const resolved = parts.join('/');
  return prefixes.some((prefix) => resolved.startsWith(prefix)) ? resolved : null;
}

function extractRequiredPaths(markdown, fromRelativePath, includeScripts) {
  const required = new Set();
  const prefixes = includeScripts ? 'references|templates|examples|scripts' : 'references|templates|examples';
  for (const match of markdown.matchAll(/\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g)) {
    const resolved = resolveCompanionPath(fromRelativePath, match[1], includeScripts);
    if (resolved) required.add(resolved);
  }
  for (const match of markdown.matchAll(new RegExp(`\`((?:${prefixes})/[^\`]+)\``, 'g'))) {
    const resolved = resolveCompanionPath(fromRelativePath, match[1], includeScripts);
    if (resolved) required.add(resolved);
  }
  return required;
}

async function markdownFilesUnder(directory, relativeDir = 'references') {
  let entries;
  try {
    entries = await fs.readdir(directory, { withFileTypes: true });
  } catch (error) {
    if (error && error.code === 'ENOENT') return [];
    throw error;
  }
  const files = [];
  for (const entry of entries) {
    if (entry.name.startsWith('.') || entry.name === '__pycache__') continue;
    const absolutePath = path.join(directory, entry.name);
    const relativePath = `${relativeDir}/${entry.name}`;
    if (entry.isDirectory()) {
      files.push(...await markdownFilesUnder(absolutePath, relativePath));
    } else if (entry.isFile() && entry.name.endsWith('.md')) {
      files.push({ absolutePath, relativePath });
    }
  }
  return files;
}

test('every Skill markdown reference resolves to a served companion resource', async () => {
  const resources = await listSkillResources(repositoryRoot);
  const served = new Map();
  for (const entry of resources) {
    served.set(`${entry.skillId}:${entry.relativePath}`, entry);
  }

  for (const skillId of SKILL_IDS) {
    const skillRoot = skillDirectory(repositoryRoot, skillId);
    const skillMarkdown = await fs.readFile(path.join(skillRoot, 'SKILL.md'), 'utf8');
    const required = extractRequiredPaths(skillMarkdown, 'SKILL.md', true);
    for (const file of await markdownFilesUnder(path.join(skillRoot, 'references'))) {
      const markdown = await fs.readFile(file.absolutePath, 'utf8');
      for (const item of extractRequiredPaths(markdown, file.relativePath, skillId !== ROOT_SKILL_ID)) {
        required.add(item);
      }
    }
    const missing = [...required].filter((relativePath) => !served.has(`${skillId}:${relativePath}`));
    assert.deepEqual(missing, [], `${skillId} missing ${missing.join(', ')}`);
  }
});
