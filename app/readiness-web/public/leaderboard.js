const list = document.querySelector('#leaderboard-list');
const note = document.querySelector('#leaderboard-note');

const escapeHtml = (value) => String(value ?? '').replace(/[&<>'"]/g, (char) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;',
})[char]);

function score(axis) {
  return axis?.score == null ? 'N/A' : axis.score;
}

function render(entries) {
  if (!entries.length) {
    list.innerHTML = '<li class="leaderboard-empty">榜单还没有公开结果。诊断你的网站并选择公开，就能加入这里。</li>';
    return;
  }
  list.innerHTML = entries.map((entry) => {
    const axes = Object.fromEntries(entry.axes.map((axis) => [axis.id, axis]));
    return `<li class="leaderboard-row">
      <span class="leaderboard-rank">${escapeHtml(String(entry.rank).padStart(2, '0'))}</span>
      <div class="leaderboard-site"><strong><a href="/leaderboard/${encodeURIComponent(entry.host)}">${escapeHtml(entry.host)}</a></strong><small>${escapeHtml(new Date(entry.scanned_at).toLocaleString('zh-CN'))}</small></div>
      <dl class="leaderboard-axes">
        <div><dt>可发现</dt><dd>${escapeHtml(score(axes.discoverable))}</dd></div>
        <div><dt>可理解</dt><dd>${escapeHtml(score(axes.understandable))}</dd></div>
        <div><dt>可操作</dt><dd>${escapeHtml(score(axes.actionable))}</dd></div>
      </dl>
    </li>`;
  }).join('');
}

try {
  const response = await fetch('/api/v1/leaderboard', { headers: { Accept: 'application/json' } });
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail || '榜单读取失败');
  render(body.entries || []);
  note.textContent = body.storage === 'ready' ? '榜单只保存域名、三项得分、检查时间和结果指纹。' : '榜单暂未开放，本次诊断仍可正常使用。';
} catch (error) {
  list.innerHTML = '<li class="leaderboard-empty">榜单暂时不可用。</li>';
  note.textContent = error.message;
}
