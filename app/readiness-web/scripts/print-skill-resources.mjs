import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { listSkillResources, skillHubRepoPath } from '../src/skill-resources.mjs';

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const resources = await listSkillResources(repositoryRoot);
process.stdout.write(`${JSON.stringify(resources.map((entry) => ({
  skillId: entry.skillId,
  path: skillHubRepoPath(entry.skillId, entry.relativePath),
})))}\n`);
