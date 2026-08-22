import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const REPOSITORY_ROOT = path.resolve(ROOT, '..', '..');
const OUTPUT = path.join(ROOT, '.worker-build');
const SKILL_IDS = ['bflabs-agent-readiness', 'geo-content', 'geo-discover', 'geo-measure', 'geo-optimize', 'seo-plan', 'webmcp-enable'];

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
]);

const skills = {};
for (const id of SKILL_IDS) {
  skills[id] = await fs.readFile(id === 'bflabs-agent-readiness'
    ? path.join(REPOSITORY_ROOT, 'SKILL.md')
    : path.join(REPOSITORY_ROOT, 'skills', id, 'SKILL.md'), 'utf8');
}
const skillIndex = {
  $schema: 'https://schemas.agentskills.io/discovery/0.2.0/schema.json',
  skills: Object.entries(skills).map(([name, body]) => ({
    name,
    type: 'skill-md',
    description: name === 'bflabs-agent-readiness'
      ? 'Diagnose a public website and route one evidence-backed next action to the smallest BFLabs child Skill.'
      : `Run the BFLabs ${name} child Skill for its registered evidence-backed intent.`,
    url: `https://readiness.bflabs.cn/skills/${name}`,
    digest: `sha256:${crypto.createHash('sha256').update(body).digest('hex')}`,
  })),
};
await fs.writeFile(path.join(OUTPUT, 'skills.generated.mjs'), `export const SKILL_TEXT = ${JSON.stringify(skills, null, 2)};\nexport const SKILL_INDEX = ${JSON.stringify(skillIndex, null, 2)};\n`);
console.log(`Built Cloudflare Worker sources in ${OUTPUT}`);
