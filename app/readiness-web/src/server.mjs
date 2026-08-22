import fs from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { RULESET_VERSION, scanSite } from './scanner.mjs';
import { normalizeTarget } from './safety.mjs';
import { handleMcp } from './mcp-server.mjs';
import { memoryLeaderboardStore, publishToLeaderboard, readLeaderboard, readLeaderboardEntry } from './leaderboard.mjs';
import { leaderboardIndexPage, leaderboardSharePage, methodology, problemDetails, reportToMarkdown, wantsMarkdown } from './product-contract.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PUBLIC = path.join(ROOT, 'public');
const REPOSITORY_ROOT = path.resolve(ROOT, '..', '..');
const PORT = Number(process.env.PORT || 4177);
const reports = new Map();
const leaderboard = memoryLeaderboardStore(new Map());
const SKILL_IDS = new Set(['bflabs-agent-readiness', 'geo-content', 'geo-discover', 'geo-measure', 'geo-optimize', 'seo-plan', 'webmcp-enable']);

const types = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
};

function sendJson(response, status, value, headers = {}) {
  response.writeHead(status, { 'Content-Type': types['.json'], 'Cache-Control': 'no-store', ...headers });
  response.end(JSON.stringify(value));
}

function sendProblem(response, value) {
  response.writeHead(value.status, {
    'Content-Type': 'application/problem+json; charset=utf-8',
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
  });
  response.end(JSON.stringify(value));
}

function sendReport(request, response, status, report) {
  if (wantsMarkdown({ headers: { get: (name) => request.headers[name.toLowerCase()] || '' } })) {
    response.writeHead(status, { 'Content-Type': 'text/markdown; charset=utf-8', 'Cache-Control': 'no-store', Vary: 'Accept' });
    response.end(reportToMarkdown(report));
    return;
  }
  sendJson(response, status, report, { Vary: 'Accept' });
}

async function readBody(request) {
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > 32 * 1024) throw new Error('请求正文超过限制');
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString('utf8');
}

async function readJson(request) {
  return JSON.parse(await readBody(request) || '{}');
}

function skillPath(skillId) {
  return skillId === 'bflabs-agent-readiness'
    ? path.join(REPOSITORY_ROOT, 'SKILL.md')
    : path.join(REPOSITORY_ROOT, 'skills', skillId, 'SKILL.md');
}

async function readSkillTexts() {
  return Object.fromEntries(await Promise.all([...SKILL_IDS].map(async (id) => [id, await fs.readFile(skillPath(id), 'utf8')])));
}

async function buildAgentSkillIndex() {
  const skills = await readSkillTexts();
  return {
    $schema: 'https://schemas.agentskills.io/discovery/0.2.0/schema.json',
    skills: Object.entries(skills).map(([name, body]) => ({
      name,
      type: 'skill-md',
      description: name === 'bflabs-agent-readiness'
        ? 'Diagnose a public website and route one evidence-backed next action to the smallest BFLabs child Skill.'
        : `Run the BFLabs ${name} child Skill for its registered evidence-backed intent.`,
      url: `http://127.0.0.1:${PORT}/skills/${name}`,
      digest: `sha256:${crypto.createHash('sha256').update(body).digest('hex')}`,
    })),
  };
}

function startScan(url, options = {}) {
  const id = `rpt_${crypto.randomUUID()}`;
  reports.set(id, { report_id: id, status: 'scanning', stage: '验证公开目标' });
  scanSite(url)
    .then(async (report) => {
      const publication = options.publishToLeaderboard
        ? await publishToLeaderboard(leaderboard, report)
        : { status: 'not_requested' };
      reports.set(id, { ...report, leaderboard_publication: publication, report_id: id, status: report.scan.status });
    })
    .catch((error) => reports.set(id, { report_id: id, status: 'failed', error: error.message }));
  return id;
}

async function sendFetchResponse(response, fetchResponse) {
  const headers = Object.fromEntries(fetchResponse.headers.entries());
  response.writeHead(fetchResponse.status, headers);
  response.end(Buffer.from(await fetchResponse.arrayBuffer()));
}

async function serveStatic(request, response, pathname) {
  const candidate = pathname === '/' ? 'index.html' : pathname.slice(1);
  const resolved = path.resolve(PUBLIC, candidate);
  if (!resolved.startsWith(PUBLIC)) return false;
  try {
    const body = await fs.readFile(resolved);
    response.writeHead(200, {
      'Content-Type': types[path.extname(resolved)] || 'application/octet-stream',
      'Cache-Control': 'no-cache',
      'X-Content-Type-Options': 'nosniff',
    });
    response.end(body);
    return true;
  } catch {
    return false;
  }
}

