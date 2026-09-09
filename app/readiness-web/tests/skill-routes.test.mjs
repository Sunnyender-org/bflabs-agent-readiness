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
} from '../src/skill-resources.mjs';

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..');

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

function route(publication, pathAndQuery, headers = {}, method = 'GET') {
  return handleSkillRoute(new Request(`${PUBLIC_SKILL_ORIGIN}${pathAndQuery}`, { method, headers }), publication);
}

test('skill companion routes serve manifest, hashed body, 304, and honest 404s', async () => {
  const publication = await loadPublication();
  const resourcePath = 'references/root-agent-contract.md';
  const resource = publication.skillResources[ROOT_SKILL_ID][resourcePath];
  assert.ok(resource);

  const skill = route(publication, `/skills/${ROOT_SKILL_ID}`);
  assert.equal(skill.status, 200);
  assert.equal(skill.headers.get('content-type'), 'text/plain; charset=utf-8');
  assert.match(await skill.text(), /bflabs-agent-readiness/);
  assert.equal(skill.headers.get('cache-control'), null);

  const unknownSkill = route(publication, '/skills/not-a-skill');
  assert.equal(unknownSkill.status, 404);
  assert.deepEqual(await unknownSkill.json(), { error: '未知子 Skill' });

  const manifest = route(publication, `/skills/${ROOT_SKILL_ID}/manifest.json`);
  assert.equal(manifest.status, 200);
  assert.equal(manifest.headers.get('cache-control'), 'public, max-age=300');
  const body = await manifest.json();
  assert.equal(body.version, publication.resourceManifest.version);
  assert.equal(body.digest, publication.resourceManifest.skills[ROOT_SKILL_ID].digest);
  assert.equal(body.resources.some((item) => item.path === resourcePath), true);
  assert.equal(publication.skillIndex.skills[0].resources_url, `${PUBLIC_SKILL_ORIGIN}/skills/${ROOT_SKILL_ID}/manifest.json`);

  const file = route(publication, `/skills/${ROOT_SKILL_ID}/${resourcePath}`);
  assert.equal(file.status, 200);
  assert.equal(file.headers.get('content-type'), 'text/markdown; charset=utf-8');
  assert.equal(file.headers.get('x-content-type-options'), 'nosniff');
  assert.equal(file.headers.get('cache-control'), 'public, max-age=300');
  assert.equal(file.headers.get('etag'), `"${resource.sha256}"`);
  assert.match(await file.text(), /Root Agent Contract/);

  const cached = route(publication, `/skills/${ROOT_SKILL_ID}/${resourcePath}`, { 'if-none-match': `"${resource.sha256}"` });
  assert.equal(cached.status, 304);
  assert.equal(cached.headers.get('etag'), `"${resource.sha256}"`);
  assert.equal(await cached.text(), '');

  const traversal = route(publication, `/skills/${ROOT_SKILL_ID}/references%2F..%2F..%2FSKILL.md`);
  assert.equal(traversal.status, 404);
  assert.deepEqual(await traversal.json(), { error: '资源不存在' });

  const missing = route(publication, `/skills/${ROOT_SKILL_ID}/references/not-a-real-file.md`);
  assert.equal(missing.status, 404);
  assert.deepEqual(await missing.json(), { error: '资源不存在' });

  const unknownNested = route(publication, '/skills/not-a-skill/manifest.json');
  assert.equal(unknownNested.status, 404);
  assert.deepEqual(await unknownNested.json(), { error: '资源不存在' });
});
