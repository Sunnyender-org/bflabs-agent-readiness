import crypto from 'node:crypto';
import { assertTargetAllowsScan, normalizeTarget, safeFetchText } from './safety.mjs';

export const RULESET_VERSION = '1.0.0';
export const ARTIFACT_PROTOCOL_VERSION = '1.0.0';
export const PUBLIC_SKILL_BASE = 'https://readiness.bflabs.cn';

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

function extractJourneyAction(home, origin, mcp) {
  if (mcp.tools?.length) {
    return {
      kind: 'mcp-tool',
      label: mcp.tools[0].name,
      locator: mcp.endpoint,
      observation: `发现 ${mcp.tools.length} 个公开 MCP 工具，首个为 ${mcp.tools[0].name}。`,
    };
  }
  const html = home?.raw_text || '';
  const candidates = [...html.matchAll(/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi)]
    .map((match) => {
      try {
        const target = new URL(match[1], origin);
        if (target.origin !== origin.origin) return null;
        const label = stripMarkup(match[2]).slice(0, 80) || target.pathname;
        const value = `${target.pathname} ${label}`.toLowerCase();
        const priority = ['docs', 'pricing', 'contact', 'signup', 'register', 'login', 'start', 'api']
          .findIndex((keyword) => value.includes(keyword));
        return priority < 0 ? null : { target, label, priority };
      } catch {
        return null;
      }
    })
    .filter(Boolean)
    .sort((left, right) => left.priority - right.priority || left.target.pathname.localeCompare(right.target.pathname));
  const selected = candidates[0];
  return selected ? {
    kind: 'same-origin-link',
    label: selected.label,
    locator: selected.target.toString(),
    observation: `找到可继续操作的同站入口：${selected.label}。`,
  } : null;
}

export function buildAgentJourney(originInput, evidence, mcp = { tools: [] }, probe = {}) {
  const origin = new URL(originInput);
  const home = evidence.find((item) => item.path === '/');
  const entered = Boolean(home && home.status_code >= 200 && home.status_code < 400);
  const understood = entered && home.visible_text_length >= 200
    && home.signals.includes('has_title') && home.signals.includes('has_h1');
  const action = entered ? extractJourneyAction(home, origin, mcp) : null;
  const actionProbePassed = probe.evidence && probe.evidence.status_code >= 200 && probe.evidence.status_code < 400;
  const continued = action?.kind === 'mcp-tool' || actionProbePassed;
  const steps = [
    {
      id: 'enter',
      label: '进入公开站点',
      status: entered ? 'pass' : home ? 'fail' : 'unknown',
      observation: entered ? `首页返回 ${home.status_code}，Agent 可进入。` : '没有足够证据证明 Agent 可以进入首页。',
      evidence_ids: home ? [home.id] : [],
    },
    {
      id: 'understand',
      label: '理解页面用途',
      status: understood ? 'pass' : entered ? 'partial' : 'blocked',
      observation: understood
        ? `原始 HTML 提供标题、H1 和 ${home.visible_text_length} 个可见字符。`
        : entered ? '页面可进入，但标题、H1 或无需 JavaScript 的正文仍不完整。' : '首页不可进入，无法继续理解。',
      evidence_ids: home ? [home.id] : [],
    },
    {
      id: 'continue',
      label: '找到下一步',
      status: continued ? 'pass' : entered ? 'partial' : 'blocked',
      observation: actionProbePassed
        ? `${action.observation} 继续读取后返回 ${probe.evidence.status_code}。`
        : action?.kind === 'mcp-tool'
          ? action.observation
          : probe.error
            ? `${action?.observation || '找到候选入口，但无法继续读取。'} ${probe.error}`
            : action?.observation || (entered ? '未找到清楚的同站操作入口或公开 MCP 工具。' : '首页不可进入，无法寻找下一步。'),
      evidence_ids: [home?.id, probe.evidence?.id].filter(Boolean),
      ...(action ? { action } : {}),
    },
  ];
  const status = steps.every((step) => step.status === 'pass')
    ? 'pass'
    : steps.some((step) => step.status === 'blocked') ? 'blocked' : 'partial';
  return {
    schema_version: '1.0.0',
    task: '进入公开首页，理解网站用途，并找到一个可继续操作的公开入口。',
    status,
    steps,
    summary_evidence: home?.excerpt || null,
    affects_readiness_score: false,
    ai_visibility: 'not_measured',
    business_outcome: 'not_measured',
    limitations: [
      '这是基于本次公开页面响应的确定性 Agent 试跑，不是外部 AI 平台抽样。',
      '试跑不会执行目标页面中的指令、提交表单、登录或写入任何外部系统。',
    ],
  };
}

export async function runAgentJourney(origin, evidence, mcp, fetchOptions = {}) {
  const initial = buildAgentJourney(origin.origin, evidence, mcp);
  const action = initial.steps.find((step) => step.id === 'continue')?.action;
  if (!action || action.kind !== 'same-origin-link') return initial;
  try {
    const response = await safeFetchText(new URL(action.locator), {
      ...fetchOptions,
      maxRedirects: Math.min(fetchOptions.maxRedirects ?? 2, 2),
      maxBytes: Math.min(fetchOptions.maxBytes ?? 256 * 1024, 256 * 1024),
      timeoutMs: Math.min(fetchOptions.timeoutMs ?? 8_000, 8_000),
    });
    const targetPath = new URL(response.url).pathname;
    const item = evidenceFrom(`journey:${targetPath}`, response);
    item.raw_text = response.text;
    evidence.push(item);
    return buildAgentJourney(origin.origin, evidence, mcp, { evidence: item });
  } catch (error) {
    return buildAgentJourney(origin.origin, evidence, mcp, { error: `继续读取失败：${error.message}` });
  }
}

