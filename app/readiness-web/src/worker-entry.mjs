import { RULESET_VERSION, scanSite } from './scanner.worker.mjs';
import { normalizeTarget } from './safety-worker.mjs';
import { SKILL_TEXT } from './skills.generated.mjs';
import { forwardHelloEmail } from './email-forwarder.mjs';

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

async function readRequestJson(request) {
  const declared = Number(request.headers.get('content-length') || 0);
  if (declared > 8 * 1024) throw Object.assign(new Error('请求正文超过 8 KiB 上限'), { status: 413 });
  const text = await request.text();
  if (new TextEncoder().encode(text).byteLength > 8 * 1024) {
    throw Object.assign(new Error('请求正文超过 8 KiB 上限'), { status: 413 });
  }
  return JSON.parse(text || '{}');
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    try {
      if (request.method === 'POST' && url.pathname === '/api/scans') {
        const body = await readRequestJson(request);
        const target = normalizeTarget(body.url);
        await enforceRateLimits(request, env, target);
        const report = await scanSite(target.toString(), { delayMs: 100, fetchOptions: { timeoutMs: 8_000, maxBytes: 1024 * 1024 } });
        return json(report, 200);
      }
      if (request.method === 'GET' && url.pathname === '/api/rulesets/current') {
        return json({ version: RULESET_VERSION, axes: ['discoverable', 'understandable', 'actionable'], visibility: 'not_measured', business_outcome: 'not_measured' });
      }
      if (request.method === 'GET' && url.pathname.startsWith('/skills/')) {
        const skillId = decodeURIComponent(url.pathname.slice('/skills/'.length));
        const body = SKILL_TEXT[skillId];
        return body ? new Response(body, { headers: { 'content-type': 'text/plain; charset=utf-8', 'x-content-type-options': 'nosniff' } }) : json({ error: '未知子 Skill' }, 404);
      }
      if (request.method === 'GET' && url.pathname === '/privacy') {
        return html('隐私与扫描边界', '<p>本服务只读取你提交域名的公开页面，不登录、不绕过访问控制，不保存报告或扫描输入到应用数据库。Cloudflare 仍会按其基础设施政策处理必要的安全与运行日志。</p><p>站点所有者可在 <code>/.well-known/bflabs-agent-readiness-opt-out</code> 返回 HTTP 200，并包含 <code>opt-out</code>、<code>deny</code> 或 <code>do-not-scan</code> 来拒绝诊断。滥用报告请发送至 <a href="mailto:hello@bflabs.cn">hello@bflabs.cn</a>。</p>');
      }
      if (request.method === 'GET' && url.pathname === '/terms') {
        return html('公开 Beta 使用边界', '<p>仅可诊断你有权测试的公开网站。Readiness 评分不等于 AI 平台可见度，也不构成流量、转化或收入承诺。服务设置客户端与目标域名限流，可能拒绝高频、异常或已 opt-out 的目标。</p>');
      }
      if (request.method === 'GET' || request.method === 'HEAD') return env.ASSETS.fetch(request);
      return json({ error: '方法不允许' }, 405, { allow: 'GET, HEAD, POST' });
    } catch (error) {
      console.error('readiness_request_failed', { path: url.pathname, name: error.name, message: error.message });
      return json({ error: error.name === 'AbortError' ? '目标响应超时' : error.message }, error.status || 400);
    }
  },
  async email(message, env) {
    await forwardHelloEmail(message, env);
  },
};
