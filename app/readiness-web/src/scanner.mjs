import crypto from 'node:crypto';
import { assertTargetAllowsScan, normalizeTarget, safeFetchText } from './safety.mjs';

export const RULESET_VERSION = '1.0.0';
export const ARTIFACT_PROTOCOL_VERSION = '1.0.0';

const PATHS = [
  '/robots.txt',
  '/',
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
  const isHtml = response.contentType.includes('html');
  const visibleText = isHtml ? stripMarkup(response.text) : response.text.trim();
  const signals = [];
  if (isHtml && /<title\b/i.test(response.text)) signals.push('has_title');
  if (isHtml && /<h1\b/i.test(response.text)) signals.push('has_h1');
  if (isHtml && /rel=["']canonical["']/i.test(response.text)) signals.push('has_canonical');
  if (isHtml && /application\/ld\+json/i.test(response.text)) signals.push('has_json_ld');
  if (isHtml && /\/\.webmcp\/bridge\.js/i.test(response.text)) signals.push('has_cloudflare_webmcp_bridge');
  if (isHtml && /\b(?:modelContext|registerTool|provideContext)\b/i.test(response.text)) signals.push('has_native_webmcp_signal');
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
    captured_at: new Date().toISOString(),
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
  const hasUnresolvedEvidence = applicable.some((check) => ['unknown', 'blocked'].includes(check.state));
  const score = applicable.length && !hasUnresolvedEvidence
    ? Math.round((passed / applicable.length) * 100)
    : null;
  const status = applicable.some((check) => check.state === 'blocked')
    ? 'blocked'
    : passed === applicable.length
      ? 'pass'
      : passed > 0
        ? 'partial'
        : applicable.some((check) => check.state === 'fail')
          ? 'fail'
          : 'unknown';
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

const observedState = (evidence, passed) => {
  if (!evidence) return 'unknown';
  return passed ? 'pass' : 'fail';
};

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
      { id: 'D-HTML', label: '原始 HTML 含有可用正文', state: observedState(home, hasUsefulHome), paths: ['/'] },
      { id: 'D-ROBOTS', label: '公开扫描未被 robots 阻止', state: !robots ? 'unknown' : robots.robots_blocked ? 'blocked' : 'pass', paths: ['/robots.txt'] },
      { id: 'D-CANONICAL', label: '首页声明 canonical', state: observedState(home, home?.signals.includes('has_canonical')), paths: ['/'] },
      { id: 'D-INDEX', label: '存在 sitemap 或 llms 入口', state: !sitemap && !llms ? 'unknown' : sitemap?.status_code === 200 || llms?.status_code === 200 ? 'pass' : 'fail', paths: ['/sitemap.xml', '/llms.txt'] },
    ], byPath),
    axis('understandable', '可理解', [
      { id: 'U-DEFINITION', label: '产品定义可直接提取', state: observedState(home, hasDirectDefinition), paths: ['/'] },
      { id: 'U-INTENTS', label: '关键意图有稳定答案入口', state: observedState(home, hasIntentAnswers), paths: ['/'] },
      { id: 'U-STRUCTURED', label: '结构化数据与公开事实入口存在', state: !home && !pricing ? 'unknown' : home?.signals.includes('has_json_ld') || pricing?.status_code === 200 ? 'pass' : 'fail', paths: ['/', '/pricing.json'] },
      { id: 'U-FRESHNESS', label: '易变事实包含新鲜度或版本', state: !pricing ? 'unknown' : pricing.status_code !== 200 ? 'not_applicable' : hasFreshness ? 'pass' : 'fail', paths: ['/pricing.json'] },
    ], byPath),
    axis('actionable', '可操作', [
      { id: 'A-FALLBACK', label: '存在稳定的人类操作入口', state: observedState(home, hasFallbackAction), paths: ['/'] },
      { id: 'A-MCP-CARD', label: 'MCP 发现文档可解析', state: observedState(card, card?.status_code === 200 && mcp.advertised), paths: ['/.well-known/mcp/server-card.json'] },
      { id: 'A-TOOLS', label: '公开工具具有名称、描述和输入 schema', state: !card ? 'unknown' : toolsAreTyped ? 'pass' : mcp.error ? 'blocked' : 'fail', paths: ['/.well-known/mcp/server-card.json'] },
      { id: 'A-WEBMCP', label: 'WebMCP bridge 或原生注册可见', state: observedState(home, hasWebMcpBridge || hasNativeWebMcp), paths: ['/'] },
    ], byPath, ['真实浏览器任务尚未执行时，Actionable 只能视为准备度证据，不能视为任务成功。']),
  ];
}

