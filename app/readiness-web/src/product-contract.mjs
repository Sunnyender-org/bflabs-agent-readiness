export const PUBLIC_BASE_URL = 'https://readiness.bflabs.cn';

const PROBLEM_MAP = [
  [/API 路径不存在|api route not found/i, ['api_route_not_found', 404, 'API 路径不存在', '读取 https://readiness.bflabs.cn/openapi.json 后使用已发布的版本化路径。']],
  [/方法不允许|method not allowed/i, ['method_not_allowed', 405, '请求方法不允许', '读取 OpenAPI 后改用支持的方法。']],
  [/报告不存在|report not found/i, ['report_not_found', 404, '报告不存在', '重新运行诊断以生成当前公开状态。']],
  [/榜单记录不存在|leaderboard entry not found/i, ['leaderboard_entry_not_found', 404, '榜单记录不存在', '返回公开榜单查看当前仍在展示的域名。']],
  [/opt-out/i, ['target_opted_out', 403, '目标已拒绝诊断', '尊重目标站点的公开 opt-out；如你是站点所有者，请先移除该文件后重试。']],
  [/请求过于频繁|rate.?limit/i, ['rate_limit_exceeded', 429, '请求过于频繁', '等待限流窗口结束后重试。']],
  [/正文超过|too large/i, ['request_too_large', 413, '请求正文过大', '只提交目标 URL 和必要的布尔选项。']],
  [/超时|timeout|AbortError/i, ['scan_timeout', 504, '目标响应超时', '稍后重试，或先确认目标公开页面可以稳定访问。']],
  [/JSON|Unexpected token/i, ['invalid_json', 400, '请求格式无效', '发送 application/json，并检查 JSON 语法。']],
  [/请输入|只支持|不接受|不能包含|不允许|不是公开|不安全|解析到了/i, ['unsafe_target', 400, '目标不可诊断', '只提交你有权检查的公开 HTTP 或 HTTPS 域名。']],
];

export function problemDetails(error, instance = null) {
  const message = error?.message || String(error || '扫描失败');
  const mapped = PROBLEM_MAP.find(([pattern]) => pattern.test(`${error?.name || ''} ${message}`));
  const [code, defaultStatus, title, resolution] = mapped?.[1] || [
    error?.code || 'scan_failed',
    error?.status || 400,
    '诊断未完成',
    '检查目标 URL 后重试；若持续失败，请联系 hello@bflabs.cn。',
  ];
  const status = error?.status || defaultStatus;
  return {
    type: `${PUBLIC_BASE_URL}/problems/${code}`,
    title,
    status,
    code,
    detail: message,
    resolution,
    ...(instance ? { instance } : {}),
  };
}

export function reportToMarkdown(report) {
  const score = (axis) => axis.score == null ? 'N/A' : `${axis.score}/100`;
  const axisLines = report.axes.map((axis) => `- ${axis.label}: ${score(axis)} (${axis.status})`).join('\n');
  const findingLines = report.findings.length
    ? report.findings.map((item, index) => `${index + 1}. ${item.rule_id} [${item.state}] ${item.title}`).join('\n')
    : '无 evidence-backed 失败项。';
  const journey = report.agent_journey;
  const journeyLines = journey?.steps?.length
    ? journey.steps.map((step, index) => `${index + 1}. ${step.label}: ${step.status}，${step.observation}`).join('\n')
    : '未运行。';
  const route = report.skill_routes?.[0];
  return `# BFLabs Agent Readiness：${report.target.canonical_origin}

扫描时间：${report.scan.completed_at}
扫描指纹：${report.scan_fingerprint}

## Readiness

${axisLines}

## 当前问题

${findingLines}

## Agent Journey

任务：${journey?.task || '未运行'}
状态：${journey?.status || 'not_run'}

${journeyLines}

## 下一步

${route ? `使用 ${route.id}：${PUBLIC_BASE_URL}${route.href}` : '当前没有 evidence-backed 子 Skill 修复任务。'}

根 Skill：${PUBLIC_BASE_URL}/skills/bflabs-agent-readiness
Agent Skills 索引：${PUBLIC_BASE_URL}/.well-known/agent-skills/index.json

## 边界

- AI visibility：not_measured
- Business outcome：not_measured
- Agent Journey 是本次公开页面的确定性试跑证据，不是外部 AI 平台可见度。
`;
}

export function wantsMarkdown(request) {
  return /(?:^|,)\s*text\/markdown(?:\s*;|\s*,|$)/i.test(request.headers.get('accept') || '');
}

export function methodology() {
  return {
    schema_version: '1.0.0',
    product: 'BFLabs Agent Readiness',
    axes: [
      { id: 'discoverable', label: '可发现', meaning: '公开入口是否能被 Agent 找到和读取' },
      { id: 'understandable', label: '可理解', meaning: '产品、事实和关键意图是否能被稳定提取' },
      { id: 'actionable', label: '可操作', meaning: '是否存在稳定的人类或 Agent 操作入口' },
    ],
    ranking: '公开榜单按通过轴数、最弱轴得分、三轴平均分依次排序；不生成隐藏总分。',
    boundaries: {
      ai_visibility: 'not_measured by readiness scan',
      business_outcome: 'not_measured by readiness scan',
      agent_journey: 'supporting evidence only; never changes readiness scores',
    },
  };
}

