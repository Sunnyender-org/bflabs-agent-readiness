import crypto from 'node:crypto';
import path from 'node:path';

export const SKILL_IDS = [
  'bflabs-agent-readiness',
  'geo-content',
  'geo-discover',
  'geo-measure',
  'geo-optimize',
  'seo-plan',
  'webmcp-enable',
];

export const ROOT_SKILL_ID = 'bflabs-agent-readiness';
export const SKILLHUB_ALLOWED_SUFFIXES = new Set(['.csv', '.json', '.md', '.py', '.svg', '.yaml', '.yml']);
export const ROOT_RESOURCE_DIRS = ['references', 'templates', 'schemas'];
export const CHILD_RESOURCE_DIRS = ['references', 'templates', 'examples', 'scripts'];
export const MAX_EMBEDDED_RESOURCE_BYTES = 2 * 1024 * 1024;
export const PUBLIC_SKILL_ORIGIN = 'https://readiness.bflabs.cn';

const CONTENT_TYPES = {
  '.md': 'text/markdown; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.csv': 'text/csv; charset=utf-8',
  '.py': 'text/plain; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.yaml': 'text/yaml; charset=utf-8',
  '.yml': 'text/yaml; charset=utf-8',
};

function suffixOf(relativePath) {
  const base = relativePath.split('/').pop() || '';
  const dot = base.lastIndexOf('.');
  return dot > 0 ? base.slice(dot).toLowerCase() : '';
}

function sha256Hex(buffer) {
  return crypto.createHash('sha256').update(buffer).digest('hex');
}

export function skillDirectory(repositoryRoot, skillId) {
  return skillId === ROOT_SKILL_ID ? repositoryRoot : path.join(repositoryRoot, 'skills', skillId);
}

export function skillHubRepoPath(skillId, relativePath) {
  return skillId === ROOT_SKILL_ID ? relativePath : `skills/${skillId}/${relativePath}`;
}

export function readFrontMatterVersion(skillMarkdown) {
  const match = String(skillMarkdown).match(/^version:\s*(\S+)/m);
  if (!match) throw new Error('SKILL.md is missing a version: front-matter field');
  return match[1];
}

export function isSafeRelativePath(relativePath) {
  if (typeof relativePath !== 'string' || relativePath === '') return false;
  if (relativePath.includes('\0') || relativePath.includes('\\') || relativePath.includes('//')) return false;
  if (relativePath.startsWith('/')) return false;

  let decoded = relativePath;
  try {
    decoded = decodeURIComponent(relativePath);
  } catch {
    return false;
  }
  if (decoded.includes('\0') || decoded.includes('\\') || decoded.includes('//')) return false;
  if (decoded.startsWith('/') || decoded === '') return false;

  const segments = decoded.split('/');
  if (segments.some((segment) => segment === '' || segment === '.' || segment === '..' || segment.startsWith('.') || segment === '__pycache__')) {
    return false;
  }
  return SKILLHUB_ALLOWED_SUFFIXES.has(suffixOf(decoded));
}

export function contentTypeFor(relativePath) {
  return CONTENT_TYPES[suffixOf(relativePath)] || 'application/octet-stream';
}

async function walkResourceDir(fs, absoluteDir, relativeDir, visit) {
  let entries;
  try {
    entries = await fs.readdir(absoluteDir, { withFileTypes: true });
  } catch (error) {
    if (error && error.code === 'ENOENT') return;
    throw error;
  }
  entries.sort((left, right) => left.name.localeCompare(right.name));
  for (const entry of entries) {
    if (entry.name.startsWith('.') || entry.name === '__pycache__' || entry.isSymbolicLink()) continue;
    const relativePath = `${relativeDir}/${entry.name}`;
    const absolutePath = path.join(absoluteDir, entry.name);
    if (entry.isDirectory()) {
      await walkResourceDir(fs, absolutePath, relativePath, visit);
      continue;
    }
    if (!entry.isFile()) continue;
    if (!SKILLHUB_ALLOWED_SUFFIXES.has(path.extname(entry.name).toLowerCase())) continue;
    await visit(relativePath, absolutePath);
  }
}

