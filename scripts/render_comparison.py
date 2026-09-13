#!/usr/bin/env python3
"""Render a portable, read-only evidence view. No metrics or verdicts are inferred."""
import argparse
import html
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlsplit


def esc(value):
    return html.escape(str(value or ''), quote=True)


def time_text(value):
    if not value:
        return ''
    try:
        d = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        zone = d.strftime('%z')
        return d.strftime('%Y-%m-%d %H:%M') + (' UTC' if zone == '+0000' else (' ' + zone if zone else ''))
    except ValueError:
        return str(value)


def local_ref(root, value):
    if not isinstance(value, str) or not value or urlsplit(value).scheme:
        return None
    path = (root / value).resolve()
    try:
        relative = path.relative_to(root.resolve())
    except ValueError:
        return None
    return quote(relative.as_posix()) if path.is_file() else None


def link(root, value, title=None):
    href = local_ref(root, value)
    if href:
        return f'<a href="{href}" target="_blank" rel="noopener">{esc(title or value)}</a>'
    return f'<span class="muted">{esc(title or value)}（文件未找到）</span>'


def shot(root, ref):
    href = local_ref(root, ref)
    if href and Path(ref).suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp'):
        return f'<a href="{href}" target="_blank" rel="noopener"><img loading="lazy" src="{href}" alt="原始截图，点击查看完整图片"></a>'
    return '<p class="empty">未留存可读取的截图</p>'


def capture(root, item, label):
    if not item:
        return f'<div class="pane"><h4>{label}</h4><p class="empty">尚未采集</p></div>'
    viewport = item.get('viewport', '')
    return (f'<div class="pane"><h4>{label}</h4><p class="meta">{esc(time_text(item.get("captured_at")))} · '
            f'{esc(viewport)} · {esc({"local":"本地预览","public":"线上页面"}.get(item.get("environment"),"环境未知"))}</p>{shot(root, item.get("image"))}'
            f'<p>{esc(item.get("note"))}</p></div>')


def observation(root, row):
    refs = row.get('evidence_refs', [])
    images = [r for r in refs if isinstance(r, str) and Path(r).suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp')]
    picture = ''.join(shot(root, r) for r in images) if images else '<p class="empty">本样本缺少截图，原文保留</p>'
    cites = ''.join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(u)}</a></li>' for u in row.get('cited_urls', []) if urlsplit(u).scheme in ('http', 'https'))
    condition = ' · '.join([
        time_text(row.get('captured_at')), '模型 ' + str(row.get('visible_model') or '未知'),
        {'en':'英文','zh':'中文'}.get(row.get('language'), str(row.get('language') or '语言未知')),
        '地区 ' + ('未知' if row.get('region') in (None, 'unknown') else str(row.get('region'))),
        '个性化 ' + {'off':'关闭','on':'开启'}.get(row.get('personalization_status'),'未知'),
    ])
    note = row.get('exclusion_reason') or ''
    return (f'<div class="sample" data-round="{esc(row.get("round_id"))}"><p class="meta">轮次 {esc(row.get("round_id"))} · '
            f'尝试 {esc(row.get("attempt_index", 1))}<br>{esc(condition)}</p>{picture}'
            f'<p class="note">{esc(note)}</p><details><summary>回答全文与引用</summary><pre>{esc(row.get("answer_text"))}</pre>'
            f'<ul>{cites}</ul><p>{" · ".join(link(root,r) for r in refs)}</p></details></div>')


def read_json(path, fallback):
    return json.loads(path.read_text('utf-8')) if path.exists() else fallback


PURPOSE = {
    'A': '品牌身份：能否认对，避免同名混淆',
    'B': '页面理解：能否说清用途与受众',
    'C': '主动发现：找到正确官网与接入说明',
    'D': '自然候选：是否被提及或推荐',
}


DISPOSITION = {
    'keep_existing': '沿用现有页',
    'update_existing': '改现有页',
    'new_page': '需要新页',
    'deferred': '本轮不做',
    'not_applicable': '不适用',
}
COVERAGE_STATUS = {
    'unmapped': '还没有对应页面',
    'planned': '已规划',
    'blueprint_ready': '蓝图已有，公开页还没有',
    'changed_local': '本地已改',
    'released': '已发布',
    'verified_public': '公开页已核对',
    'deferred': '本轮不做',
}


