import fs from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { RULESET_VERSION, scanSite } from './scanner.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PUBLIC = path.join(ROOT, 'public');
const PORT = Number(process.env.PORT || 4177);
const reports = new Map();

const types = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
};

function sendJson(response, status, value) {
  response.writeHead(status, { 'Content-Type': types['.json'], 'Cache-Control': 'no-store' });
  response.end(JSON.stringify(value));
}

async function readJson(request) {
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > 32 * 1024) throw new Error('请求正文超过限制');
    chunks.push(chunk);
  }
  return JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}');
}

function startScan(url) {
  const id = `rpt_${crypto.randomUUID()}`;
  reports.set(id, { report_id: id, status: 'scanning', stage: '验证公开目标' });
  scanSite(url)
    .then((report) => reports.set(id, { ...report, report_id: id, status: report.scan.status }))
    .catch((error) => reports.set(id, { report_id: id, status: 'failed', error: error.message }));
  return id;
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
    if (request.method === 'POST' && url.pathname === '/api/scans') {
      const body = await readJson(request);
      const reportId = startScan(body.url);
      return sendJson(response, 202, { report_id: reportId, status_url: `/api/scans/${reportId}` });
    }
    if (request.method === 'GET' && url.pathname.startsWith('/api/scans/')) {
      const report = reports.get(url.pathname.split('/').pop());
      return sendJson(response, report ? 200 : 404, report || { error: '报告不存在或已过期' });
    }
    if (request.method === 'GET' && url.pathname === '/api/rulesets/current') {
      return sendJson(response, 200, {
        version: RULESET_VERSION,
        axes: ['discoverable', 'understandable', 'actionable'],
        visibility: 'not_measured',
        business_outcome: 'not_measured',
      });
    }
    if (request.method === 'GET' && url.pathname === '/skills/geo-optimize') {
      response.writeHead(302, { Location: 'https://github.com/Sunnyender-org/bflabs-agent-readiness/tree/main/skills/geo-optimize' });
      return response.end();
    }
    if (request.method === 'GET' && ['/privacy', '/terms'].includes(url.pathname)) {
      response.writeHead(200, { 'Content-Type': types['.html'] });
      return response.end(`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>BFLabs GEO Readiness</title><body><main><a href="/">返回诊断</a><h1>${url.pathname === '/privacy' ? '隐私边界' : '使用边界'}</h1><p>本地原型只扫描公开页面，不绕过登录。公开部署、数据保留和正式条款尚未批准。</p></main></body></html>`);
    }
    if (request.method === 'GET' && await serveStatic(request, response, url.pathname)) return;
    response.writeHead(404, { 'Content-Type': types['.html'] });
    response.end('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>页面不存在</title><body><main><h1>这条证据路径不存在</h1><p><a href="/">返回诊断入口</a></p></main></body></html>');
  } catch (error) {
    sendJson(response, 400, { error: error.message });
  }
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`BFLabs GEO Readiness listening on http://127.0.0.1:${PORT}`);
});