const unique = (values) => [...new Set(values)];

function protocolEvidence(evidence) {
  return evidence.map((item) => {
    let factVersion = null;
    if (item.path === '/pricing.json' && item.status_code === 200) {
      try {
        factVersion = JSON.parse(item.raw_text).pricing_version || null;
      } catch {
        factVersion = null;
      }
    }
    return {
      id: item.id,
      summary: `${item.path} returned ${item.status_code} (${item.content_type || 'unknown'})`,
      source_type: 'public-url',
      locator: item.url,
      captured_at: item.captured_at,
      content_hash: item.response_hash,
      support_scope: `fixed public-path readiness check for ${item.path}`,
      limitations: ['A local fixed-path response does not establish external AI visibility or business outcome.'],
      dynamic_fact: item.path === '/pricing.json' && item.status_code === 200,
      fact_version: factVersion,
      license: 'public response used as diagnostic evidence',
    };
  });
}

export function buildReadinessReport(origin, axes, findings, mcp) {
  const byId = new Map(axes.map((item) => [item.id, item]));
  const axisValue = (axisId) => {
    const source = byId.get(axisId);
    const value = {
      status: source.status,
      evidence_ids: unique(source.checks.flatMap((check) => check.evidence_ids)),
      limitations: source.limitations,
    };
    if (axisId === 'actionable') {
      const webmcp = source.checks.find((check) => check.id === 'A-WEBMCP');
      value.webmcp_status = webmcp?.state === 'pass'
        ? 'present_unverified'
        : webmcp?.state === 'fail'
          ? 'not_present'
          : 'unknown';
    }
    return value;
  };
  return {
    schema_version: '1.0.0',
    target: { origin },
    mode: 'audit',
    axes: {
      discoverable: axisValue('discoverable'),
      understandable: axisValue('understandable'),
      actionable: axisValue('actionable'),
    },
    findings,
    verification: axes.flatMap((axisItem) => axisItem.checks.map((check) => ({
      axis: axisItem.id,
      rule_id: check.id,
      state: check.state,
      evidence_ids: check.evidence_ids,
    }))),
    ai_visibility: 'not_measured',
    business_outcome: 'not_measured',
    external_gates: axisValue('actionable').webmcp_status === 'present_unverified' || mcp.advertised
      ? ['compatible-browser-task-verification']
      : [],
  };
}

export function buildSkillRoutes(findings) {
  const routes = new Map([
    ['geo-discover', '发现受众问题与内容机会'],
    ['geo-measure', '导入真实平台回答后测量外部可见度'],
    ['seo-plan', '需要迁移、索引或技术 SEO 计划时使用'],
  ]);
  for (const finding of findings) {
    routes.set(finding.owner_route, finding.owner_route === 'webmcp-enable'
      ? '补齐或验证 Agent 可操作入口'
      : '修复当前公开事实与准备度失败谓词');
  }
  if (findings.some((finding) => finding.axis === 'understandable')) {
    routes.set('geo-content', '从已确认事实生成答案页或内容蓝图');
  }
  return [...routes].map(([id, reason]) => ({
    id,
    reason,
    href: `/skills/${id}`,
    status: 'active',
  }));
}

