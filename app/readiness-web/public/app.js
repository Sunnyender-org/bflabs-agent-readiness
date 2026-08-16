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
let currentReport = null;
let baselineReport = null;

const defaultHelp = '30 秒出报告 · 公开页面 ONLY · 零登录';

const axisDescriptions = {
  discoverable: '公开页面与机器入口是否能被找到。',
  understandable: '产品事实是否清晰、稳定、可核对。',
  actionable: 'Agent 是否拥有可发现的任务路径。',
};

const statusLabels = {
  pass: 'pass',
  partial: 'partial',
  fail: 'fail',
  unknown: 'unknown',
  blocked: 'blocked',
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
    const score = axis.score == null ? 'N/A' : axis.score;
    const width = axis.score == null ? 0 : Math.max(0, Math.min(100, axis.score));
    const suffix = axis.score == null ? '<small>证据不足</small>' : '<small>/100</small>';
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
          <ul>${axis.checks.map((check) => `<li><strong>${escapeHtml(check.state)}</strong> · ${escapeHtml(check.label)}</li>`).join('')}</ul>
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

  document.querySelector('#delivery-context').textContent = `本地实测：${report.target.canonical_origin} 的同站复测对比`;
  document.querySelector('#delta-label').textContent = '真实三轴 Δ';
  document.querySelector('#delta-value').textContent = 'Before → After';
  document.querySelector('#delta-summary').textContent = deltas.join(' · ');
  document.querySelector('#delta-progress').style.width = `${progressValue}%`;
  document.querySelector('#before-value').textContent = '基线';
  document.querySelector('#before-summary').textContent = scoreText(baselineReport);
  document.querySelector('#after-value').textContent = '复测';
  document.querySelector('#after-summary').textContent = scoreText(report);
  document.querySelector('#delivery-notice-title').textContent = 'Before / After 已由两次独立扫描生成';
  document.querySelector('#delivery-notice-copy').textContent = '这只证明准备度变化，AI visibility 与 Business outcome 仍需独立测量。';
  document.querySelector('#report-status').textContent = '已复测';
}

function resetComparisonExample() {
  document.querySelector('#delivery-context').textContent = '付费示例：阶段清楚，变化可见';
  document.querySelector('#delta-label').textContent = '示例 Δ';
  document.querySelector('#delta-value').innerHTML = '33<i>→</i>78';
  document.querySelector('#delta-summary').textContent = '示例：可理解 +45 · 关闭 4/7 缺口';
  document.querySelector('#delta-progress').style.width = '78%';
  document.querySelector('#before-value').innerHTML = '几乎<br>读不到';
  document.querySelector('#before-summary').textContent = 'HTML 正文薄 · 无稳定答案页';
  document.querySelector('#after-value').innerHTML = '事实<br>可核对';
  document.querySelector('#after-summary').textContent = 'SSR 正文 · 答案页 · 接入路径';
  document.querySelector('#delivery-notice-title').textContent = '没有 Before / After，就不算完成本阶段';
  document.querySelector('#delivery-notice-copy').textContent = '下一阶段只修仍开放的项。';
}

