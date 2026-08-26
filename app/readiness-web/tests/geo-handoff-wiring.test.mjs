import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), 'utf8');

test('worker and local server attach handoffs to scans and expose redeem only', () => {
  const server = read('src/server.mjs');
  const worker = read('src/worker-entry.mjs');
  for (const source of [server, worker]) {
    assert.match(source, /handleGeoHandoffRequest/);
    assert.match(source, /createD1GeoHandoffStore|createMemoryGeoHandoffStore/);
    assert.match(source, /attachGeoHandoff/);
    assert.match(source, /prepare_workbuddy_handoff/);
    assert.doesNotMatch(source, /url\.pathname === '\/api\/v1\/geo-handoffs'\s*\|\|/);
  }
});

test('Cloudflare config and migration provide bounded D1 handoff storage', () => {
  const config = read('wrangler.jsonc');
  const migration = read('migrations/0001_geo_handoffs.sql');
  assert.match(config, /"binding": "GEO_HANDOFFS"/);
  assert.match(config, /"migrations_dir": "migrations"/);
  assert.match(migration, /CREATE TABLE geo_handoffs/);
  assert.match(migration, /token_hash TEXT PRIMARY KEY/);
  assert.match(migration, /receipt_json TEXT NOT NULL/);
  assert.match(migration, /consumed_at INTEGER/);
});

test('worker build includes the GEO handoff implementation', () => {
  assert.match(read('scripts/build-worker.mjs'), /geo-handoff\.mjs/);
});

test('OpenAPI prepares handoff during scan and publishes redeem only', () => {
  const openapi = JSON.parse(read('public/openapi.json'));
  assert.equal(openapi.paths['/api/v1/geo-handoffs'], undefined);
  assert.ok(openapi.paths['/api/v1/geo-handoffs/redeem']?.post);
  assert.equal(openapi.paths['/api/v1/scans'].post.requestBody.content['application/json'].schema.properties.prepare_workbuddy_handoff.type, 'boolean');
  assert.equal(openapi.components.schemas.GeoHandoffIssue.properties.schema_version.const, 'bflabs.geo-handoff-issue/1.0.0');
  assert.equal(openapi.components.schemas.GeoHandoffReceipt.properties.schema_version.const, 'bflabs.geo-handoff/1.0.0');
});

test('privacy copy discloses the short-lived bounded handoff without changing leaderboard consent', () => {
  const worker = read('src/worker-entry.mjs');
  assert.match(worker, /15 分钟/);
  assert.match(worker, /继续到 WorkBuddy/);
  assert.match(worker, /只有用户主动勾选公开榜单/);
});
