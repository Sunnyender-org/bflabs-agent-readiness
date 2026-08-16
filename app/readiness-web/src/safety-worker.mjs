const BLOCKED_HOST_SUFFIXES = ['.local', '.internal', '.localhost', '.home.arpa'];

function isIpLiteral(hostname) {
  const value = hostname.replace(/^\[|\]$/g, '');
  return /^(?:\d{1,3}\.){3}\d{1,3}$/.test(value) || value.includes(':');
}

export function normalizeTarget(input) {
  const value = String(input || '').trim();
  if (!value) throw new Error('请输入公开域名或 HTTPS URL');
  const withScheme = /^[a-z][a-z0-9+.-]*:/i.test(value) ? value : `https://${value}`;
  const url = new URL(withScheme);
  if (!['http:', 'https:'].includes(url.protocol)) throw new Error('只支持 HTTP 和 HTTPS');
  if (url.username || url.password) throw new Error('URL 不能包含账号或凭据');
  if (url.port && !['80', '443'].includes(url.port)) throw new Error('只允许 80 和 443 端口');
  const hostname = url.hostname.replace(/^\[|\]$/g, '').toLowerCase();
  if (isIpLiteral(hostname)) throw new Error('不接受 IP 地址，请使用公开域名');
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

export async function safeFetchText(input, options = {}) {
  const maxRedirects = options.maxRedirects ?? 3;
  const maxBytes = options.maxBytes ?? 1024 * 1024;
  const timeoutMs = options.timeoutMs ?? 8_000;
  let current = new URL(input);
  const redirects = [];

  for (let redirectCount = 0; redirectCount <= maxRedirects; redirectCount += 1) {
    normalizeTarget(current);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort('timeout'), timeoutMs);
    let response;
    try {
      const headers = {
        Accept: options.accept || 'text/html, application/json, text/plain, application/xml;q=0.9',
        'User-Agent': 'BFLabs-Agent-Readiness/1.0 public-beta; +https://readiness.bflabs.cn/privacy',
      };
      if (options.contentType) headers['Content-Type'] = options.contentType;
      response = await fetch(current, {
        method: options.method || 'GET',
        body: options.body,
        headers,
        redirect: 'manual',
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
      normalizeTarget(next);
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
          throw new Error('响应正文超过 1 MiB 上限');
        }
        chunks.push(value);
      }
    }
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) {
      bytes.set(chunk, offset);
      offset += chunk.byteLength;
    }
    return {
      url: current.toString(),
      status: response.status,
      ok: response.ok,
      contentType: response.headers.get('content-type') || '',
      text: new TextDecoder().decode(bytes),
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