function updateContactLink(report) {
  const subject = `BFLabs Agent Readiness 咨询：${displayHost(report.target.canonical_origin)}`;
  const body = [
    `诊断目标：${report.target.canonical_origin}`,
    `扫描指纹：${report.scan_fingerprint}`,
    `准备度：${scoreText(report)}`,
    '',
    '我希望了解：跨系统改站 / 多平台 GEO 抽样 / 持续监测 / 业务结果归因（请保留适用项）',
  ].join('\n');
  document.querySelector('#contact-bflabs').href = `mailto:hello@bflabs.cn?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

function renderReport(report) {
  currentReport = report;
  const host = displayHost(report.target.canonical_origin);
  landing.hidden = true;
  workspace.hidden = false;
  progress.hidden = true;
  form.setAttribute('aria-busy', 'false');
  activatePanel('report');
  improvementPanel.hidden = true;
  showMoreButton.textContent = '如何改进';
  showMoreButton.setAttribute('aria-expanded', 'false');

  document.querySelector('#report-origin').textContent = host;
  document.querySelector('#delivery-origin').textContent = host;
  document.querySelector('#report-status').textContent = report.scan.status === 'complete' ? '完成' : '报告不完整';
  document.querySelector('#report-fingerprint').textContent = report.scan_fingerprint;
  renderAxes(report.axes);
  updateContactLink(report);

  const findings = document.querySelector('#findings');
  findings.innerHTML = report.findings.length
    ? report.findings.map((finding) => `
      <li>
        <code>${escapeHtml(finding.rule_id)}</code>
        <span>${escapeHtml(finding.title)}</span>
        <small>${escapeHtml(finding.owner_route)}</small>
      </li>
    `).join('')
    : '<li class="finding-empty">本次固定入口没有发现失败谓词。真实平台表现仍未测量。</li>';

  document.querySelector('#evidence-body').innerHTML = report.evidence.map((item) => `
    <tr>
      <td><code>${escapeHtml(item.path)}</code></td>
      <td>${escapeHtml(item.status_code)}</td>
      <td>${escapeHtml(item.content_type || 'unknown')}</td>
      <td>${escapeHtml((item.signals || []).join(', ') || (item.excerpt || '').slice(0, 90) || '无可显示信号')}</td>
    </tr>
  `).join('');

  renderCompactList('#evidence-gaps', report.evidence_gaps || [], (item) => `
    <code>${escapeHtml(item.rule_id)}</code>
    <p>${escapeHtml(item.title)} · ${escapeHtml(item.state)}</p>
  `, '固定入口证据完整，没有未知谓词。');

  renderCompactList('#opportunities', report.opportunities || [], (item) => `
    <code>${escapeHtml(item.state)}</code>
    <p>${escapeHtml(item.title)} · ${escapeHtml(item.route)}</p>
  `, '当前没有由失败或未知谓词产生的机会。');

  document.querySelector('#skill-routes').innerHTML = (report.skill_routes || []).length
    ? report.skill_routes.map((item) => `<a href="${escapeHtml(item.href)}">${escapeHtml(item.id)}</a>`).join('')
    : '<span>当前无需额外子 Skill</span>';

  resetComparisonExample();
  renderComparison(report);

  window.scrollTo({ top: 0, behavior: 'auto' });
}

async function pollReport(statusUrl) {
  for (let attempt = 0; attempt < 90; attempt += 1) {
    const response = await fetch(statusUrl, { headers: { Accept: 'application/json' } });
    const report = await response.json();
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
    const response = await fetch('/api/scans', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: value }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || '无法创建诊断');
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
  errorNode.textContent = '';
  progress.hidden = true;
  submitButton.textContent = '检查';
  document.querySelector('#url-help').textContent = defaultHelp;
  input.focus();
  window.scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
});

document.querySelector('#save-baseline').addEventListener('click', () => {
  if (!currentReport) return;
  baselineReport = structuredClone(currentReport);
  workspace.hidden = true;
  landing.hidden = false;
  input.value = displayHost(currentReport.target.canonical_origin);
  submitButton.textContent = '复测并对比';
  document.querySelector('#url-help').textContent = '基线仅保存在当前页面内存 · 优化完成后点击复测';
  input.focus();
  window.scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
});

showMoreButton.addEventListener('click', () => {
  const opening = improvementPanel.hidden;
  improvementPanel.hidden = !opening;
  showMoreButton.textContent = opening ? '收起' : '如何改进';
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
    await downloadArtifactPack();
    await navigator.clipboard.writeText(currentReport.agent_prompt);
    status.textContent = 'Artifact Pack 已下载，指令已复制。把两者一起交给 Agent。';
  } catch {
    status.textContent = 'Artifact Pack 已尝试下载；复制失败，请手动附上报告。';
  }
});
