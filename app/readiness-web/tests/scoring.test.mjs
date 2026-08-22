import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { buildAgentJourney, buildAgentPrompt, buildArtifactPack, buildReadinessReport, buildSkillRoutes, scoreEvidence } from '../src/scanner.mjs';

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

test('Agent handoff binds current public-state evidence and selects one next Skill', () => {
  const prompt = buildAgentPrompt({
    origin: 'https://example.com',
    fingerprint: `sha256:${'a'.repeat(64)}`,
    axes: [
      { label: '可发现', score: 100, status: 'pass' },
      { label: '可理解', score: 75, status: 'partial' },
      { label: '可操作', score: null, status: 'unknown' },
    ],
    findings: [{ rule_id: 'U-INTENTS', state: 'fail', title: '关键意图有稳定答案入口' }],
    evidenceGaps: [{ rule_id: 'A-WEBMCP', title: 'WebMCP bridge 或原生注册可见' }],
    routes: [{ id: 'geo-optimize' }],
    journey: { status: 'partial', steps: [{ id: 'enter', status: 'pass' }, { id: 'continue', status: 'partial' }] },
  });
  assert.match(prompt, /Agent Skills 索引：https:\/\/readiness\.bflabs\.cn\/\.well-known\/agent-skills\/index\.json/);
  assert.match(prompt, /根 Skill：https:\/\/readiness\.bflabs\.cn\/skills\/bflabs-agent-readiness/);
  assert.match(prompt, /本次唯一子 Skill：geo-optimize/);
  assert.match(prompt, /扫描指纹：sha256:/);
  assert.match(prompt, /可操作=N\/A \(unknown\)/);
  assert.match(prompt, /Agent Journey：partial/);
  assert.match(prompt, /不要自行部署/);
  assert.match(prompt, /AI visibility 与 Business outcome 必须保持 not_measured/);
  assert.doesNotMatch(prompt, /Artifact Pack/);
});

test('child Skill routes stay inside the checked-out trial build', () => {
  const routes = buildSkillRoutes([{ axis: 'actionable', owner_route: 'webmcp-enable' }]);
  assert.equal(routes.every((route) => route.href === `/skills/${route.id}`), true);
  assert.deepEqual(routes.map((route) => route.id), ['webmcp-enable']);
  assert.deepEqual(buildSkillRoutes([]), []);
});

test('child Skill handoff chooses the first evidence-backed owner only', () => {
  const routes = buildSkillRoutes([
    { axis: 'understandable', owner_route: 'geo-optimize' },
    { axis: 'actionable', owner_route: 'webmcp-enable' },
  ]);
  assert.deepEqual(routes.map((route) => route.id), ['geo-optimize']);
});

test('MCP discovery and tool findings belong to webmcp-enable', () => {
  const withoutMcp = evidence.filter((item) => item.path !== '/.well-known/mcp/server-card.json');
  const axes = scoreEvidence(withoutMcp, { advertised: false, tools: [] });
  const actionable = axes.find((axis) => axis.id === 'actionable');
  const mcpChecks = actionable.checks.filter((check) => ['A-MCP-CARD', 'A-TOOLS'].includes(check.id));
  assert.deepEqual(mcpChecks.map((check) => check.state), ['unknown', 'unknown']);
  assert.deepEqual(mcpChecks.map((check) => check.id), ['A-MCP-CARD', 'A-TOOLS']);
});

test('Agent Journey is deterministic supporting evidence and never promotes measurement layers', () => {
  const journey = buildAgentJourney('https://beefapi.com', evidence, {
    endpoint: 'https://beefapi.com/mcp',
    tools: [{ name: 'get_model_pricing' }],
  });
  assert.equal(journey.status, 'partial');
  assert.deepEqual(journey.steps.map((step) => step.id), ['enter', 'understand', 'continue']);
  assert.equal(journey.steps[2].action.kind, 'mcp-tool');
  assert.equal(journey.affects_readiness_score, false);
  assert.equal(journey.ai_visibility, 'not_measured');
  assert.equal(journey.business_outcome, 'not_measured');
});

test('Agent Journey only marks a same-origin continuation passed after the link is fetched', () => {
  const home = {
    id: 'ev_home', path: '/', status_code: 200, visible_text_length: 640,
    raw_text: '<title>Example</title><h1>Example service</h1><p>Example provides a public service with enough stable text for an agent to understand the page.</p><a href="/docs">Docs</a>',
    excerpt: 'Example service', signals: ['has_title', 'has_h1'],
  };
  const planned = buildAgentJourney('https://example.com', [home], { tools: [] });
  assert.equal(planned.steps[2].status, 'partial');
  const followed = buildAgentJourney('https://example.com', [home], { tools: [] }, {
    evidence: { id: 'ev_docs', status_code: 200 },
  });
  assert.equal(followed.steps[2].status, 'pass');
  assert.deepEqual(followed.steps[2].evidence_ids, ['ev_home', 'ev_docs']);
});
