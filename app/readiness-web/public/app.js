const form = document.querySelector('#scan-form');
const input = document.querySelector('#site-url');
const errorNode = document.querySelector('#url-error');
const progress = document.querySelector('#progress');
const submitButton = form.querySelector('button[type="submit"]');
const landing = document.querySelector('#landing');
const workspace = document.querySelector('#workspace');
const reportPanel = document.querySelector('#report-panel');
const deliveryPanel = document.querySelector('#delivery-panel');
const reportTab = document.querySelector('#report-tab');
const deliveryTab = document.querySelector('#delivery-tab');
const improvementPanel = document.querySelector('#improvement-panel');
const showMoreButton = document.querySelector('#show-more');
const publishCheckbox = document.querySelector('#publish-to-leaderboard');
const continueWorkBuddyButton = document.querySelector('#continue-workbuddy');
const homeLeaderboard = document.querySelector('#public-results');
const featuredScoresList = document.querySelector('#featured-scores-list');
const recentScoresList = document.querySelector('#recent-scores-list');
let currentReport = null;
let baselineReport = null;

const defaultHelp = '约 30 秒 · 只读取公开页面 · 默认不公开结果';

const axisDescriptions = {
  discoverable: '公开页面与机器入口是否能被找到。',
  understandable: '产品事实是否清晰、稳定、可核对。',
  actionable: 'Agent 是否拥有可发现的任务路径。',
};

const statusLabels = {
  pass: '通过',
  partial: '部分通过',
  fail: '未通过',
  unknown: '证据不足',
  blocked: '无法检查',
  not_applicable: '不适用',
};

const evidenceSignals = {
  has_title: '页面包含标题',
  has_h1: '页面包含主标题',
  has_canonical: '页面标明标准网址',
  has_json_ld: '页面包含结构化数据',
  has_cloudflare_webmcp_bridge: '网页提供 Agent 工具入口',
  has_native_webmcp_signal: '网页原生提供 Agent 工具入口',
};

const evidenceTypes = {
  'text/html': '网页',
  'text/plain': '文本',
  'application/json': '数据接口',
  'application/ld+json': '结构化数据',
  'application/xml': '站点地图',
  'text/xml': '站点地图',
};

function setStage(stage) {
  const order = ['validate', 'fetch', 'contracts', 'report'];
  const current = order.indexOf(stage);
  progress.hidden = false;
  form.setAttribute('aria-busy', 'true');
  progress.querySelectorAll('li').forEach((item, index) => {
    item.classList.toggle('active', index === current);
    item.classList.toggle('done', index < current);
  });
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  })[character]);
}

function displayHost(origin) {
  try {
    return new URL(origin).hostname;
  } catch {
    return origin;
  }
}

function displayEvidenceType(value) {
  const normalized = String(value || '').split(';')[0].trim().toLowerCase();
  return evidenceTypes[normalized] || (normalized ? '公开文件' : '未识别');
}

function displayEvidence(item) {
  const signals = (item.signals || []).map((signal) => evidenceSignals[signal]).filter(Boolean);
  return signals.join('、') || (item.excerpt || '').slice(0, 90) || '没有可显示的内容';
}

function scoreFor(entry, id) {
  const axis = (entry.axes || []).find((item) => item.id === id);
  return axis?.score == null ? '证据不足' : axis.score;
}

function renderScoreRows(list, entries) {
  if (!entries.length) {
    list.innerHTML = '<li class="home-leaderboard-empty">暂无公开结果</li>';
    return;
  }
  list.innerHTML = entries.map((entry) => `
    <li>
      <span class="home-leaderboard-rank">${escapeHtml(String(entry.rank).padStart(2, '0'))}</span>
      <a href="/leaderboard/${encodeURIComponent(entry.host)}">${escapeHtml(entry.host)}</a>
      <dl>
        <div><dt>可发现</dt><dd>${escapeHtml(scoreFor(entry, 'discoverable'))}</dd></div>
        <div><dt>可理解</dt><dd>${escapeHtml(scoreFor(entry, 'understandable'))}</dd></div>
        <div><dt>可操作</dt><dd>${escapeHtml(scoreFor(entry, 'actionable'))}</dd></div>
      </dl>
    </li>
  `).join('');
}

