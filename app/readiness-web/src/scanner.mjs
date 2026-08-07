import crypto from 'node:crypto';
import { normalizeTarget, safeFetchText } from './safety.mjs';

export const RULESET_VERSION = '0.2.0';

const PATHS = [
  '/',
  '/robots.txt',
  '/sitemap.xml',
  '/llms.txt',
  '/pricing.json',
  '/.well-known/mcp/server-card.json',
];

const stripMarkup = (html) => html
  .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, ' ')
  .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, ' ')
  .replace(/<[^>]+>/g, ' ')
  .replace(/\s+/g, ' ')
  .trim();

const hash = (value) => `sha256:${crypto.createHash('sha256').update(value).digest('hex')}`;

function evidenceFrom(path, response) {
  const visibleText = response.contentType.includes('html') ? stripMarkup(response.text) : response.text.trim();
  const signals = [];
  if (/<title\b/i.test(response.text)) signals.push('has_title');
  if (/<h1\b/i.test(response.text)) signals.push('has_h1');
  if (/rel=["']canonical["']/i.test(response.text)) signals.push('has_canonical');
  if (/application\/ld\+json/i.test(response.text)) signals.push('has_json_ld');
  if (/\/\.webmcp\/bridge\.js/i.test(response.text)) signals.push('has_cloudflare_webmcp_bridge');
  if (/modelContext|registerTool|provideContext/i.test(response.text)) signals.push('has_native_webmcp_signal');
  return {
    id: `ev_${crypto.createHash('sha1').update(path).digest('hex').slice(0, 8)}`,
    path,
    url: response.url,
    status_code: response.status,
    content_type: response.contentType,
    response_hash: hash(response.text),
    excerpt: visibleText.slice(0, 420),
    visible_text_length: visibleText.length,
    redirect_chain: response.redirects,
    signals,
  };
}

function parseRobotsBlocked(text) {
  const groups = String(text).split(/(?=^\s*user-agent\s*:)/gim);
  return groups.some((group) => {
    const wildcard = /^\s*user-agent\s*:\s*\*/im.test(group) || /^\s*user-agent\s*:\s*bflabs-geo-audit/im.test(group);
    return wildcard && /^\s*disallow\s*:\s*\/\s*$/im.test(group);
  });
}

function axis(id, label, checks, evidenceByPath, limitations = []) {
  const applicable = checks.filter((check) => check.state !== 'not_applicable');
  const passed = applicable.filter((check) => check.state === 'pass').length;
  const score = applicable.length ? Math.round((passed / applicable.length) * 100) : null;
  const status = applicable.some((check) => check.state === 'blocked')
    ? 'blocked'
    : passed === applicable.length
      ? 'pass'
      : passed > 0
        ? 'partial'
        : 'fail';
  return {
    id,
    label,
    status,
    score,
    checks: checks.map((check) => ({
      ...check,
      evidence_ids: (check.paths || []).map((path) => evidenceByPath.get(path)?.id).filter(Boolean),
    })),
    limitations,
  };
}

async function inspectMcp(origin, cardEvidence, fetchOptions) {
  const result = { advertised: false, endpoint: null, tools: [], error: null };
  if (!cardEvidence || cardEvidence.status_code !== 200) return result;
  try {
    const card = JSON.parse(cardEvidence.raw_text);
    const endpoint = card.remotes?.find((remote) => remote.type === 'streamable-http')?.url;
    if (!endpoint) return result;
    const target = new URL(endpoint, origin);
    if (target.origin !== origin.origin) throw new Error('MCP endpoint is not same-origin');
    result.advertised = true;
    result.endpoint = target.toString();
    const payload = JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/list', params: {} });
    const response = await safeFetchText(target, {
      ...fetchOptions,
      method: 'POST',
      body: payload,
      contentType: 'application/json',
      accept: 'application/json, text/event-stream',
    });
    const parsed = JSON.parse(response.text);
    result.tools = parsed.result?.tools || [];
  } catch (error) {
    result.error = error.message;
  }
  return result;
}

export function scoreEvidence(evidence, mcp = { advertised: false, tools: [] }) {
  const byPath = new Map(evidence.map((item) => [item.path, item]));
  const home = byPath.get('/');
  const robots = byPath.get('/robots.txt');
  const sitemap = byPath.get('/sitemap.xml');
  const llms = byPath.get('/llms.txt');
  const pricing = byPath.get('/pricing.json');
  const card = byPath.get('/.well-known/mcp/server-card.json');
  const rawHome = home?.raw_text || '';
  const rawPricing = pricing?.raw_text || '';
  const hasUsefulHome = home?.status_code === 200 && home.visible_text_length >= 200;
  const hasDirectDefinition = /description|是什么|provides|platform|service|服务|产品/i.test(`${rawHome} ${home?.excerpt || ''}`);
  const hasFreshness = /generated_at|effective_at|pricing_version|dateModified|version/i.test(rawPricing);
  const hasIntentAnswers = /FAQPage|Question|answers|pricing|价格|quickstart|开始|docs/i.test(rawHome);
  const hasFallbackAction = /href=["'][^"']*(chat|login|register|signup|pricing|docs|contact|start)/i.test(rawHome);
  const hasWebMcpBridge = home?.signals.includes('has_cloudflare_webmcp_bridge') || false;
  const hasNativeWebMcp = home?.signals.includes('has_native_webmcp_signal') || false;
  const toolsAreTyped = mcp.tools.length > 0 && mcp.tools.every((tool) => tool.name && tool.description && tool.inputSchema);

  return [
    axis('discoverable', '可发现', [
      { id: 'D-HTML', label: '原始 HTML 含有可用正文', state: hasUsefulHome ? 'pass' : 'fail', paths: ['/'] },
      { id: 'D-ROBOTS', label: '公开扫描未被 robots 阻止', state: robots?.robots_blocked ? 'blocked' : 'pass', paths: ['/robots.txt'] },
      { id: 'D-CANONICAL', label: '首页声明 canonical', state: home?.signals.includes('has_canonical') ? 'pass' : 'fail', paths: ['/'] },
      { id: 'D-INDEX', label: '存在 sitemap 或 llms 入口', state: sitemap?.status_code === 200 || llms?.status_code === 200 ? 'pass' : 'fail', paths: ['/sitemap.xml', '/llms.txt'] },
    ], byPath),
    axis('understandable', '可理解', [
      { id: 'U-DEFINITION', label: '产品定义可直接提取', state: hasDirectDefinition ? 'pass' : 'fail', paths: ['/'] },
      { id: 'U-INTENTS', label: '关键意图有稳定答案入口', state: hasIntentAnswers ? 'pass' : 'fail', paths: ['/'] },
      { id: 'U-STRUCTURED', label: '结构化数据与公开事实入口存在', state: home?.signals.includes('has_json_ld') || pricing?.status_code === 200 ? 'pass' : 'fail', paths: ['/', '/pricing.json'] },
      { id: 'U-FRESHNESS', label: '易变事实包含新鲜度或版本', state: pricing?.status_code !== 200 ? 'not_applicable' : hasFreshness ? 'pass' : 'fail', paths: ['/pricing.json'] },
    ], byPath),
    axis('actionable', '可操作', [
      { id: 'A-FALLBACK', label: '存在稳定的人类操作入口', state: hasFallbackAction ? 'pass' : 'fail', paths: ['/'] },
      { id: 'A-MCP-CARD', label: 'MCP 发现文档可解析', state: card?.status_code === 200 && mcp.advertised ? 'pass' : 'fail', paths: ['/.well-known/mcp/server-card.json'] },
      { id: 'A-TOOLS', label: '公开工具具有名称、描述和输入 schema', state: toolsAreTyped ? 'pass' : mcp.error ? 'blocked' : 'fail', paths: ['/.well-known/mcp/server-card.json'] },
      { id: 'A-WEBMCP', label: 'WebMCP bridge 或原生注册可见', state: hasWebMcpBridge || hasNativeWebMcp ? 'pass' : 'fail', paths: ['/'] },
    ], byPath, ['真实浏览器任务尚未执行时，Actionable 只能视为准备度证据，不能视为任务成功。']),
  ];
}

export async function scanSite(input, options = {}) {
  const origin = normalizeTarget(input);
  const evidence = [];
  const errors = [];
  const delayMs = options.delayMs ?? 350;

  for (const path of PATHS) {
    try {
      const response = await safeFetchText(new URL(path, origin), options.fetchOptions);
      const item = evidenceFrom(path, response);
      item.raw_text = response.text;
      if (path === '/robots.txt') item.robots_blocked = response.status === 200 && parseRobotsBlocked(response.text);
      evidence.push(item);
      if (path === '/robots.txt' && item.robots_blocked) break;
    } catch (error) {
      errors.push({ path, message: error.message });
    }
    if (delayMs > 0) await new Promise((resolve) => setTimeout(resolve, delayMs));
  }

  const byPath = new Map(evidence.map((item) => [item.path, item]));
  const mcp = await inspectMcp(origin, byPath.get('/.well-known/mcp/server-card.json'), options.fetchOptions);
  const axes = scoreEvidence(evidence, mcp);
  const findings = axes.flatMap((item) => item.checks
    .filter((check) => ['fail', 'blocked'].includes(check.state))
    .map((check) => ({
      id: `finding_${check.id.toLowerCase()}`,
      axis: item.id,
      rule_id: check.id,
      severity: check.state === 'blocked' ? 'high' : 'medium',
      title: check.label,
      state: check.state,
      evidence_ids: check.evidence_ids,
      owner_route: check.id === 'A-WEBMCP' || check.id === 'A-TOOLS' ? 'webmcp-enable' : 'geo-optimize',
    })));

  const publicEvidence = evidence.map(({ raw_text: _rawText, ...item }) => item);
  const fingerprint = hash(JSON.stringify({ origin: origin.origin, ruleset: RULESET_VERSION, hashes: publicEvidence.map((item) => item.response_hash) }));
  return {
    schema_version: '0.2.0',
    ruleset_version: RULESET_VERSION,
    report_id: `rpt_${crypto.randomUUID()}`,
    scan_fingerprint: fingerprint,
    target: { requested_url: input, canonical_origin: origin.origin },
    scan: {
      status: axes.some((item) => item.status === 'blocked') ? 'partial' : 'complete',
      completed_at: new Date().toISOString(),
      scanned_urls: publicEvidence.map((item) => item.url),
      errors,
    },
    axes,
    mcp: {
      advertised: mcp.advertised,
      endpoint: mcp.endpoint,
      tools: mcp.tools.map((tool) => ({ name: tool.name, description: tool.description, annotations: tool.annotations || {} })),
      error: mcp.error,
    },
    evidence: publicEvidence,
    findings,
    disclaimers: {
      ai_visibility: 'not_measured',
      business_outcome: 'not_measured',
      actionability: 'A real compatible-browser task run is required for verified task completion.',
    },
  };
}
