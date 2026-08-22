import { RULESET_VERSION, scanSite } from './scanner.worker.mjs';
import { normalizeTarget } from './safety-worker.mjs';
import { SKILL_INDEX, SKILL_TEXT } from './skills.generated.mjs';
import { forwardHelloEmail } from './email-forwarder.mjs';
import { handleMcp } from './mcp-server.mjs';
import { publishToLeaderboard, readLeaderboard, readLeaderboardEntry } from './leaderboard.mjs';
import { leaderboardIndexPage, leaderboardSharePage, methodology, problemDetails, reportToMarkdown, wantsMarkdown } from './product-contract.mjs';

const json = (value, status = 200, headers = {}) => new Response(JSON.stringify(value), {
  status,
  headers: {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
    'x-content-type-options': 'nosniff',
    ...headers,
  },
});

const html = (title, body) => new Response(`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>${title}</title><body><main><a href="/">返回诊断</a><h1>${title}</h1>${body}</main></body></html>`, {
  headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'public, max-age=300' },
});

const problem = (value) => new Response(JSON.stringify(value), {
  status: value.status,
  headers: {
    'content-type': 'application/problem+json; charset=utf-8',
    'cache-control': 'no-store',
    'x-content-type-options': 'nosniff',
  },
});

const reportResponse = (request, report) => wantsMarkdown(request)
  ? new Response(reportToMarkdown(report), { headers: { 'content-type': 'text/markdown; charset=utf-8', 'cache-control': 'no-store', vary: 'Accept' } })
  : json(report, 200, { vary: 'Accept' });

const serverCard = () => ({
  $schema: 'https://static.modelcontextprotocol.io/schemas/v1/server-card.schema.json',
  name: 'io.bflabs.agent-readiness',
  title: 'BFLabs Agent Readiness',
  description: 'Scan public websites, read the opt-in leaderboard, and retrieve BFLabs Skills.',
  version: '1.0.0',
  websiteUrl: 'https://readiness.bflabs.cn/',
  remotes: [{ type: 'streamable-http', url: 'https://readiness.bflabs.cn/mcp', supportedProtocolVersions: ['2025-06-18'] }],
});