function renderHomeLeaderboard(entries) {
  renderScoreRows(featuredScoresList, entries.slice(0, 4));
  const recent = [...entries]
    .sort((left, right) => String(right.scanned_at).localeCompare(String(left.scanned_at)))
    .slice(0, 10);
  renderScoreRows(recentScoresList, recent);
}

async function loadHomeLeaderboard() {
  try {
    const response = await fetch('/api/v1/leaderboard', { headers: { Accept: 'application/json' } });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || '公开榜单读取失败');
    renderHomeLeaderboard(body.entries || []);
  } catch {
    featuredScoresList.innerHTML = '<li class="home-leaderboard-empty">暂时不可用</li>';
    recentScoresList.innerHTML = '<li class="home-leaderboard-empty">暂时不可用</li>';
  }
}

function activatePanel(panel) {
  const reportActive = panel === 'report';
  reportPanel.hidden = !reportActive;
  deliveryPanel.hidden = reportActive;
  reportTab.classList.toggle('is-active', reportActive);
  deliveryTab.classList.toggle('is-active', !reportActive);
  reportTab.setAttribute('aria-selected', String(reportActive));
  deliveryTab.setAttribute('aria-selected', String(!reportActive));
}

function renderAxes(axes) {
  document.querySelector('#axis-rail').innerHTML = axes.map((axis) => {
    const score = axis.score == null ? '—' : axis.score;
    const width = axis.score == null ? 0 : Math.max(0, Math.min(100, axis.score));
    const suffix = axis.score == null ? '<small class="score-unavailable">证据不足</small>' : '<small>/100</small>';
    return `
      <article class="score-card" data-status="${escapeHtml(axis.status)}">
        <div class="score-meta">
          <span>${escapeHtml(axis.label)}</span>
          <span class="score-tag">${escapeHtml(statusLabels[axis.status] || axis.status)}</span>
        </div>
        <p class="score-number">${escapeHtml(score)}${suffix}</p>
        <div class="score-track" aria-hidden="true"><i style="width:${width}%"></i></div>
        <p class="score-description">${escapeHtml(axisDescriptions[axis.id] || '')}</p>
        <details>
          <summary>查看 ${axis.checks.length} 条判断</summary>
          <ul>${axis.checks.map((check) => `<li><strong>${escapeHtml(statusLabels[check.state] || '待确认')}</strong> · ${escapeHtml(check.label)}</li>`).join('')}</ul>
        </details>
      </article>
    `;
  }).join('');
}

function renderCompactList(selector, items, renderItem, emptyText) {
  document.querySelector(selector).innerHTML = items.length
    ? items.map((item) => `<article>${renderItem(item)}</article>`).join('')
    : `<p>${escapeHtml(emptyText)}</p>`;
}

function scoreText(report) {
  return report.axes.map((axis) => `${axis.label} ${axis.score == null ? 'N/A' : axis.score}`).join(' · ');
}

function renderComparison(report) {
  const sameTarget = baselineReport?.target.canonical_origin === report.target.canonical_origin;
  const isNewScan = baselineReport?.scan_fingerprint !== report.scan_fingerprint
    || baselineReport?.scan.completed_at !== report.scan.completed_at;
  if (!sameTarget || !isNewScan) return;

  const beforeById = new Map(baselineReport.axes.map((axis) => [axis.id, axis]));
  const deltas = report.axes.map((axis) => {
    const before = beforeById.get(axis.id)?.score;
    const delta = before == null || axis.score == null ? null : axis.score - before;
    return `${axis.label} ${delta == null ? 'N/A' : `${delta >= 0 ? '+' : ''}${delta}`}`;
  });
  const comparableScores = report.axes.map((axis) => axis.score).filter((score) => score != null);
  const progressValue = comparableScores.length
    ? Math.round(comparableScores.reduce((sum, score) => sum + score, 0) / comparableScores.length)
    : 0;

  document.querySelector('#delivery-context').textContent = `${report.target.canonical_origin} 的两次诊断结果对比`;
  document.querySelector('#delta-label').textContent = '本次变化';
  document.querySelector('#delta-value').textContent = '改动前 → 改动后';
  document.querySelector('#delta-summary').textContent = deltas.join(' · ');
  document.querySelector('#delta-progress').style.width = `${progressValue}%`;
  document.querySelector('#before-value').textContent = '首次检查';
  document.querySelector('#before-summary').textContent = scoreText(baselineReport);
  document.querySelector('#after-value').textContent = '复测';
  document.querySelector('#after-summary').textContent = scoreText(report);
  document.querySelector('#delivery-notice-title').textContent = '修复前后的结果来自两次独立检查';
  document.querySelector('#delivery-notice-copy').textContent = '这里只证明网站准备度发生变化，外部 AI 平台可见度与业务结果仍需单独测量。';
  document.querySelector('#report-status').textContent = '已复测';
}