def coverage_section(coverage, questions):
    question_text = {item.get('question_id'): item.get('text') for item in questions.get('questions', [])}
    cards = []
    for row in coverage.get('rows', []):
        urls = row.get('url')
        page = urls if urls else '还没有公开页'
        topics = [question_text.get(qid) or qid for qid in row.get('question_ids', [])]
        evidence = row.get('evidence_ref')
        visual = ''
        if row.get('disposition') == 'keep_existing':
            visual = '<p class="note">这一页按原样保留，没有视觉改动。</p>'
        elif row.get('status') == 'blueprint_ready' and not urls:
            visual = '<p class="note">内容蓝图已有，公开页还没有。不算已经建完。</p>'
        cards.append(
            f'<article><p class="eyebrow">{esc(page)}</p><h3>{esc(row.get("question_cluster"))}</h3>'
            f'<p>{esc(DISPOSITION.get(row.get("disposition"), row.get("disposition")))} · '
            f'{esc(COVERAGE_STATUS.get(row.get("status"), row.get("status")))}</p>'
            f'<p>{"；".join(esc(item) for item in topics) or "尚未绑定冻结问题"}</p>'
            + (f'<p class="meta">证据 {esc(evidence)}</p>' if evidence else '<p class="empty">尚未留下页面或回答证据</p>')
            + visual + f'<p>{esc(row.get("note"))}</p></article>'
        )
    if not cards:
        return '<p class="empty">还没有记下哪些问题对应哪一页。某一页已发布，不等于整站已经建完。</p>'
    return '<p class="intro">优先问题是否都有对应页面。多题可以共用同一页。</p>' + ''.join(cards)


def question_section(questions, backlog):
    cards = []
    for q in questions.get('questions', []):
        purpose = q.get('purpose') or PURPOSE.get(q.get('observation_line'), '按本题判读标准核对')
        cards.append(f'<article><h3>{esc(q.get("text"))}</h3><p>{esc(purpose)}</p>'
                     f'<details><summary>本题如何判断</summary><p>{esc(q.get("partial_credit_rule"))}</p></details></article>')
    candidates = []
    for q in backlog.get('next_round_pool', []):
        source = {'agent_hypothesis':'生成候选，未证明真实需求','support':'客服原话','onsite_search':'站内搜索记录','user_reported':'用户提供','platform_export':'平台导出'}.get(q.get('source_kind'),'来源待核对')
        candidates.append(f'<li><b>{esc(q.get("text"))}</b><p class="meta">{esc(source)} · {esc(q.get("market"))}</p><p>{esc(q.get("selection_reason"))}</p></li>')
    return ('<p class="intro">固定题用于本轮前后比较。新题留在下一轮候选，不改变已采样的题目。</p>'
            + (''.join(cards) or '<p class="empty">尚未冻结题库</p>')
            + '<details><summary>下一轮候选问题（' + str(len(candidates)) + '）</summary><ul>'
            + ''.join(candidates) + '</ul></details>')