export function buildAgentPrompt({ origin, fingerprint, axes, findings, evidenceGaps, routes }) {
  const failed = findings.map((item) => `${item.rule_id}:${item.state} (${item.title})`).join('; ') || 'none';
  const unknown = evidenceGaps.map((item) => `${item.rule_id} (${item.title})`).join('; ') || 'none';
  const readiness = axes.map((axisItem) => `${axisItem.label}=${axisItem.score == null ? 'N/A' : axisItem.score} (${axisItem.status})`).join('; ');
  const routeIds = routes.map((route) => route.id).join(', ') || 'none';
  return [
    'Use the bflabs-agent-readiness root Skill and the attached Artifact Pack as the evidence baseline.',
    `Target: ${origin}`,
    `Scan fingerprint: ${fingerprint}`,
    `Readiness axes: ${readiness}`,
    `Evidence-backed failed predicates: ${failed}`,
    `Unknown predicates requiring evidence: ${unknown}`,
    `Available minimum child-Skill routes: ${routeIds}`,
    'Validate the Artifact Pack hashes, inspect the website repository, choose the smallest child Skill, and change only evidence-backed items.',
    'After local verification, rerun the same diagnostic and return an explicit Before / After comparison tied to both scan fingerprints.',
    'Preserve unknown states, and keep AI visibility and business outcome not_measured unless separate evidence is supplied.',
    'Do not publish, deploy, enable external services, access private consoles, or claim ranking/revenue without separate owner approval and evidence.',
  ].join('\n');
}

export function buildArtifactPack({ input, completedAt, readinessReport, ledger, qualityReport, externalGates }) {
  const runId = `run-${completedAt.replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z')}-${crypto.randomBytes(4).toString('hex')}`;
  const files = {
    'input/request.json': input,
    'evidence-ledger.json': ledger,
    'quality-report.json': qualityReport,
    'outputs/readiness-report.json': readinessReport,
  };
  const schemaByPath = {
    'input/request.json': null,
    'evidence-ledger.json': 'evidence-ledger.schema.json',
    'quality-report.json': 'quality-report.schema.json',
    'outputs/readiness-report.json': 'readiness-report.schema.json',
  };
  const artifacts = Object.keys(files).sort().map((path) => ({
    path,
    sha256: crypto.createHash('sha256').update(`${JSON.stringify(files[path], null, 2)}\n`).digest('hex'),
    media_type: 'application/json',
    schema: schemaByPath[path],
  }));
  const manifest = {
    protocol_version: ARTIFACT_PROTOCOL_VERSION,
    run_id: runId,
    capability: 'bflabs-agent-readiness',
    capability_version: '1.0.0',
    workflow_id: null,
    created_at: completedAt,
    input_hash: `sha256:${crypto.createHash('sha256').update(`${JSON.stringify(input, null, 2)}\n`).digest('hex')}`,
    status: qualityReport.status,
    degradation: qualityReport.status === 'pass' ? null : 'fixed-path scan has warnings or blocked predicates',
    external_gates: externalGates,
    artifacts,
    replay_command: 'Run the local readiness-web scanner again for the same public origin.',
  };
  return {
    protocol_version: ARTIFACT_PROTOCOL_VERSION,
    manifest,
    files,
  };
}

