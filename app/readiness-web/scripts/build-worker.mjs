import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const REPOSITORY_ROOT = path.resolve(ROOT, '..', '..');
const OUTPUT = path.join(ROOT, '.worker-build');
const SKILL_IDS = ['geo-content', 'geo-discover', 'geo-measure', 'geo-optimize', 'seo-plan', 'webmcp-enable'];

await fs.rm(OUTPUT, { recursive: true, force: true });
await fs.mkdir(OUTPUT, { recursive: true });

const scanner = await fs.readFile(path.join(ROOT, 'src', 'scanner.mjs'), 'utf8');
const workerScanner = scanner.replace("from './safety.mjs';", "from './safety-worker.mjs';");
if (workerScanner === scanner) throw new Error('scanner safety import transform did not apply');

await Promise.all([
  fs.writeFile(path.join(OUTPUT, 'scanner.worker.mjs'), workerScanner),
  fs.copyFile(path.join(ROOT, 'src', 'safety-worker.mjs'), path.join(OUTPUT, 'safety-worker.mjs')),
  fs.copyFile(path.join(ROOT, 'src', 'worker-entry.mjs'), path.join(OUTPUT, 'worker-entry.mjs')),
]);

const skills = {};
for (const id of SKILL_IDS) {
  skills[id] = await fs.readFile(path.join(REPOSITORY_ROOT, 'skills', id, 'SKILL.md'), 'utf8');
}
await fs.writeFile(path.join(OUTPUT, 'skills.generated.mjs'), `export const SKILL_TEXT = ${JSON.stringify(skills, null, 2)};\n`);
console.log(`Built Cloudflare Worker sources in ${OUTPUT}`);
