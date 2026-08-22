import dns from 'node:dns/promises';
import net from 'node:net';

const BLOCKED_HOST_SUFFIXES = ['.local', '.internal', '.localhost', '.home.arpa'];

export function normalizeTarget(input) {
  const value = String(input || '').trim();
  if (!value) throw new Error('请输入公开域名或 HTTPS URL');
  const withScheme = /^[a-z][a-z0-9+.-]*:/i.test(value) ? value : `https://${value}`;
  const url = new URL(withScheme);
  if (!['http:', 'https:'].includes(url.protocol)) throw new Error('只支持 HTTP 和 HTTPS');
  if (url.username || url.password) throw new Error('URL 不能包含账号或凭据');
  if (url.port && !['80', '443'].includes(url.port)) throw new Error('只允许 80 和 443 端口');
  const literalHostname = url.hostname.replace(/^\[|\]$/g, '');
  if (net.isIP(literalHostname)) throw new Error('不接受 IP 地址，请使用公开域名');
  const hostname = literalHostname.toLowerCase();
  if (hostname === 'localhost' || BLOCKED_HOST_SUFFIXES.some((suffix) => hostname.endsWith(suffix))) {
    throw new Error('目标不是公开互联网域名');
  }
  url.username = '';
  url.password = '';
  url.hash = '';
  url.pathname = '/';
  url.search = '';
  return url;
}

export function isUnsafeAddress(address) {
  const normalized = String(address).toLowerCase().split('%')[0];
  const version = net.isIP(normalized);
  if (version === 4) {
    const parts = normalized.split('.').map(Number);
    const [a, b, c] = parts;
    return (
      a === 0 ||
      a === 10 ||
      a === 127 ||
      (a === 100 && b >= 64 && b <= 127) ||
      (a === 169 && b === 254) ||
      (a === 172 && b >= 16 && b <= 31) ||
      (a === 192 && b === 0 && c === 0) ||
      (a === 192 && b === 0 && c === 2) ||
      (a === 192 && b === 168) ||
      (a === 198 && (b === 18 || b === 19)) ||
      (a === 198 && b === 51 && c === 100) ||
      (a === 203 && b === 0 && c === 113) ||
      a >= 224
    );
  }
  if (version === 6) {
    if (normalized === '::' || normalized === '::1') return true;
    if (normalized.startsWith('fc') || normalized.startsWith('fd')) return true;
    if (/^fe[89ab]/.test(normalized)) return true;
    if (normalized.startsWith('2001:db8:')) return true;
    if (normalized.startsWith('::ffff:')) {
      const mapped = normalized.slice('::ffff:'.length);
      return net.isIP(mapped) === 4 ? isUnsafeAddress(mapped) : true;
    }
    return false;
  }
  return true;
}

export async function assertPublicHostname(hostname, lookup = dns.lookup) {
  const records = await lookup(hostname, { all: true, verbatim: true });
  if (!records.length) throw new Error('域名没有可用的公开地址');
  const unsafe = records.find((record) => isUnsafeAddress(record.address));
  if (unsafe) throw new Error(`域名解析到了不安全地址类型 IPv${unsafe.family}`);
  return records;
}

export async function safeFetchText(input, options = {}) {
  const maxRedirects = options.maxRedirects ?? 3;
  const maxBytes = options.maxBytes ?? 2 * 1024 * 1024;
  const timeoutMs = options.timeoutMs ?? 10_000;
  let current = new URL(input);
  const redirects = [];

  for (let redirectCount = 0; redirectCount <= maxRedirects; redirectCount += 1) {
    if (!['http:', 'https:'].includes(current.protocol)) throw new Error('重定向到了不支持的协议');
    if (current.username || current.password) throw new Error('重定向 URL 包含凭据');
    if (current.port && !['80', '443'].includes(current.port)) throw new Error('重定向到了不允许的端口');
    if (net.isIP(current.hostname)) throw new Error('重定向到了 IP 地址');
    await assertPublicHostname(current.hostname, options.lookup || dns.lookup);

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    let response;
    try {
      const headers = {
        Accept: options.accept || 'text/html, application/json, text/plain, application/xml;q=0.9',
        'User-Agent': 'BFLabs-Agent-Readiness/1.0; +https://readiness.bflabs.cn/privacy',
      };
      if (options.contentType) headers['Content-Type'] = options.contentType;
      response = await (options.fetchImpl || fetch)(current, {
        method: options.method || 'GET',
        body: options.body,
        headers,
        redirect: 'manual',
        credentials: 'omit',
        referrerPolicy: 'no-referrer',
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timer);
    }

    if ([301, 302, 303, 307, 308].includes(response.status)) {
      const location = response.headers.get('location');
      if (!location) throw new Error('重定向响应缺少 Location');
      if (redirectCount === maxRedirects) throw new Error('重定向次数超过限制');
      const next = new URL(location, current);
      redirects.push({ from: current.toString(), to: next.toString(), status: response.status });
      current = next;
      continue;
    }

    const reader = response.body?.getReader();
    const chunks = [];
    let size = 0;
    if (reader) {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        size += value.byteLength;
        if (size > maxBytes) {
          await reader.cancel();
          throw new Error('响应正文超过 2 MiB 上限');
        }
        chunks.push(value);
      }
    }
    const bytes = Buffer.concat(chunks.map((chunk) => Buffer.from(chunk)));
    return {
      url: current.toString(),
      status: response.status,
      ok: response.ok,
      contentType: response.headers.get('content-type') || '',
      text: bytes.toString('utf8'),
      redirects,
    };
  }
  throw new Error('无法完成安全请求');
}

export async function assertTargetAllowsScan(origin, options = {}) {
  try {
    const response = await safeFetchText(new URL('/.well-known/bflabs-agent-readiness-opt-out', origin), {
      ...options,
      maxRedirects: 1,
      maxBytes: 4 * 1024,
      timeoutMs: Math.min(options.timeoutMs ?? 5_000, 5_000),
    });
    if (response.status === 200 && /(?:^|\W)(?:true|deny|blocked|opt[\s_-]?out|do[\s_-]?not[\s_-]?scan)(?:\W|$)/i.test(response.text)) {
      throw new Error('目标站点已通过公开 opt-out 文件拒绝诊断');
    }
  } catch (error) {
    if (/已通过公开 opt-out/.test(error.message)) throw error;
  }
}