const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (character) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
})[character]);

export function leaderboardSharePage(entry) {
  const axes = entry.axes.map((axis) => `<article class="score-card" data-status="${escapeHtml(axis.status)}"><div class="score-meta"><span>${escapeHtml(axis.label)}</span><span class="score-tag">${escapeHtml(axis.status)}</span></div><p class="score-number">${axis.score == null ? 'N/A' : escapeHtml(axis.score)}${axis.score == null ? '<small>证据不足</small>' : '<small>/100</small>'}</p></article>`).join('');
  const canonical = `${PUBLIC_BASE_URL}/leaderboard/${encodeURIComponent(entry.host)}`;
  const displayDate = new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Shanghai' }).format(new Date(entry.scanned_at));
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHtml(entry.host)} · BFLabs Agent Readiness 榜单</title><meta name="description" content="${escapeHtml(entry.host)} 主动公开的 BFLabs Agent Readiness 三轴结果。"><link rel="canonical" href="${canonical}"><link rel="icon" href="/bf-mark.svg" type="image/svg+xml"><link rel="stylesheet" href="/styles.css"></head><body><header class="site-header"><a class="brand" href="/"><img src="/bf-mark.svg" alt=""><span class="brand-copy"><strong>BF LABS</strong><small>Agent Readiness</small></span></a><nav class="site-nav"><a href="/leaderboard">公开榜单</a><a href="https://skills.bflabs.cn/catalog.html#geo">SkillHub</a></nav></header><main class="app-shell leaderboard-shell"><header class="leaderboard-hero"><span>OPT-IN PUBLIC RESULT</span><h1>${escapeHtml(entry.host)}</h1><p>这是该域名主动公开的三轴诊断摘要，扫描于 ${escapeHtml(displayDate)}。不包含 AI visibility 或 Business outcome。</p><a class="button button-primary" href="/">重新诊断</a></header><section class="score-grid" aria-label="三轴结果">${axes}</section><p class="leaderboard-note">扫描指纹：${escapeHtml(entry.scan_fingerprint)}</p></main><footer class="site-footer"><span>BFLabs Agent Readiness</span><nav><a href="/leaderboard">返回榜单</a><a href="/privacy">隐私边界</a></nav></footer></body></html>`;
}

export function leaderboardIndexPage(board) {
  const rows = board.entries.length ? board.entries.map((entry) => {
    const axes = Object.fromEntries(entry.axes.map((axis) => [axis.id, axis]));
    const score = (id) => axes[id]?.score == null ? 'N/A' : axes[id].score;
    const displayDate = new Intl.DateTimeFormat('zh-CN', { dateStyle: 'short', timeStyle: 'short', timeZone: 'Asia/Shanghai' }).format(new Date(entry.scanned_at));
    return `<li class="leaderboard-row"><span class="leaderboard-rank">${String(entry.rank).padStart(2, '0')}</span><div class="leaderboard-site"><strong><a href="/leaderboard/${encodeURIComponent(entry.host)}">${escapeHtml(entry.host)}</a></strong><small>${escapeHtml(displayDate)}</small></div><dl class="leaderboard-axes"><div><dt>可发现</dt><dd>${escapeHtml(score('discoverable'))}</dd></div><div><dt>可理解</dt><dd>${escapeHtml(score('understandable'))}</dd></div><div><dt>可操作</dt><dd>${escapeHtml(score('actionable'))}</dd></div></dl></li>`;
  }).join('') : '<li class="leaderboard-empty">还没有用户选择公开结果。你可以成为第一个。</li>';
  const storageNote = board.storage === 'ready'
    ? '榜单仅保存公开摘要，不保存证据正文、IP 或 Agent 提示词。'
    : '榜单存储尚未配置，当前不会公开任何结果。';
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>公开榜单 · BFLabs Agent Readiness</title><meta name="description" content="BFLabs Agent Readiness 公开榜单，只收录用户主动公开的三轴诊断结果。"><link rel="canonical" href="${PUBLIC_BASE_URL}/leaderboard"><link rel="icon" href="/bf-mark.svg" type="image/svg+xml"><link rel="stylesheet" href="/styles.css"></head><body><header class="site-header"><a class="brand" href="/"><img src="/bf-mark.svg" alt=""><span class="brand-copy"><strong>BF LABS</strong><small>Agent Readiness</small></span></a><nav class="site-nav"><a href="/">开始诊断</a><a href="https://skills.bflabs.cn/catalog.html#geo">SkillHub</a></nav></header><main class="app-shell leaderboard-shell"><header class="leaderboard-hero"><span>OPT-IN PUBLIC INDEX</span><h1>公开榜单</h1><p>只展示用户主动公开的当前三轴结果。排名不混入 AI visibility 或 Business outcome。</p><a class="button button-primary" href="/">检查你的网站</a></header><section aria-labelledby="ranking-title"><div class="leaderboard-heading"><h2 id="ranking-title">Agent Readiness</h2><p>依次按通过轴数、最弱轴、三轴平均分排序，不生成隐藏总分。</p></div><ol class="leaderboard-list">${rows}</ol><p class="leaderboard-note">${escapeHtml(storageNote)}</p></section></main><footer class="site-footer"><span>BFLabs Agent Readiness</span><nav><a href="/privacy">隐私边界</a><a href="/terms">使用边界</a></nav></footer></body></html>`;
}