def render(project, template):
    root = Path(project).resolve()
    exp = read_json(root / 'experiment.json', {})
    actions = read_json(root / 'actions.json', {}).get('actions', [])
    questions = read_json(root / 'questions.json', {})
    backlog = read_json(root / 'question-backlog.json', {})
    coverage = read_json(root / 'coverage.json', {})
    obs_path = root / 'observations.jsonl'
    rows = [json.loads(line) for line in obs_path.read_text('utf-8').splitlines() if line.strip()] if obs_path.exists() else []
    # Refuse silently mixed projects; this is a view of one experiment, not an importer.
    for row in rows:
        if row.get('experiment_id') and row['experiment_id'] != exp.get('experiment_id'):
            raise ValueError('Observation belongs to another experiment')
    before_id = (exp.get('baseline') or {}).get('round_id')
    groups = defaultdict(list)
    for row in rows:
        # Include question version and line: never visually pair a changed prompt as the same question.
        key = tuple(row.get(k) or '' for k in ['platform', 'terminal', 'prompt_id', 'prompt_text', 'question_version', 'observation_line', 'sample_slot_id'])
        groups[key].append(row)
    page_blocks = []
    for action in sorted(actions, key=lambda a: not bool(a.get('visual_evidence'))):
        pairs = action.get('visual_evidence', [])
        pairs_html = ''
        for pair in pairs:
            b, a = pair.get('before'), pair.get('after')
            mismatch = bool(b and a and b.get('viewport') != a.get('viewport'))
            pairs_html += f'<h3>{esc(pair.get("label"))}</h3><div class="pair">{capture(root,b,"改前")}{capture(root,a,"改后")}</div>'
            if mismatch:
                pairs_html += '<p class="note">两张图视口不同，不能作为同条件视觉对照。</p>'
            if a and (a.get('environment') == 'local' or (b and b.get('environment') != a.get('environment'))):
                pairs_html += '<p class="note">包含本地预览或环境不同，不能当作线上发布前后验证。</p>'
            pairs_html += f'<p class="explain">{esc(pair.get("change_note"))}</p>'
            pairs_html += '<p>' + ' · '.join(link(root,r) for r in pair.get('evidence_refs', [])) + '</p>'
        if not pairs:
            pairs_html = '<p class="empty">暂无成对截图。查看修改记录与原始证据，不补造改前画面。</p>'
        page_blocks.append(f'<article><p class="eyebrow">{esc(action.get("page_url"))}</p><h2>{esc(action.get("summary"))}</h2>'
                           f'<p class="meta">发布时间 {esc(time_text(action.get("released_at")) or "尚未发布")}</p>{pairs_html}</article>')
    ai_blocks = []
    for key, group in groups.items():
        before = [r for r in group if not before_id or r.get('round_id') == before_id]
        after = [r for r in group if before_id and r.get('round_id') != before_id]
        pane = lambda rs: ''.join(observation(root,r) for r in sorted(rs,key=lambda r:(r.get('captured_at',''),r.get('attempt_index',0))))
        ai_blocks.append(f'<article class="ai-item" data-platform="{esc(key[0])}" data-search="{esc(key[3].lower())}">'
                         f'<p class="eyebrow">{esc(key[0])} · {esc(key[1])} · {esc(key[6])} · 题目版本 {esc(key[4])}</p>'
                         f'<h2>{esc(key[3])}</h2><div class="pair"><div class="pane"><h4>{"改前" if before_id else "已有记录 · 尚未绑定基线"}</h4>{pane(before) or "<p class=empty>无绑定基线记录</p>"}</div>'
                         f'<div class="pane"><h4>复测</h4>{pane(after)}<p class="empty round-empty"{" hidden" if after else ""}>待复测 · 尚无改后回答</p></div></div></article>')
    platforms = sorted({str(r.get('platform','')) for r in rows})
    rounds = sorted({str(r.get('round_id','')) for r in rows if before_id and r.get('round_id') != before_id})
    window = exp.get('business_window') or {}
    windows = ''.join(f'<div class="pane"><h4>{label}</h4><p>{esc((window.get(k) or {}).get("start") or "未设置")}<br>至<br>{esc((window.get(k) or {}).get("end") or "未设置")}</p></div>' for k,label in [('before','改前窗口'),('after','改后窗口')])
    business = f'<div class="pair">{windows}</div><p>注册、成功调用和付款分开看。金额和来源以业务报告为准；本页不从截图推算收入。</p><p>{link(root,"report.md","查看整轮业务与测量报告")}</p>'
    data = {
        'TITLE': esc((exp.get('brand') or {}).get('canonical_name') or exp.get('site_domain') or '网站'),
        'SITE': esc(exp.get('site_url') or exp.get('site_domain')),
        'NEXT': esc(exp.get('next_step') or '补充本轮下一步'),
        'COUNTS': f'{len(actions)} 项网站改动 · {len(rows)} 条回答记录 · {len(rounds)} 个复测轮次',
        'QUESTIONS': question_section(questions, backlog),
        'COVERAGE': coverage_section(coverage, questions),
        'PAGES': ''.join(page_blocks) or '<p class="empty">尚无网站修改记录</p>',
        'AI': ''.join(ai_blocks) or '<p class="empty">尚无回答样本</p>',
        'BUSINESS': business,
        'PLATFORMS': ''.join(f'<option>{esc(x)}</option>' for x in platforms),
        'ROUNDS': ''.join(f'<option>{esc(x)}</option>' for x in rounds),
        'SOURCES': ' · '.join(link(root,f) for f in ['experiment.json','actions.json','questions.json','question-backlog.json','coverage.json','observations.jsonl']),
    }
    result = Path(template).read_text('utf-8')
    return re.sub(r'\{\{([A-Z]+)\}\}', lambda match: data[match[1]], result)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', required=True, type=Path)
    args = p.parse_args()
    template = Path(__file__).resolve().parent.parent / 'templates' / 'comparison.html'
    output = args.project / 'comparison.html'
    output.write_text(render(args.project, template), 'utf-8')
    print(output)


if __name__ == '__main__':
    main()
