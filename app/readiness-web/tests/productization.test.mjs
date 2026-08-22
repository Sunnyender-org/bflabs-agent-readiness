import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { handleMcp, MCP_TOOLS } from '../src/mcp-server.mjs';
import { buildLeaderboardEntry, LEADERBOARD_RETENTION_SECONDS, memoryLeaderboardStore, publishToLeaderboard, rankLeaderboard, readLeaderboard, readLeaderboardEntry } from '../src/leaderboard.mjs';
import { leaderboardIndexPage, leaderboardSharePage, problemDetails, reportToMarkdown } from '../src/product-contract.mjs';

const report = {
  target: { canonical_origin: 'https://example.com' },
  scan_fingerprint: `sha256:${'a'.repeat(64)}`,
  scan: { completed_at: '2026-08-22T10:00:00.000Z' },
  axes: [
    { id: 'discoverable', label: '可发现', score: 100, status: 'pass' },
    { id: 'understandable', label: '可理解', score: 75, status: 'partial' },
    { id: 'actionable', label: '可操作', score: 50, status: 'partial' },
  ],
  findings: [{ rule_id: 'A-WEBMCP', state: 'fail', title: 'WebMCP 可见' }],
  skill_routes: [{ id: 'webmcp-enable', href: '/skills/webmcp-enable' }],
  agent_journey: {
    task: '进入并找到下一步。', status: 'partial',
    steps: [{ label: '进入', status: 'pass', observation: '首页可访问。' }],
    affects_readiness_score: false,
    ai_visibility: 'not_measured',
    business_outcome: 'not_measured',
  },
};

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const scenarios = JSON.parse(fs.readFileSync(path.join(root, 'tests/fixtures/productization-scenarios.json'), 'utf8'));

test('leaderboard stores only the public summary and ranks without a hidden total', async () => {
  const entry = buildLeaderboardEntry(report);
  assert.deepEqual(Object.keys(entry).sort(), ['axes', 'canonical_origin', 'host', 'scan_fingerprint', 'scanned_at', 'schema_version']);
  assert.equal('evidence' in entry, false);
  const store = memoryLeaderboardStore();
  assert.equal((await publishToLeaderboard(store, report)).status, 'published');
  const board = await readLeaderboard(store);
  assert.equal(board.entries[0].host, 'example.com');
  assert.equal(board.entries[0].ranking_basis.passed_axes, 1);
  assert.equal('score' in board.entries[0], false);
});

test('leaderboard publication degrades without storage instead of failing the scan', async () => {
  assert.deepEqual(await publishToLeaderboard(null, report), {
    status: 'unavailable', reason: 'leaderboard-storage-not-configured',
  });
});

test('leaderboard entries expire after the disclosed 30-day retention window', async () => {
  let write;
  const store = {
    async put(key, value, options) { write = { key, value, options }; },
  };
  await publishToLeaderboard(store, report);
  assert.equal(write.key, 'entry:example.com');
  assert.equal(write.options.expirationTtl, LEADERBOARD_RETENTION_SECONDS);
  assert.equal(LEADERBOARD_RETENTION_SECONDS, 2_592_000);
});

test('opt-in leaderboard entries have indexable share pages', async () => {
  const store = memoryLeaderboardStore();
  await publishToLeaderboard(store, report);
  const entry = await readLeaderboardEntry(store, 'example.com');
  const page = leaderboardSharePage(entry);
  assert.match(page, /<title>example\.com · BFLabs Agent Readiness 榜单<\/title>/);
  assert.match(page, /rel="canonical" href="https:\/\/readiness\.bflabs\.cn\/leaderboard\/example\.com"/);
  assert.match(page, /AI visibility 或 Business outcome/);
  const index = leaderboardIndexPage(await readLeaderboard(store));
  assert.match(index, /href="\/leaderboard\/example\.com"/);
  assert.match(index, /rel="canonical" href="https:\/\/readiness\.bflabs\.cn\/leaderboard"/);
  assert.equal(await readLeaderboardEntry(store, '../bad'), null);
});

test('productization scenarios replay through production contract helpers', async () => {
  const outcomes = [];
  for (const scenario of scenarios.cases) {
    if ('publish_to_leaderboard' in scenario) {
      const publication = scenario.publish_to_leaderboard
        ? await publishToLeaderboard(scenario.store === 'ready' ? memoryLeaderboardStore() : null, report)
        : { status: 'not_requested' };
      outcomes.push([scenario.id, publication.status]);
      assert.equal(publication.status, scenario.expected_publication, scenario.id);
    } else {
      outcomes.push([scenario.id, report.agent_journey.status]);
      assert.equal(report.agent_journey.status, scenario.journey_status);
      assert.equal(report.agent_journey.affects_readiness_score, scenario.expected_score_effect);
      assert.equal(report.agent_journey.ai_visibility, scenario.expected_ai_visibility);
      assert.equal(report.agent_journey.business_outcome, scenario.expected_business_outcome);
    }
  }
  assert.equal(outcomes.length, 4);
});

test('leaderboard ordering uses the disclosed three-axis method', () => {
  const stronger = { ...buildLeaderboardEntry(report), host: 'strong.example', axes: report.axes.map((axis) => ({ ...axis, status: 'pass', score: 80 })) };
  const weaker = { ...buildLeaderboardEntry(report), host: 'weak.example' };
  assert.deepEqual(rankLeaderboard([weaker, stronger]).map((entry) => entry.host), ['strong.example', 'weak.example']);
});

test('markdown report is agent-readable and preserves measurement boundaries', () => {
  const text = reportToMarkdown(report);
  assert.match(text, /# BFLabs Agent Readiness/);
  assert.match(text, /webmcp-enable/);
  assert.match(text, /AI visibility：not_measured/);
  assert.match(text, /Agent Journey 是本次公开页面的确定性试跑证据/);
});

test('problem details include stable code and resolution', () => {
  const value = problemDetails(new Error('目标站点已通过公开 opt-out 文件拒绝诊断'), '/api/v1/scans');
  assert.equal(value.status, 403);
  assert.equal(value.code, 'target_opted_out');
  assert.match(value.resolution, /opt-out/);
  const missing = problemDetails(Object.assign(new Error('API 路径不存在'), { status: 404 }), '/api/v1/nope');
  assert.equal(missing.code, 'api_route_not_found');
  assert.match(missing.resolution, /openapi\.json/);
});

test('MCP exposes one report contract through read-only agent tools', async () => {
  assert.deepEqual(MCP_TOOLS.map((tool) => tool.name), [
    'bflabs_scan_public_site', 'bflabs_get_methodology', 'bflabs_get_skill', 'bflabs_get_leaderboard',
  ]);
  const request = new Request('https://readiness.example/mcp', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'bflabs_scan_public_site', arguments: { url: 'https://example.com' } } }),
  });
  const response = await handleMcp(request, {
    scan: async () => report,
    leaderboard: async () => ({ entries: [] }),
    skills: { 'bflabs-agent-readiness': '# Root Skill' },
  });
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.equal(body.result.structuredContent.scan_fingerprint, report.scan_fingerprint);
  assert.match(body.result.content[0].text, /BFLabs Agent Readiness/);
});
