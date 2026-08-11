import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { buildArtifactPack, buildReadinessReport, scoreEvidence } from '../src/scanner.mjs';

const evidence = [
  {
    id: 'ev_home',
    path: '/',
    status_code: 200,
    visible_text_length: 640,
    raw_text: '<link rel="canonical" href="https://beefapi.com"><script type="application/ld+json">FAQPage</script><a href="/pricing">价格</a><p>BeefAPI 是多模型 AI 服务入口。</p><script src="/.webmcp/bridge.js"></script>',
    excerpt: 'BeefAPI 是多模型 AI 服务入口',
    signals: ['has_canonical', 'has_json_ld', 'has_cloudflare_webmcp_bridge'],
  },
  { id: 'ev_robots', path: '/robots.txt', status_code: 200, robots_blocked: false, raw_text: 'User-agent: *\nAllow: /', signals: [] },
  { id: 'ev_sitemap', path: '/sitemap.xml', status_code: 200, raw_text: '<urlset/>', signals: [] },
  { id: 'ev_llms', path: '/llms.txt', status_code: 200, raw_text: '# BeefAPI', signals: [] },
  { id: 'ev_pricing', path: '/pricing.json', status_code: 200, raw_text: '{"generated_at":"now","pricing_version":"sha256:test"}', signals: [] },
  { id: 'ev_card', path: '/.well-known/mcp/server-card.json', status_code: 200, raw_text: '{"remotes":[]}', signals: [] },
];

test('reports three independent readiness axes', () => {
  const axes = scoreEvidence(evidence, {
    advertised: true,
    tools: [{ name: 'get_model_pricing', description: 'Get price', inputSchema: { type: 'object' } }],
  });
  assert.deepEqual(axes.map((axis) => axis.id), ['discoverable', 'understandable', 'actionable']);
  assert.equal(axes.every((axis) => axis.status === 'pass'), true);
});

test('missing WebMCP affects only Actionable', () => {
  const withoutBridge = evidence.map((item) => item.path === '/' ? { ...item, signals: ['has_canonical', 'has_json_ld'], raw_text: item.raw_text.replace('/.webmcp/bridge.js', '/app.js') } : item);
  const axes = scoreEvidence(withoutBridge, { advertised: true, tools: [{ name: 'search', description: 'Search', inputSchema: {} }] });
  assert.equal(axes.find((axis) => axis.id === 'discoverable').status, 'pass');
  assert.equal(axes.find((axis) => axis.id === 'understandable').status, 'pass');
  assert.equal(axes.find((axis) => axis.id === 'actionable').status, 'partial');
  const report = buildReadinessReport('https://beefapi.com', axes, [], { advertised: true });
  assert.equal(report.axes.actionable.webmcp_status, 'not_present');
  assert.deepEqual(report.external_gates, ['compatible-browser-task-verification']);
});

test('missing fetch evidence remains unknown instead of becoming a failed finding', () => {
  const axes = scoreEvidence([], { advertised: false, tools: [] });
  assert.deepEqual(axes.map((axis) => axis.status), ['unknown', 'unknown', 'unknown']);
  assert.deepEqual(axes.map((axis) => axis.score), [null, null, null]);
  assert.equal(axes.flatMap((axis) => axis.checks).some((check) => check.state === 'fail'), false);
  const report = buildReadinessReport('https://example.com', axes, [], { advertised: false });
  assert.equal(report.axes.actionable.webmcp_status, 'unknown');
});

test('web scanner canonical report matches the shared readiness schema topology', () => {
  const axes = scoreEvidence(evidence, {
    advertised: true,
    tools: [{ name: 'get_model_pricing', description: 'Get price', inputSchema: { type: 'object' } }],
  });
  const report = buildReadinessReport('https://beefapi.com', axes, [], { advertised: true });
  assert.deepEqual(Object.keys(report).sort(), [
    'ai_visibility', 'axes', 'business_outcome', 'external_gates', 'findings', 'mode', 'schema_version', 'target', 'verification',
  ]);
  assert.equal(report.schema_version, '1.0.0');
  assert.deepEqual(Object.keys(report.axes), ['discoverable', 'understandable', 'actionable']);
  assert.equal(report.ai_visibility, 'not_measured');
  assert.equal(report.business_outcome, 'not_measured');
  assert.equal(report.axes.actionable.webmcp_status, 'present_unverified');
});

test('downloadable artifact pack hashes every shared protocol file', () => {
  const completedAt = '2026-08-11T07:10:00.000Z';
  const readinessReport = {
    schema_version: '1.0.0', target: { origin: 'https://example.com' }, mode: 'audit',
    axes: {
      discoverable: { status: 'unknown', evidence_ids: [], limitations: [] },
      understandable: { status: 'unknown', evidence_ids: [], limitations: [] },
      actionable: { status: 'unknown', evidence_ids: [], limitations: [], webmcp_status: 'unknown' },
    },
    findings: [], verification: [], ai_visibility: 'not_measured', business_outcome: 'not_measured', external_gates: [],
  };
  const ledger = { schema_version: '1.0.0', items: [], claims: [] };
  const qualityReport = { schema_version: '1.0.0', status: 'pass_with_warnings', checks: [], warnings: ['fixture'], blockers: [] };
  const input = { schema_version: '1.0.0', capability: 'bflabs-agent-readiness', captured_at: completedAt, url: 'https://example.com' };
  const pack = buildArtifactPack({ input, completedAt, readinessReport, ledger, qualityReport, externalGates: [] });
  assert.match(pack.manifest.run_id, /^run-20260811T071000Z-[a-f0-9]{8}$/);
  assert.equal(pack.manifest.status, 'pass_with_warnings');
  for (const artifact of pack.manifest.artifacts) {
    const expected = crypto.createHash('sha256').update(`${JSON.stringify(pack.files[artifact.path], null, 2)}\n`).digest('hex');
    assert.equal(artifact.sha256, expected);
  }
  assert.equal(pack.manifest.input_hash, `sha256:${pack.manifest.artifacts.find((item) => item.path === 'input/request.json').sha256}`);
});