export async function listSkillResources(repositoryRoot) {
  const fs = await import('node:fs/promises');
  const resources = [];
  let totalBytes = 0;
  for (const skillId of SKILL_IDS) {
    const dirs = skillId === ROOT_SKILL_ID ? ROOT_RESOURCE_DIRS : CHILD_RESOURCE_DIRS;
    const skillRoot = skillDirectory(repositoryRoot, skillId);
    for (const dir of dirs) {
      await walkResourceDir(fs, path.join(skillRoot, dir), dir, async (relativePath, absolutePath) => {
        if (!isSafeRelativePath(relativePath)) return;
        const buffer = await fs.readFile(absolutePath);
        totalBytes += buffer.byteLength;
        resources.push({
          skillId,
          relativePath,
          bytes: buffer.byteLength,
          sha256: sha256Hex(buffer),
          body: buffer.toString('utf8'),
        });
      });
    }
  }
  for (const [relativePath, sourcePath] of [
    ['scripts/analyze_business.py', 'scripts/analyze_business.py'],
    ['scripts/business_attribution.py', 'src/bflabs_readiness/business_attribution.py'],
    ['scripts/business_report.py', 'src/bflabs_readiness/business_report.py'],
  ]) {
    const buffer = await fs.readFile(path.join(repositoryRoot, sourcePath));
    totalBytes += buffer.byteLength;
    resources.push({ skillId: ROOT_SKILL_ID, relativePath, bytes: buffer.byteLength,
      sha256: sha256Hex(buffer), body: buffer.toString('utf8') });
  }
  if (totalBytes > MAX_EMBEDDED_RESOURCE_BYTES) {
    throw new Error(`Embedded Skill resources exceed 2 MiB (${totalBytes} bytes)`);
  }
  resources.sort((left, right) => left.skillId.localeCompare(right.skillId) || left.relativePath.localeCompare(right.relativePath));
  return resources;
}

export function skillDescription(skillId) {
  return skillId === ROOT_SKILL_ID
    ? 'Diagnose a public website and route one evidence-backed next action to the smallest BFLabs child Skill.'
    : `Run the BFLabs ${skillId} child Skill for its registered evidence-backed intent.`;
}

export function buildSkillPublication({ skillText, resources, publicBase }) {
  const skillResources = {};
  const skills = {};
  for (const skillId of SKILL_IDS) {
    skillResources[skillId] = {};
    const body = skillText[skillId];
    if (typeof body !== 'string') throw new Error(`missing SKILL.md text for ${skillId}`);
    skills[skillId] = {
      url: `${publicBase}/skills/${skillId}`,
      digest: `sha256:${sha256Hex(body)}`,
      resources: [],
    };
  }
  for (const entry of resources) {
    if (!skillResources[entry.skillId]) continue;
    skillResources[entry.skillId][entry.relativePath] = {
      body: entry.body,
      sha256: entry.sha256,
      bytes: entry.bytes,
      contentType: contentTypeFor(entry.relativePath),
    };
    skills[entry.skillId].resources.push({
      path: entry.relativePath,
      url: `${publicBase}/skills/${entry.skillId}/${entry.relativePath}`,
      sha256: entry.sha256,
      bytes: entry.bytes,
    });
  }
  for (const skillId of SKILL_IDS) {
    skills[skillId].resources.sort((left, right) => left.path.localeCompare(right.path));
  }
  return {
    skillResources,
    resourceManifest: {
      version: readFrontMatterVersion(skillText[ROOT_SKILL_ID]),
      skills,
    },
    skillIndex: {
      $schema: 'https://schemas.agentskills.io/discovery/0.2.0/schema.json',
      skills: SKILL_IDS.map((name) => ({
        name,
        type: 'skill-md',
        description: skillDescription(name),
        url: `${publicBase}/skills/${name}`,
        digest: skills[name].digest,
        resources_url: `${publicBase}/skills/${name}/manifest.json`,
      })),
    },
  };
}

