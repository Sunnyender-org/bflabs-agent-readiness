const form = document.querySelector('#scan-form');
const input = document.querySelector('#site-url');
const errorNode = document.querySelector('#url-error');
const progress = document.querySelector('#progress');
const submitButton = form.querySelector('button[type="submit"]');
const emptyState = document.querySelector('#empty-state');
const reportNode = document.querySelector('#report');
let currentReport = null;

const axisDescriptions = {
  discoverable: '公开页面与机器入口是否能被找到',
  understandable: '产品事实是否清晰、稳定、可核对',
  actionable: 'Agent 是否拥有可发现的任务路径',
};

function setStage(stage) {
  const order = ['validate', 'fetch', 'contracts', 'report'];
  const current = order.indexOf(stage);
  progress.hidden = false;
  progress.querySelectorAll('li').forEach((item, index) => {
    item.classList.toggle('active', index === current);
    item.classList.toggle('done', index < current);
  });
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"]/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;',
  })[character]);
}

function renderAxes(axes) {
  document.querySelector('#axis-rail').innerHTML = axes.map((axis, index) => `
    <article class="axis" data-axis="${escapeHtml(axis.id)}">
      <span class="axis-index">0${index + 1} / ${escapeHtml(axis.status)}</span>
      <div class="axis-score"><strong>${axis.score ?? 'N/A'}</strong><span>/100</span></div>
      <h3>${escapeHtml(axis.label)}</h3>
      <p>${escapeHtml(axisDescriptions[axis.id])}</p>
      <details>
        <summary>查看 ${axis.checks.length} 条判断</summary>
        <ul>${axis.checks.map((check) => `<li><strong>${escapeHtml(check.state)}</strong> · ${escapeHtml(check.label)}</li>`).join('')}</ul>
      </details>
    </article>
  `).join('');
}

function renderReport(report) {
  currentReport = report;
  emptyState.hidden = true;
  reportNode.hidden = false;
  progress.hidden = true;
  document.querySelector('#report-origin').textContent = report.target.canonical_origin;
  document.querySelector('#report-status').textContent = report.scan.status === 'complete' ? '公开诊断完成' : '报告不完整';
  document.querySelector('#report-fingerprint').textContent = report.scan_fingerprint;
  renderAxes(report.axes);

  const findings = document.querySelector('#findings');
  findings.innerHTML = report.findings.length
    ? report.findings.map((finding) => `
      <article class="finding">
        <code>${escapeHtml(finding.rule_id)}</code>
        <div><h4>${escapeHtml(finding.title)}</h4><p>${escapeHtml(finding.state)} · 交给 ${escapeHtml(finding.owner_route)}</p></div>
      </article>
    `).join('')
    : '<p>本次固定入口没有发现失败谓词。真实平台表现仍未测量。</p>';

  document.querySelector('#evidence-body').innerHTML = report.evidence.map((item) => `
    <tr>
      <td><code>${escapeHtml(item.path)}</code></td>
      <td>${escapeHtml(item.status_code)}</td>
      <td>${escapeHtml(item.content_type || 'unknown')}</td>
      <td>${escapeHtml(item.signals.join(', ') || item.excerpt.slice(0, 90) || '无可显示信号')}</td>
    </tr>
  `).join('');
  reportNode.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
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
    errorNode.textContent = error.message;
  } finally {
    submitButton.disabled = false;
  }
});

document.querySelector('#download-report').addEventListener('click', () => {
  if (!currentReport) return;
  const blob = new Blob([`${JSON.stringify(currentReport, null, 2)}\n`], { type: 'application/json' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${new URL(currentReport.target.canonical_origin).hostname}-geo-readiness.json`;
  link.click();
  URL.revokeObjectURL(link.href);
});
