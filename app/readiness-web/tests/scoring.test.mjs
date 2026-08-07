import test from 'node:test';
import assert from 'node:assert/strict';
import { scoreEvidence } from '../src/scanner.mjs';

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
});
