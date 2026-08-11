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
    const report = await pollReport(body.status_url);
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
  workspace.hidden = true;
  landing.hidden = false;
  errorNode.textContent = '';
  progress.hidden = true;
  input.focus();
  window.scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
});

showMoreButton.addEventListener('click', () => {
  const opening = improvementPanel.hidden;
  improvementPanel.hidden = !opening;
  showMoreButton.textContent = opening ? '收起' : '如何改进';
  showMoreButton.setAttribute('aria-expanded', String(opening));
});

document.querySelector('#download-report').addEventListener('click', async () => {
  if (!currentReport) return;
  const response = await fetch(`/api/scans/${encodeURIComponent(currentReport.report_id)}/artifact-pack`, {
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) return;
  const blob = await response.blob();
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${displayHost(currentReport.target.canonical_origin)}-agent-readiness-artifact-pack.json`;
  link.click();
  URL.revokeObjectURL(link.href);
});

document.querySelector('#copy-agent-prompt').addEventListener('click', async () => {
  if (!currentReport?.agent_prompt) return;
  const status = document.querySelector('#copy-status');
  try {
    await navigator.clipboard.writeText(currentReport.agent_prompt);
    status.textContent = '已复制，可直接交给你的 Agent。';
  } catch {
    status.textContent = '复制失败，请从 Artifact Pack 读取优化指令。';
  }
});