async function hashed(value) {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

async function enforceRateLimits(request, env, target) {
  const client = request.headers.get('cf-connecting-ip') || 'unknown';
  const [clientResult, targetResult] = await Promise.all([
    env.CLIENT_RATE_LIMITER.limit({ key: await hashed(client) }),
    env.TARGET_RATE_LIMITER.limit({ key: target.hostname.toLowerCase() }),
  ]);
  if (!clientResult.success || !targetResult.success) {
    throw Object.assign(new Error('请求过于频繁，请稍后再试'), { status: 429 });
  }
}

async function readRequestText(request) {
  const declared = Number(request.headers.get('content-length') || 0);
  if (declared > 8 * 1024) throw Object.assign(new Error('请求正文超过 8 KiB 上限'), { status: 413 });
  const text = await request.text();
  if (new TextEncoder().encode(text).byteLength > 8 * 1024) {
    throw Object.assign(new Error('请求正文超过 8 KiB 上限'), { status: 413 });
  }
  return text;
}

async function readRequestJson(request) {
  return JSON.parse(await readRequestText(request) || '{}');
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    try {
      if (request.method === 'POST' && ['/api/scans', '/api/v1/scans'].includes(url.pathname)) {
        const body = await readRequestJson(request);
        const target = normalizeTarget(body.url);
        await enforceRateLimits(request, env, target);
        const report = await scanSite(target.toString(), { delayMs: 100, fetchOptions: { timeoutMs: 8_000, maxBytes: 1024 * 1024 } });
        report.leaderboard_publication = body.publish_to_leaderboard === true
          ? await publishToLeaderboard(env.LEADERBOARD, report)
          : { status: 'not_requested' };
        return reportResponse(request, report);
      }
      if (request.method === 'GET' && ['/api/rulesets/current', '/api/v1/rulesets/current'].includes(url.pathname)) {
        return json({ version: RULESET_VERSION, axes: ['discoverable', 'understandable', 'actionable'], visibility: 'not_measured', business_outcome: 'not_measured' });
      }
      if (request.method === 'GET' && url.pathname === '/api/v1/leaderboard') return json(await readLeaderboard(env.LEADERBOARD));
      if (request.method === 'GET' && url.pathname === '/leaderboard') {
        return new Response(leaderboardIndexPage(await readLeaderboard(env.LEADERBOARD)), { headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'public, max-age=120' } });
      }
      if (request.method === 'GET' && url.pathname.startsWith('/leaderboard/')) {
        const entry = await readLeaderboardEntry(env.LEADERBOARD, decodeURIComponent(url.pathname.slice('/leaderboard/'.length)));
        if (!entry) return problem(problemDetails(Object.assign(new Error('榜单记录不存在'), { code: 'leaderboard_entry_not_found', status: 404 }), url.pathname));
        return new Response(leaderboardSharePage(entry), { headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'public, max-age=300' } });
      }
      if (request.method === 'GET' && url.pathname === '/.well-known/agent-skills/index.json') {
        return json(SKILL_INDEX, 200, { 'cache-control': 'public, max-age=300' });
      }
      if (request.method === 'GET' && ['/.well-known/mcp/server-card.json', '/mcp/server-card', '/server.json'].includes(url.pathname)) {
        return json(serverCard(), 200, { 'cache-control': 'public, max-age=300' });
      }
      if (request.method === 'GET' && url.pathname === '/methodology') return json(methodology(), 200, { 'cache-control': 'public, max-age=300' });
      if (url.pathname === '/mcp') {
        const body = request.method === 'POST' ? await readRequestText(request) : undefined;
        const boundedRequest = new Request(request.url, { method: request.method, headers: request.headers, ...(body !== undefined ? { body } : {}) });
        return handleMcp(boundedRequest, {
          scan: async (input) => {
            const target = normalizeTarget(input);
            await enforceRateLimits(request, env, target);
            return scanSite(target.toString(), { delayMs: 100, fetchOptions: { timeoutMs: 8_000, maxBytes: 1024 * 1024 } });
          },
          leaderboard: () => readLeaderboard(env.LEADERBOARD),
          skills: SKILL_TEXT,
        });
      }
      if (request.method === 'GET' && url.pathname.startsWith('/skills/')) {
        const skillId = decodeURIComponent(url.pathname.slice('/skills/'.length));
        const body = SKILL_TEXT[skillId];
        return body ? new Response(body, { headers: { 'content-type': 'text/plain; charset=utf-8', 'x-content-type-options': 'nosniff' } }) : json({ error: '未知子 Skill' }, 404);
      }
      if (request.method === 'GET' && url.pathname === '/privacy') {
        return html('隐私与扫描边界', '<p>本服务只读取你提交域名的公开页面，不登录、不绕过访问控制。完整报告、证据正文和 Agent 提示词不写入应用数据库。只有用户主动勾选公开榜单时，才保存域名、三轴结果、扫描时间和指纹摘要；不保存 IP。榜单记录最多保留 30 天，同一域名主动再次公开会刷新该记录。Cloudflare 仍会按其基础设施政策处理必要的安全与运行日志。</p><p>站点所有者可在 <code>/.well-known/bflabs-agent-readiness-opt-out</code> 返回 HTTP 200，并包含 <code>opt-out</code>、<code>deny</code> 或 <code>do-not-scan</code> 来拒绝诊断。榜单移除或滥用报告请发送至 <a href="mailto:hello@bflabs.cn">hello@bflabs.cn</a>。</p>');
      }
      if (request.method === 'GET' && url.pathname === '/terms') {
        return html('公开 Beta 使用边界', '<p>仅可诊断你有权测试的公开网站。公开榜单默认关闭。Readiness 三轴与 Agent Journey 不等于 AI 平台可见度，也不构成流量、转化或收入承诺。服务设置客户端与目标域名限流，可能拒绝高频、异常或已 opt-out 的目标。</p>');
      }
      if (url.pathname.startsWith('/api/')) return problem(problemDetails(Object.assign(new Error('API 路径不存在'), { status: 404 }), url.pathname));
      if (request.method === 'GET' || request.method === 'HEAD') return env.ASSETS.fetch(request);
      return problem(problemDetails(Object.assign(new Error('方法不允许'), { status: 405 }), url.pathname));
    } catch (error) {
      console.error('readiness_request_failed', { path: url.pathname, name: error.name, message: error.message });
      return problem(problemDetails(error, url.pathname));
    }
  },
  async email(message, env) {
    await forwardHelloEmail(message, env);
  },
};