export function parseSkillsPathname(pathname) {
  if (typeof pathname !== 'string' || !pathname.startsWith('/skills/')) return null;
  const remainder = pathname.slice('/skills/'.length);
  if (remainder === '') return { type: 'skill', skillId: '' };
  const slash = remainder.indexOf('/');
  const rawId = slash === -1 ? remainder : remainder.slice(0, slash);
  const rawRest = slash === -1 ? null : remainder.slice(slash + 1);
  let skillId;
  try {
    skillId = decodeURIComponent(rawId);
  } catch {
    return { type: 'unsafe' };
  }
  if (rawRest === null || rawRest === '') return { type: 'skill', skillId };
  let relativePath;
  try {
    relativePath = decodeURIComponent(rawRest);
  } catch {
    return { type: 'unsafe', skillId };
  }
  if (relativePath === 'manifest.json') return { type: 'manifest', skillId };
  return { type: 'resource', skillId, relativePath };
}

function etagMatches(ifNoneMatch, etag) {
  if (!ifNoneMatch) return false;
  return ifNoneMatch.split(',').some((part) => {
    const candidate = part.trim();
    return candidate === '*' || candidate === etag || candidate === `W/${etag}`;
  });
}

function jsonResponse(value, status, headers = {}, method = 'GET') {
  return new Response(method === 'HEAD' ? null : JSON.stringify(value), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
      'x-content-type-options': 'nosniff',
      ...headers,
    },
  });
}

export function handleSkillRoute(request, { skillText, skillResources, resourceManifest, skillTextCacheControl }) {
  const method = request.method || 'GET';
  if (method !== 'GET' && method !== 'HEAD') return null;
  const url = new URL(request.url, PUBLIC_SKILL_ORIGIN);
  const pathname = request.pathname || url.pathname;
  if (!pathname.startsWith('/skills/')) return null;

  const parsed = parseSkillsPathname(pathname);
  if (!parsed) return jsonResponse({ error: '资源不存在' }, 404, {}, method);

  if (parsed.type === 'skill') {
    const body = skillText[parsed.skillId];
    if (body == null) return jsonResponse({ error: '未知子 Skill' }, 404, {}, method);
    const headers = {
      'content-type': 'text/plain; charset=utf-8',
      'x-content-type-options': 'nosniff',
      link: `<${PUBLIC_SKILL_ORIGIN}/skills/${parsed.skillId}/manifest.json>; rel="describedby"`,
    };
    if (skillTextCacheControl) headers['cache-control'] = skillTextCacheControl;
    return new Response(method === 'HEAD' ? null : body, { headers });
  }

  if (parsed.type === 'unsafe' || !resourceManifest.skills[parsed.skillId]) {
    return jsonResponse({ error: '资源不存在' }, 404, {}, method);
  }

  if (parsed.type === 'manifest') {
    return jsonResponse({
      version: resourceManifest.version,
      ...resourceManifest.skills[parsed.skillId],
    }, 200, { 'cache-control': 'public, max-age=300' }, method);
  }

  if (!isSafeRelativePath(parsed.relativePath)) {
    return jsonResponse({ error: '资源不存在' }, 404, {}, method);
  }
  const resource = skillResources[parsed.skillId]?.[parsed.relativePath];
  if (!resource) return jsonResponse({ error: '资源不存在' }, 404, {}, method);

  const etag = `"${resource.sha256}"`;
  const headers = {
    'content-type': resource.contentType,
    'x-content-type-options': 'nosniff',
    'cache-control': 'public, max-age=300',
    etag,
  };
  if (etagMatches(request.headers?.get?.('if-none-match'), etag)) {
    return new Response(null, { status: 304, headers });
  }
  return new Response(method === 'HEAD' ? null : resource.body, { status: 200, headers });
}