export async function scanSite(input, options = {}) {
  const origin = normalizeTarget(input);
  await assertTargetAllowsScan(origin, options.fetchOptions);
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
  const evidenceGaps = axes.flatMap((item) => item.checks
    .filter((check) => check.state === 'unknown')
    .map((check) => ({
      id: `gap_${check.id.toLowerCase()}`,
      axis: item.id,
      rule_id: check.id,
      title: check.label,
      state: 'unknown',
      owner_route: check.id.startsWith('A-') ? 'webmcp-enable' : 'geo-optimize',
    })));

  const publicEvidence = evidence.map(({ raw_text: _rawText, ...item }) => item);
  const fingerprint = hash(JSON.stringify({ origin: origin.origin, ruleset: RULESET_VERSION, hashes: publicEvidence.map((item) => item.response_hash) }));
  const completedAt = new Date().toISOString();
  const scanStatus = errors.length || axes.some((item) => ['blocked', 'unknown'].includes(item.status))
    ? 'partial'
    : 'complete';
  const readinessReport = buildReadinessReport(origin.origin, axes, findings, mcp);
  const ledgerItems = protocolEvidence(evidence);
  const ledgerClaims = axes.flatMap((axisItem) => axisItem.checks
    .filter((check) => check.evidence_ids.length > 0)
    .map((check) => {
      const text = `${check.id}=${check.state}: ${check.label}`;
      return {
        id: `claim_${crypto.createHash('sha256').update(text).digest('hex').slice(0, 12)}`,
        text,
        evidence_ids: check.evidence_ids,
        support_level: 'direct',
      };
    }));
  const evidenceLedger = {
    schema_version: '1.0.0',
    items: ledgerItems,
    claims: ledgerClaims,
  };
  const unversionedDynamic = ledgerItems.filter((item) => item.dynamic_fact && !item.fact_version);
  const warnings = [];
  if (errors.length) warnings.push(`${errors.length} fixed public paths could not be fetched.`);
  if (evidenceGaps.length) warnings.push(`${evidenceGaps.length} predicates remain unknown because evidence is missing.`);
  if (unversionedDynamic.length) warnings.push('Dynamic public facts were found without a fact_version.');
  const qualityReport = {
    schema_version: '1.0.0',
    status: warnings.length ? 'pass_with_warnings' : 'pass',
    checks: [
      {
        id: 'fixed-path-scan',
        status: errors.length ? 'warning' : 'pass',
        message: errors.length ? 'one or more fixed public paths could not be fetched' : 'fixed public paths completed',
      },
      {
        id: 'unknown-preservation',
        status: evidenceGaps.length ? 'warning' : 'pass',
        message: evidenceGaps.length ? 'missing evidence remains unknown' : 'no predicate was inferred from missing evidence',
      },
      {
        id: 'dynamic-fact-freshness',
        status: unversionedDynamic.length ? 'warning' : 'pass',
        message: unversionedDynamic.length ? 'dynamic facts lack a version and are not promoted as current claims' : 'dynamic fact evidence is versioned or absent',
      },
      {
        id: 'measurement-boundary',
        status: 'pass',
        message: 'AI visibility and business outcome remain not_measured',
      },
    ],
    warnings,
    blockers: [],
  };
  const opportunities = [
    ...findings.map((item) => ({
      id: `opportunity_${item.rule_id.toLowerCase()}`,
      state: item.state,
      title: item.title,
      route: item.owner_route,
      basis: item.evidence_ids,
    })),
    ...evidenceGaps.map((item) => ({
      id: `opportunity_${item.rule_id.toLowerCase()}`,
      state: 'unknown',
      title: `补证据：${item.title}`,
      route: item.owner_route,
      basis: [],
    })),
  ];
  const routes = buildSkillRoutes(findings);
  const prompt = buildAgentPrompt({
    origin: origin.origin,
    fingerprint,
    axes,
    findings,
    evidenceGaps,
    routes,
  });
  const artifactPack = buildArtifactPack({
    input: { schema_version: '1.0.0', capability: 'bflabs-agent-readiness', captured_at: completedAt, url: origin.origin },
    completedAt,
    readinessReport,
    ledger: evidenceLedger,
    qualityReport,
    externalGates: readinessReport.external_gates,
  });
  return {
    schema_version: '1.0.0',
    ruleset_version: RULESET_VERSION,
    report_id: `rpt_${crypto.randomUUID()}`,
    scan_fingerprint: fingerprint,
    target: { requested_url: input, canonical_origin: origin.origin },
    scan: {
      status: scanStatus,
      completed_at: completedAt,
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
    evidence_gaps: evidenceGaps,
    opportunities,
    skill_routes: routes,
    agent_prompt: prompt,
    readiness_report: readinessReport,
    evidence_ledger: evidenceLedger,
    quality_report: qualityReport,
    artifact_pack: artifactPack,
    disclaimers: {
      ai_visibility: 'not_measured',
      business_outcome: 'not_measured',
      actionability: 'A real compatible-browser task run is required for verified task completion.',
    },
  };
}