function resetComparisonExample() {
  document.querySelector('#delivery-context').textContent = '示例：从首次检查到改完复测';
  document.querySelector('#delta-label').textContent = '示例变化';
  document.querySelector('#delta-value').innerHTML = '33<i>→</i>78';
  document.querySelector('#delta-summary').textContent = '示例：可理解 +45 · 解决 4/7 个问题';
  document.querySelector('#delta-progress').style.width = '78%';
  document.querySelector('#before-value').innerHTML = '几乎<br>读不到';
  document.querySelector('#before-summary').textContent = '页面正文过少 · 没有稳定答案页';
  document.querySelector('#after-value').innerHTML = '事实<br>可核对';
  document.querySelector('#after-summary').textContent = '正文可直接读取 · 答案页 · 接入路径';
  document.querySelector('#delivery-notice-title').textContent = '没有修复前后的复测对比，就不算完成本阶段';
  document.querySelector('#delivery-notice-copy').textContent = '下一阶段只修仍开放的项。';
}

function updateContactLink(report) {
  const subject = `BFLabs Agent Readiness 咨询：${displayHost(report.target.canonical_origin)}`;
  const body = [
    `诊断目标：${report.target.canonical_origin}`,
    `诊断记录编号：${report.scan_fingerprint}`,
    `准备度：${scoreText(report)}`,
    '',
    '我希望了解：跨系统改站 / 多平台 GEO 抽样 / 持续监测 / 业务结果归因（请保留适用项）',
  ].join('\n');
  document.querySelector('#contact-bflabs').href = `mailto:hello@bflabs.cn?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

function renderJourney(journey) {
  const status = document.querySelector('#journey-status');
  const task = document.querySelector('#journey-task');
  const steps = document.querySelector('#journey-steps');
  if (!journey) {
    status.textContent = '未运行';
    task.textContent = '本次没有可显示的 Agent 任务试跑。';
    steps.innerHTML = '';
    return;
  }
  status.textContent = journey.status === 'pass' ? '已通过' : journey.status === 'blocked' ? '无法完成' : '有缺口';
  task.textContent = journey.task;
  steps.innerHTML = journey.steps.map((step) => `
    <li data-status="${escapeHtml(step.status)}">
      <strong>${escapeHtml(step.label)}</strong>
      <span>${escapeHtml(statusLabels[step.status] || '待确认')}</span>
      <p>${escapeHtml(step.observation)}</p>
    </li>
  `).join('');
}

function renderLeaderboardPublication(publication) {
  const node = document.querySelector('#leaderboard-publication');
  if (publication?.status === 'published') {
    node.innerHTML = '已加入 <a href="/leaderboard">公开榜单</a>。';
    loadHomeLeaderboard();
  } else if (publication?.status === 'not_published') {
    node.textContent = '本次诊断未完整完成，因此没有加入榜单。';
  } else if (publication?.status === 'unavailable') {
    node.textContent = '你选择了公开，但榜单存储尚未配置，本次没有上榜。';
  } else {
    node.textContent = '本次结果未公开到榜单。';
  }
}

function renderReport(report) {
  currentReport = report;
  const host = displayHost(report.target.canonical_origin);
  const evidenceIncomplete = report.scan.status !== 'complete' || report.axes.some((axis) => axis.score == null);
  landing.hidden = true;
  homeLeaderboard.hidden = true;
  workspace.hidden = false;
  progress.hidden = true;
  form.setAttribute('aria-busy', 'false');
  activatePanel('report');
  improvementPanel.hidden = true;
  showMoreButton.textContent = '查看改进方案';
  showMoreButton.setAttribute('aria-expanded', 'false');

  document.querySelector('#report-origin').textContent = host;
  document.querySelector('#delivery-origin').textContent = host;
  document.querySelector('#report-status').textContent = report.scan.status === 'complete' ? '完成' : '报告不完整';
  document.querySelector('#report-fingerprint').textContent = report.scan_fingerprint;
  renderAxes(report.axes);
  renderJourney(report.agent_journey);
  renderLeaderboardPublication(report.leaderboard_publication);
  updateContactLink(report);

  const findings = document.querySelector('#findings');
  findings.innerHTML = report.findings.length
    ? report.findings.map((finding) => `
      <li>
        <span>${escapeHtml(finding.title)}</span>
      </li>
    `).join('')
    : evidenceIncomplete
      ? '<li class="finding-empty">本次证据不足，暂时无法判断是否存在问题。外部 AI 平台表现仍需单独验证。</li>'
      : '<li class="finding-empty">本次检查没有发现明确问题。外部 AI 平台表现仍需单独验证。</li>';

  document.querySelector('#evidence-body').innerHTML = report.evidence.map((item) => `
    <tr>
      <td><code>${escapeHtml(item.path)}</code></td>
      <td>${escapeHtml(item.status_code)}</td>
      <td>${escapeHtml(displayEvidenceType(item.content_type))}</td>
      <td>${escapeHtml(displayEvidence(item))}</td>
    </tr>
  `).join('');

  renderCompactList('#evidence-gaps', report.evidence_gaps || [], (item) => `
    <p>${escapeHtml(item.title)} · ${escapeHtml(statusLabels[item.state] || '待确认')}</p>
  `, '已检查的公开入口证据完整。');

  renderCompactList('#opportunities', report.opportunities || [], (item) => `
    <p>${escapeHtml(item.title)}</p>
  `, '当前没有由问题或证据缺口产生的改进机会。');

  document.querySelector('#skill-routes').innerHTML = (report.skill_routes || []).length
    ? report.skill_routes.map((item, index) => `<a href="${escapeHtml(item.href)}">${report.skill_routes.length > 1 ? `查看修复指南 ${index + 1}` : '查看修复指南'}</a>`).join('')
    : '<span>当前没有需要修复的问题</span>';

  const promptButton = document.querySelector('#copy-agent-prompt');
  const hasRepair = (report.skill_routes || []).length > 0;
  promptButton.textContent = hasRepair ? '复制给 Agent，开始修复' : evidenceIncomplete ? '复制给 Agent，继续核对' : '复制给 Agent，核对结果';
  document.querySelector('#agent-action-copy').textContent = hasRepair
    ? '提示词已带上本次诊断证据和修复方法。'
    : evidenceIncomplete
      ? '本次证据不足，提示词会让 Agent 继续核对缺失信息。'
      : '本次没有发现由公开证据支持的问题，提示词会让 Agent 只核对结果。';
  document.querySelector('#copy-status').textContent = '';
  document.querySelector('#handoff-status').textContent = '';
  continueWorkBuddyButton.disabled = false;
  continueWorkBuddyButton.textContent = '在 WorkBuddy 中继续';

  resetComparisonExample();
  renderComparison(report);

  window.scrollTo({ top: 0, behavior: 'auto' });
}

async function pollReport(statusUrl) {
  for (let attempt = 0; attempt < 90; attempt += 1) {
    const response = await fetch(statusUrl, { headers: { Accept: 'application/json' } });
    const report = await response.json();
    if (!response.ok) throw new Error(report.detail || report.error || '诊断失败');
    if (report.status === 'failed') throw new Error(report.error || '诊断失败');
    if (['complete', 'partial', 'blocked'].includes(report.status)) return report;
    setStage(attempt < 2 ? 'validate' : attempt < 9 ? 'fetch' : 'contracts');
    await new Promise((resolve) => setTimeout(resolve, 700));
  }
  throw new Error('诊断超过本地等待时间');
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  errorNode.textContent = '';
  const value = input.value.trim();
  if (!value) {
    errorNode.textContent = '请输入公开域名。';
    input.focus();
    return;
  }

  submitButton.disabled = true;
  setStage('validate');
  try {
    const response = await fetch('/api/v1/scans', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: value,
        publish_to_leaderboard: publishCheckbox.checked,
        prepare_workbuddy_handoff: true,
      }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || body.error || '无法创建诊断');
    const report = body.status_url ? await pollReport(body.status_url) : (body.report || body);
    setStage('report');
    renderReport(report);
  } catch (error) {
    progress.hidden = true;
    form.setAttribute('aria-busy', 'false');
    errorNode.textContent = error.message;
  } finally {
    submitButton.disabled = false;
  }
});

reportTab.addEventListener('click', () => activatePanel('report'));
deliveryTab.addEventListener('click', () => activatePanel('delivery'));
document.querySelector('#show-delivery').addEventListener('click', () => {
  activatePanel('delivery');
  workspace.scrollIntoView({ behavior: 'smooth' });
});

document.querySelector('#rescan').addEventListener('click', () => {
  baselineReport = null;
  workspace.hidden = true;
  landing.hidden = false;
  homeLeaderboard.hidden = false;
  errorNode.textContent = '';
  progress.hidden = true;
  submitButton.textContent = '开始诊断';
  document.querySelector('#url-help').textContent = defaultHelp;
  input.focus();
  window.scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
});

document.querySelector('#save-baseline').addEventListener('click', () => {
  if (!currentReport) return;
  baselineReport = structuredClone(currentReport);
  workspace.hidden = true;
  landing.hidden = false;
  homeLeaderboard.hidden = false;
  input.value = displayHost(currentReport.target.canonical_origin);
  submitButton.textContent = '复测并对比';
  document.querySelector('#url-help').textContent = '基线只保存在当前页面，关闭后会消失 · 优化完成后点击复测';
  input.focus();
  window.scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
});

showMoreButton.addEventListener('click', () => {
  const opening = improvementPanel.hidden;
  improvementPanel.hidden = !opening;
  showMoreButton.textContent = opening ? '收起改进方案' : '查看改进方案';
  showMoreButton.setAttribute('aria-expanded', String(opening));
});

async function downloadArtifactPack() {
  if (!currentReport) return;
  const blob = new Blob([`${JSON.stringify(currentReport.artifact_pack, null, 2)}\n`], { type: 'application/json' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${displayHost(currentReport.target.canonical_origin)}-agent-readiness-artifact-pack.json`;
  link.click();
  URL.revokeObjectURL(link.href);
}

