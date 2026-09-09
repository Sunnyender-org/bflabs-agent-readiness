import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { SKILL_IDS, ROOT_SKILL_ID, PUBLIC_SKILL_ORIGIN, listSkillResources, buildSkillPublication } from '../src/skill-resources.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const REPOSITORY_ROOT = path.resolve(ROOT, '..', '..');
const OUTPUT = path.join(ROOT, '.worker-build');

await fs.rm(OUTPUT, { recursive: true, force: true });
await fs.mkdir(OUTPUT, { recursive: true });

const scanner = await fs.readFile(path.join(ROOT, 'src', 'scanner.mjs'), 'utf8');
const workerScanner = scanner.replace("from './safety.mjs';", "from './safety-worker.mjs';");
if (workerScanner === scanner) throw new Error('scanner safety import transform did not apply');

await Promise.all([
  fs.writeFile(path.join(OUTPUT, 'scanner.worker.mjs'), workerScanner),
  fs.copyFile(path.join(ROOT, 'src', 'safety-worker.mjs'), path.join(OUTPUT, 'safety-worker.mjs')),
  fs.copyFile(path.join(ROOT, 'src', 'email-forwarder.mjs'), path.join(OUTPUT, 'email-forwarder.mjs')),
  fs.copyFile(path.join(ROOT, 'src', 'worker-entry.mjs'), path.join(OUTPUT, 'worker-entry.mjs')),
  fs.copyFile(path.join(ROOT, 'src', 'leaderboard.mjs'), path.join(OUTPUT, 'leaderboard.mjs')),
  fs.copyFile(path.join(ROOT, 'src', 'mcp-server.mjs'), path.join(OUTPUT, 'mcp-server.mjs')),
  fs.copyFile(path.join(ROOT, 'src', 'product-contract.mjs'), path.join(OUTPUT, 'product-contract.mjs')),
  fs.copyFile(path.join(ROOT, 'src', 'geo-handoff.mjs'), path.join(OUTPUT, 'geo-handoff.mjs')),
  fs.copyFile(path.join(ROOT, 'src', 'skill-resources.mjs'), path.join(OUTPUT, 'skill-resources.mjs')),
]);

const skillText = {};
for (const id of SKILL_IDS) {
  skillText[id] = await fs.readFile(id === ROOT_SKILL_ID
    ? path.join(REPOSITORY_ROOT, 'SKILL.md')
    : path.join(REPOSITORY_ROOT, 'skills', id, 'SKILL.md'), 'utf8');
}
const { skillIndex, skillResources, resourceManifest } = buildSkillPublication({
  skillText,
  resources: await listSkillResources(REPOSITORY_ROOT),
  publicBase: PUBLIC_SKILL_ORIGIN,
});
await fs.writeFile(
  path.join(OUTPUT, 'skills.generated.mjs'),
  `export const SKILL_TEXT = ${JSON.stringify(skillText, null, 2)};\nexport const SKILL_INDEX = ${JSON.stringify(skillIndex, null, 2)};\nexport const SKILL_RESOURCES = ${JSON.stringify(skillResources, null, 2)};\nexport const RESOURCE_MANIFEST = ${JSON.stringify(resourceManifest, null, 2)};\n`,
);
const resourceCount = Object.values(skillResources).reduce((sum, files) => sum + Object.keys(files).length, 0);
console.log(`Built Cloudflare Worker sources in ${OUTPUT} (${resourceCount} companion resources)`);
