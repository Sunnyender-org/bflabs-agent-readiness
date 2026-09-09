import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const html = fs.readFileSync(path.join(root, 'public/index.html'), 'utf8');
const css = fs.readFileSync(path.join(root, 'public/styles.css'), 'utf8');
const app = fs.readFileSync(path.join(root, 'public/app.js'), 'utf8');
const server = fs.readFileSync(path.join(root, 'src/server.mjs'), 'utf8');
const skillResources = fs.readFileSync(path.join(root, 'src/skill-resources.mjs'), 'utf8');

test('uses the committed BFLabs Grok prototype as the formal web shell', () => {
  assert.match(html, /BF LABS/);
  assert.match(html, /你的网站，AI 读得懂吗？/);
  assert.match(html, /GEO（生成式引擎优化）与 Agent 准备度/);
  assert.match(html, /不了解 GEO？先从 GEO 学院开始/);
  assert.match(html, /诊断报告/);
  assert.match(html, /BFLabs 如何交付/);
  assert.match(html, /精选评分/);
  assert.match(html, /最新评分/);
  assert.doesNotMatch(html, /Featured scores|Recent scores/);
  assert.doesNotMatch(html, /别先问 AI 会不会推荐你/);
  assert.doesNotMatch(css, /Iowan Old Style|folio/);
});

test('keeps the real scanner and protocol actions wired into the visual shell', () => {
  for (const id of [
    'scan-form',
    'axis-rail',
    'findings',
    'evidence-body',
    'download-report',
    'copy-agent-prompt',
    'continue-workbuddy',
    'handoff-status',
    'publish-to-leaderboard',
    'journey-steps',
    'journey-status',
    'skill-routes',
    'save-baseline',
    'contact-bflabs',
    'delivery-context',
    'featured-scores-list',
    'recent-scores-list',
  ]) {
    assert.match(html, new RegExp(`id="${id}"`));
    assert.match(app, new RegExp(`#${id}`));
  }
});

test('exposes a real BFLabs inquiry route and an in-session retest contract', () => {
  assert.match(html, /mailto:hello@bflabs\.cn/);
  assert.match(html, /同一浏览会话内保存首次结果并复测/);
  assert.match(html, /多平台重复抽样、持续监测与趋势报告/);
  assert.match(app, /let baselineReport = null/);
  assert.match(app, /复测并对比/);
  assert.match(app, /外部 AI 平台可见度与业务结果仍需单独测量/);
  assert.match(app, /downloadArtifactPack/);
  assert.match(app, /复制给 Agent，开始修复/);
  assert.match(app, /prepare_workbuddy_handoff: true/);
  assert.match(app, /currentReport\.geo_handoff/);
  assert.match(app, /window\.location\.assign\(handoff\.continue_url\)/);
  assert.doesNotMatch(app, /fetch\('\/api\/v1\/geo-handoffs'/);
  assert.match(app, /继续链接暂时不可用，请复制给 Agent/);
  assert.match(app, /publish_to_leaderboard: publishCheckbox\.checked/);
  assert.doesNotMatch(app, /await downloadArtifactPack\(\);\s*await navigator\.clipboard\.writeText/);
  assert.match(html, /href="\/leaderboard"/);
  assert.match(html, /skills\.bflabs\.cn\/catalog\.html#geo/);
  assert.match(html, /我确认有权公开，将本次诊断结果加入榜单/);
  assert.match(html, /每一步都有可核对的检查结果/);
  assert.doesNotMatch(html, /这里说明交付步骤/);
  assert.doesNotMatch(html, /33<i>→<\/i>78/);
  assert.doesNotMatch(html, />验收中</);
  assert.doesNotMatch(app, /#delivery-origin'\)\.textContent = host/);
  assert.match(app, /#delivery-origin'\)\.textContent = '专业交付'/);
  assert.doesNotMatch(html, /唯一对应 Skill|读取根 Skill|Agent Journey|SkillHub/);
  assert.match(app, /finding\.rule_id/);
  assert.doesNotMatch(app, /finding\.owner_route|item\.route|report\.skill_routes\[0\]\.id/);
  assert.match(server, /from '\.\/skill-resources\.mjs'/);
  assert.match(server, /handleSkillRoute/);
  assert.match(skillResources, /export const SKILL_IDS/);
  assert.match(skillResources, /text\/plain; charset=utf-8/);
  assert.match(server, /await completeScan/);
  assert.doesNotMatch(server, /sendJson\(response, 202/);
});