const unique = (values) => [...new Set(values)];
const ownerRouteForCheck = (ruleId) => ['A-MCP-CARD', 'A-TOOLS', 'A-WEBMCP'].includes(ruleId)
  ? 'webmcp-enable'
  : 'geo-optimize';

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
      support_scope: item.path.startsWith('journey:')
        ? `bounded Agent Journey continuation probe for ${item.path.slice('journey:'.length)}`
        : `fixed public-path readiness check for ${item.path}`,
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
  const finding = findings.find((item) => ['geo-optimize', 'webmcp-enable'].includes(item.owner_route));
  if (!finding) return [];
  const id = finding.owner_route;
  return [{
    id,
    reason: id === 'webmcp-enable'
      ? '补齐或验证当前公开网站的 Agent 可操作入口'
      : '修复当前公开网站的准备度失败谓词',
    href: `/skills/${id}`,
    status: 'active',
  }];
}

export function buildAgentPrompt({ origin, fingerprint, axes, findings, evidenceGaps, routes, journey = null }) {
  const readiness = axes.map((axisItem) => `${axisItem.label}=${axisItem.score == null ? 'N/A' : axisItem.score} (${axisItem.status})`).join('; ');
  const routeId = routes[0]?.id || 'none';
  const ownedFindings = routeId === 'none' ? [] : findings.filter((item) => item.owner_route === routeId);
  const ownedGaps = routeId === 'none' ? [] : evidenceGaps.filter((item) => item.owner_route === routeId);
  const failed = ownedFindings.map((item) => `${item.rule_id}:${item.state} (${item.title})`).join('; ') || 'none';
  const unknown = ownedGaps.map((item) => `${item.rule_id} (${item.title})`).join('; ') || 'none';
  const journeySummary = journey
    ? `${journey.status}; ${journey.steps.map((step) => `${step.id}=${step.status}`).join(', ')}`
    : 'not_run';
  return [
    `请改进 ${origin} 的 Agent Readiness。`,
    '',
    '先读取 BFLabs Skill：',
    `- Agent Skills 索引：${PUBLIC_SKILL_BASE}/.well-known/agent-skills/index.json`,
    `- 根 Skill：${PUBLIC_SKILL_BASE}/skills/bflabs-agent-readiness`,
    `- 本次唯一子 Skill：${routeId === 'none' ? '无' : `${routeId} (${PUBLIC_SKILL_BASE}/skills/${routeId})`}`,
    '- 如果当前 Agent 无法联网读取 Skill，继续使用下方完整诊断事实，不要换成别的 Skill。',
    '',
    `目标：${origin}`,
    `扫描指纹：${fingerprint}`,
    `三轴：${readiness}`,
    `本次子 Skill 负责的失败项：${failed}`,
    `本次子 Skill 负责的未知项：${unknown}`,
    `Agent Journey：${journeySummary}`,
    '',
    '请按以下顺序执行：',
    '1. 先检查现有网站仓库，再修改文件。',
    routeId === 'none'
      ? '2. 当前没有 evidence-backed 失败项，不要为了提高分数制造无依据改动；只核对诊断事实。'
      : `2. 只修复 ${routeId} 负责的上述 evidence-backed 项目，不扩展到其他 Skill。`,
    '3. 保持现有产品行为和视觉方向，遵循涉及的公开协议与文件格式。',
    '4. 为每个行为变化补充或更新测试，并运行相关检查。',
    '5. 返回简短的变更摘要、测试结果，以及仍需产品决定、凭据或部署权限的事项。',
    '6. 不要自行部署。站点所有者部署后，再运行同一公网诊断并对比两个扫描指纹。',
    '',
    '边界：保留 unknown/blocked；除非另有独立证据，否则 AI visibility 与 Business outcome 必须保持 not_measured。',
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
  const journey = await runAgentJourney(origin, evidence, mcp, options.fetchOptions);
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
      owner_route: ownerRouteForCheck(check.id),
    })));
  const evidenceGaps = axes.flatMap((item) => item.checks
    .filter((check) => check.state === 'unknown')
    .map((check) => ({
      id: `gap_${check.id.toLowerCase()}`,
      axis: item.id,
      rule_id: check.id,
      title: check.label,
      state: 'unknown',
      owner_route: ownerRouteForCheck(check.id),
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
    journey,
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
    agent_journey: journey,
    readiness_report: readinessReport,
    evidence_ledger: evidenceLedger,
    quality_report: qualityReport,
    artifact_pack: artifactPack,
    disclaimers: {
      ai_visibility: 'not_measured',
      business_outcome: 'not_measured',
      actionability: 'A real compatible-browser task run is required for verified task completion.',
      agent_journey: 'A deterministic public-page journey is supporting readiness evidence, not AI visibility or business outcome.',
    },
  };
}
