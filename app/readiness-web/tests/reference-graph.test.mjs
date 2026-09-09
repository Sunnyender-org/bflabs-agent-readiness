import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import {
  PUBLIC_SKILL_ORIGIN,
  ROOT_SKILL_ID,
  SKILL_IDS,
  buildSkillPublication,
  handleSkillRoute,
  listSkillResources,
  parseSkillsPathname,
  skillDirectory,
} from '../src/skill-resources.mjs';

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

const GRAPH_PREFIXES = ['references/', 'templates/', 'examples/', 'scripts/', 'schemas/'];
const GRAPH_DEPTH_LIMIT = 8;

async function loadPublication() {
  const skillText = Object.fromEntries(await Promise.all(SKILL_IDS.map(async (id) => {
    const file = id === ROOT_SKILL_ID
      ? path.join(repositoryRoot, 'SKILL.md')
      : path.join(repositoryRoot, 'skills', id, 'SKILL.md');
    return [id, await fs.readFile(file, 'utf8')];
  })));
  return {
    skillText,
    ...buildSkillPublication({
      skillText,
      resources: await listSkillResources(repositoryRoot),
      publicBase: PUBLIC_SKILL_ORIGIN,
    }),
  };
}

function startPromptUrl(skillMarkdown) {
  const fence = skillMarkdown.match(/```\n([\s\S]*?)\n```/);
  assert.ok(fence, 'root SKILL.md is missing the start prompt fence');
  const match = fence[1].match(/https:\/\/readiness\.bflabs\.cn\/skills\/[A-Za-z0-9-]+/);
  assert.ok(match, 'start prompt fence has no Skill URL');
  return match[0];
}

function stripGraphTarget(raw) {
  return String(raw || '').split('#', 1)[0].split('?', 1)[0].replace(/[.,;:]+$/, '');
}

function extractGraphHrefs(markdown) {
  const hrefs = [];
  const seen = new Set();
  const add = (value) => {
    const clean = stripGraphTarget(value);
    if (!clean || seen.has(clean)) return;
    seen.add(clean);
    hrefs.push(clean);
  };
  for (const match of markdown.matchAll(/<!--\s*AGENT_ONLY:([\s\S]*?)-->/g)) {
    for (const url of match[1].matchAll(/https?:\/\/[^\s<>"'`]+/g)) {
      add(url[0]);
    }
  }
  for (const match of markdown.matchAll(/\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g)) {
    add(match[1]);
  }
  for (const match of markdown.matchAll(/`((?:references|templates|examples|scripts|schemas)\/[^`]+)`/g)) {
    add(match[1]);
  }
  return hrefs;
}

function skillCollectionUrl(responseUrl) {
  const url = new URL(responseUrl);
  const match = url.pathname.match(/^(\/skills\/[^/]+)/);
  if (!match) return null;
  return new URL(`${match[1]}/`, url.origin);
}

function resolveGraphHref(href, responseUrl) {
  const target = stripGraphTarget(href);
  if (!target || /^(mailto:|#)/i.test(target)) return null;
  try {
    if (/^[a-z][a-z0-9+.-]*:/i.test(target)) {
      return new URL(target, responseUrl);
    }
    if (GRAPH_PREFIXES.some((prefix) => target.startsWith(prefix))) {
      const collection = target.startsWith('schemas/')
        ? new URL(`/skills/${ROOT_SKILL_ID}/`, PUBLIC_SKILL_ORIGIN)
        : skillCollectionUrl(responseUrl);
      return new URL(target, collection || responseUrl);
    }
    return new URL(target, responseUrl);
  } catch {
    return null;
  }
}

function expandGlobUrl(url, publication) {
  const parsed = parseSkillsPathname(url.pathname);
  if (!parsed || parsed.type !== 'resource' || !parsed.relativePath.includes('*')) {
    return [url];
  }
  const escaped = parsed.relativePath.replace(/[.+?^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '[^/]*');
  const matcher = new RegExp(`^${escaped}$`);
  const resources = publication.resourceManifest.skills[parsed.skillId]?.resources || [];
  const matches = resources.filter((item) => matcher.test(item.path)).map((item) => new URL(item.url));
  return matches.length ? matches : [url];
}

function requestPublication(publication, href) {
  return handleSkillRoute(new Request(href), publication);
}

test('start-prompt first hop follows the live reference graph without pre-assembled paths', async () => {
  const publication = await loadPublication();
  const startUrl = startPromptUrl(publication.skillText[ROOT_SKILL_ID]);
  assert.equal(startUrl, `${PUBLIC_SKILL_ORIGIN}/skills/${ROOT_SKILL_ID}`);

  const startResponse = requestPublication(publication, startUrl);
  assert.equal(startResponse.status, 200, startUrl);
  const startBody = await startResponse.text();

  const contractUrl = startBody.match(/https:\/\/readiness\.bflabs\.cn\/skills\/bflabs-agent-readiness\/references\/root-agent-contract\.md/);
  assert.ok(contractUrl, 'start body AGENT_ONLY comment must name the absolute contract URL');
  const firstHop = new URL(contractUrl[0], startUrl);
  assert.equal(firstHop.href, `${PUBLIC_SKILL_ORIGIN}/skills/${ROOT_SKILL_ID}/references/root-agent-contract.md`);
  const firstHopResponse = requestPublication(publication, firstHop.href);
  assert.equal(firstHopResponse.status, 200, firstHop.href);

  const visited = new Set();
  const queue = [{ url: startUrl, body: startBody, depth: 0 }];
  let sawRoundSchema = false;

  while (queue.length) {
    const current = queue.shift();
    if (visited.has(current.url) || current.depth > GRAPH_DEPTH_LIMIT) continue;
    visited.add(current.url);

    let body = current.body;
    if (body == null) {
      const response = requestPublication(publication, current.url);
      assert.equal(response.status, 200, `first non-200: ${current.url} -> ${response.status}`);
      const contentType = response.headers.get('content-type') || '';
      if (!contentType.includes('markdown') && !contentType.includes('text/plain')) continue;
      body = await response.text();
    }

    for (const href of extractGraphHrefs(body)) {
      const resolved = resolveGraphHref(href, current.url);
      if (!resolved || resolved.origin !== PUBLIC_SKILL_ORIGIN) continue;
      if (!resolved.pathname.startsWith('/skills/')) continue;
      for (const next of expandGlobUrl(resolved, publication)) {
        if (visited.has(next.href) || queue.some((item) => item.url === next.href)) continue;
        const response = requestPublication(publication, next.href);
        assert.ok(response, `first non-200: ${next.href} -> no skill route`);
        assert.equal(response.status, 200, `first non-200: ${next.href} -> ${response.status}`);
        if (next.pathname.includes('/schemas/round-') && next.pathname.endsWith('.schema.json')) {
          sawRoundSchema = true;
        }
        const contentType = response.headers.get('content-type') || '';
        const isMarkdown = contentType.includes('markdown') || (contentType.includes('text/plain') && next.pathname.split('/').length === 3);
        if (isMarkdown && current.depth + 1 <= GRAPH_DEPTH_LIMIT) {
          queue.push({ url: next.href, body: await response.text(), depth: current.depth + 1 });
        }
      }
    }
  }

  assert.equal(visited.has(firstHop.href), true, 'graph must reach the root Agent contract');
  assert.equal(sawRoundSchema, true, 'graph must reach a schemas/round-*.schema.json resource');
});