document.querySelector('#download-report').addEventListener('click', async () => {
  await downloadArtifactPack();
});

document.querySelector('#copy-agent-prompt').addEventListener('click', async () => {
  if (!currentReport?.agent_prompt) return;
  const status = document.querySelector('#copy-status');
  try {
    await navigator.clipboard.writeText(currentReport.agent_prompt);
    status.textContent = '已复制。粘贴到 Codex、Cursor、Claude Code 或 WorkBuddy 即可。';
  } catch {
    status.textContent = '复制失败，请允许剪贴板访问后重试。';
  }
});

continueWorkBuddyButton.addEventListener('click', () => {
  if (!currentReport) return;
  const status = document.querySelector('#handoff-status');
  status.textContent = '';
  try {
    const handoff = currentReport.geo_handoff;
    const continueUrl = new URL(handoff?.continue_url || '');
    const fragmentToken = new URLSearchParams(continueUrl.hash.slice(1)).get('token');
    if (continueUrl.origin !== 'https://wb.bflabs.app' || continueUrl.pathname !== '/geo/claim' || continueUrl.search || !/^[A-Za-z0-9_-]{43}$/.test(fragmentToken || '')) {
      throw new Error('handoff unavailable');
    }
    if (!handoff.expires_at || Date.parse(handoff.expires_at) <= Date.now()) throw new Error('handoff expired');
    window.location.assign(handoff.continue_url);
  } catch {
    status.textContent = '继续链接暂时不可用，请复制给 Agent。';
    document.querySelector('#copy-agent-prompt').focus();
  }
});

loadHomeLeaderboard();