const server = http.createServer(async (request, response) => {
  const url = new URL(request.url, `http://${request.headers.host || `127.0.0.1:${PORT}`}`);
  try {
    if (request.method === 'POST' && ['/api/scans', '/api/v1/scans'].includes(url.pathname)) {
      const body = await readJson(request);
      const target = normalizeTarget(body.url);
      const reportId = startScan(target.toString(), { publishToLeaderboard: body.publish_to_leaderboard === true });
      return sendJson(response, 202, { report_id: reportId, status_url: `/api/v1/scans/${reportId}` });
    }
    if (request.method === 'GET' && /^\/api\/(?:v1\/)?scans\//.test(url.pathname)) {
      const artifactMatch = url.pathname.match(/^\/api\/(?:v1\/)?scans\/([^/]+)\/artifact-pack$/);
      if (artifactMatch) {
        const report = reports.get(artifactMatch[1]);
        if (!report?.artifact_pack) return sendJson(response, 404, { error: 'Artifact Pack 不存在或尚未完成' });
        return sendJson(response, 200, report.artifact_pack, {
          'Content-Disposition': `attachment; filename="${artifactMatch[1]}-artifact-pack.json"`,
        });
      }
      const report = reports.get(url.pathname.split('/').pop());
      if (!report) return sendProblem(response, problemDetails(Object.assign(new Error('报告不存在或已过期'), { code: 'report_not_found', status: 404 }), url.pathname));
      if (report.status === 'failed') return sendProblem(response, problemDetails(new Error(report.error), url.pathname));
      return ['complete', 'partial', 'blocked'].includes(report.status)
        ? sendReport(request, response, 200, report)
        : sendJson(response, 200, report);
    }
    if (request.method === 'GET' && ['/api/rulesets/current', '/api/v1/rulesets/current'].includes(url.pathname)) {
      return sendJson(response, 200, {
        version: RULESET_VERSION,
        axes: ['discoverable', 'understandable', 'actionable'],
        visibility: 'not_measured',
        business_outcome: 'not_measured',
      });
    }
    if (request.method === 'GET' && url.pathname === '/api/v1/leaderboard') {
      return sendJson(response, 200, await readLeaderboard(leaderboard));
    }
    if (request.method === 'GET' && url.pathname === '/leaderboard') {
      response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'public, max-age=120' });
      return response.end(leaderboardIndexPage(await readLeaderboard(leaderboard)));
    }
    if (request.method === 'GET' && url.pathname.startsWith('/leaderboard/')) {
      const entry = await readLeaderboardEntry(leaderboard, decodeURIComponent(url.pathname.slice('/leaderboard/'.length)));
      if (!entry) return sendProblem(response, problemDetails(Object.assign(new Error('榜单记录不存在'), { code: 'leaderboard_entry_not_found', status: 404 }), url.pathname));
      response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'public, max-age=300' });
      return response.end(leaderboardSharePage(entry));
    }
    if (request.method === 'GET' && url.pathname === '/.well-known/agent-skills/index.json') {
      return sendJson(response, 200, await buildAgentSkillIndex(), { 'Cache-Control': 'public, max-age=300' });
    }
    if (request.method === 'GET' && ['/.well-known/mcp/server-card.json', '/mcp/server-card', '/server.json'].includes(url.pathname)) {
      return sendJson(response, 200, {
        $schema: 'https://static.modelcontextprotocol.io/schemas/v1/server-card.schema.json',
        name: 'io.bflabs.agent-readiness',
        title: 'BFLabs Agent Readiness',
        description: 'Scan public websites, read the opt-in leaderboard, and retrieve BFLabs Skills.',
        version: '1.0.0',
        websiteUrl: `http://127.0.0.1:${PORT}/`,
        remotes: [{ type: 'streamable-http', url: `http://127.0.0.1:${PORT}/mcp`, supportedProtocolVersions: ['2025-06-18'] }],
      });
    }
    if (request.method === 'GET' && url.pathname === '/methodology') return sendJson(response, 200, methodology());
    if (url.pathname === '/mcp') {
      const body = request.method === 'POST' ? await readBody(request) : undefined;
      const webRequest = new Request(url, { method: request.method, headers: request.headers, ...(body !== undefined ? { body } : {}) });
      const skills = await readSkillTexts();
      const result = await handleMcp(webRequest, {
        scan: (target) => scanSite(target),
        leaderboard: () => readLeaderboard(leaderboard),
        skills,
      });
      return sendFetchResponse(response, result);
    }
    if (request.method === 'GET' && url.pathname.startsWith('/skills/')) {
      const skillId = decodeURIComponent(url.pathname.slice('/skills/'.length));
      if (!SKILL_IDS.has(skillId)) return sendJson(response, 404, { error: '未知子 Skill' });
      const body = await fs.readFile(skillPath(skillId), 'utf8');
      response.writeHead(200, {
        'Content-Type': 'text/plain; charset=utf-8',
        'Cache-Control': 'no-cache',
        'X-Content-Type-Options': 'nosniff',
      });
      return response.end(body);
    }
    if (request.method === 'GET' && ['/privacy', '/terms'].includes(url.pathname)) {
      response.writeHead(200, { 'Content-Type': types['.html'] });
      return response.end(`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>BFLabs Agent Readiness</title><body><main><a href="/">返回诊断</a><h1>${url.pathname === '/privacy' ? '隐私边界' : '使用边界'}</h1><p>${url.pathname === '/privacy'
        ? '只读取你提交域名的公开页面，不登录、不绕过访问控制。完整报告、证据正文和 Agent 提示词不写入应用数据库。只有你主动勾选公开榜单时，才保存域名、三轴结果、扫描时间和指纹摘要；不保存 IP。'
        : '仅可诊断你有权测试的公开网站。公开榜单默认关闭。Readiness、Agent Journey、AI visibility 与 Business outcome 彼此独立，不构成流量、转化或收入承诺。'}</p></main></body></html>`);
    }
    if (url.pathname.startsWith('/api/')) {
      return sendProblem(response, problemDetails(Object.assign(new Error('API 路径不存在'), { status: 404 }), url.pathname));
    }
    if (request.method === 'GET' && await serveStatic(request, response, url.pathname)) return;
    response.writeHead(404, { 'Content-Type': types['.html'] });
    response.end('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>页面不存在</title><body><main><h1>这条证据路径不存在</h1><p><a href="/">返回诊断入口</a></p></main></body></html>');
  } catch (error) {
    sendProblem(response, problemDetails(error, url.pathname));
  }
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`BFLabs Agent Readiness listening on http://127.0.0.1:${PORT}`);
});
