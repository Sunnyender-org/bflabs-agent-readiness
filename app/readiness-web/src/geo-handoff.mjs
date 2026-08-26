export const GEO_HANDOFF_TTL_SECONDS = 15 * 60;
export const GEO_HANDOFF_SCHEMA_VERSION = 'bflabs.geo-handoff/1.0.0';
export const GEO_HANDOFF_ISSUE_SCHEMA_VERSION = 'bflabs.geo-handoff-issue/1.0.0';

const TOKEN_BYTES = 32;
const TOKEN_PATTERN = /^[A-Za-z0-9_-]{43}$/;
const FINGERPRINT_PATTERN = /^sha256:[a-f0-9]{64}$/;
const TERMINAL_SCAN_STATUSES = new Set(['complete', 'partial', 'blocked']);
const AXIS_IDS = ['discoverable', 'understandable', 'actionable'];
const AXIS_LABELS = { discoverable: '可发现', understandable: '可理解', actionable: '可操作' };
const AXIS_STATUSES = new Set(['pass', 'partial', 'fail', 'unknown', 'blocked']);
const RECOMMENDED_SKILLS = new Set(['geo-optimize', 'webmcp-enable']);
const MAX_GAPS = 24;
const MAX_RECEIPT_BYTES = 16 * 1024;

export class GeoHandoffInputError extends Error {
  constructor(message) {
    super(message);
    this.name = 'GeoHandoffInputError';
    this.status = 400;
    this.code = 'geo_handoff_invalid';
  }
}

export class GeoHandoffUnavailableError extends Error {
  constructor() {
    super('这条继续链接已失效，请从诊断报告重新生成');
    this.name = 'GeoHandoffUnavailableError';
    this.status = 410;
    this.code = 'geo_handoff_unavailable';
  }
}

function boundedString(value, field, maxLength) {
  if (typeof value !== 'string' || !value.trim() || value.length > maxLength) {
    throw new GeoHandoffInputError(`${field} 不符合 GEO 交接要求`);
  }
  return value.trim();
}

function canonicalHttpsOrigin(value) {
  let url;
  try {
    url = new URL(value);
  } catch {
    throw new GeoHandoffInputError('诊断目标必须是公开 HTTPS 网站');
  }
  if (url.protocol !== 'https:' || url.username || url.password || url.port || url.pathname !== '/' || url.search || url.hash) {
    throw new GeoHandoffInputError('诊断目标必须是公开 HTTPS 网站首页');
  }
  return url.origin;
}

function sanitizeAxis(axis, expectedId) {
  if (!axis || axis.id !== expectedId || !AXIS_STATUSES.has(axis.status)) {
    throw new GeoHandoffInputError('诊断三轴结果不完整');
  }
  const score = axis.score === null ? null : Number(axis.score);
  if (score !== null && (!Number.isInteger(score) || score < 0 || score > 100)) {
    throw new GeoHandoffInputError('诊断三轴分数无效');
  }
  return {
    id: expectedId,
    label: AXIS_LABELS[expectedId],
    score,
    status: axis.status,
  };
}

function sanitizeGap(gap) {
  if (!gap || typeof gap !== 'object') throw new GeoHandoffInputError('证据缺口无效');
  return {
    rule_id: boundedString(gap.rule_id, '缺口编号', 80),
    title: boundedString(gap.title, '缺口标题', 240),
    state: boundedString(gap.state, '缺口状态', 40),
    owner_route: boundedString(gap.owner_route, '建议路径', 80),
  };
}

export function buildGeoHandoffReceipt(report) {
  if (!report || typeof report !== 'object' || !TERMINAL_SCAN_STATUSES.has(report.scan?.status)) {
    throw new GeoHandoffInputError('请先完成诊断，再继续到 WorkBuddy');
  }
  const targetOrigin = canonicalHttpsOrigin(report.target?.canonical_origin);
  if (!FINGERPRINT_PATTERN.test(String(report.scan_fingerprint || ''))) {
    throw new GeoHandoffInputError('扫描指纹无效');
  }
  if (!Array.isArray(report.axes) || report.axes.length !== AXIS_IDS.length) {
    throw new GeoHandoffInputError('诊断三轴结果不完整');
  }
  const axesById = new Map(report.axes.map((axis) => [axis.id, axis]));
  if (axesById.size !== AXIS_IDS.length) throw new GeoHandoffInputError('诊断三轴结果不完整');
  const axes = AXIS_IDS.map((id) => sanitizeAxis(axesById.get(id), id));
  const gaps = Array.isArray(report.evidence_gaps) ? report.evidence_gaps : [];
  if (gaps.length > MAX_GAPS) throw new GeoHandoffInputError('证据缺口超过交接上限');
  if (report.disclaimers?.ai_visibility !== 'not_measured' || report.disclaimers?.business_outcome !== 'not_measured') {
    throw new GeoHandoffInputError('AI 可见度和业务结果必须保持未测量');
  }
  const scannedAtInput = report.scan.completed_at == null ? null : boundedString(report.scan.completed_at, '扫描时间', 40);
  if (scannedAtInput !== null && Number.isNaN(Date.parse(scannedAtInput))) throw new GeoHandoffInputError('扫描时间无效');
  const scannedAt = scannedAtInput === null ? null : new Date(scannedAtInput).toISOString();
  const recommendedSkillInput = Array.isArray(report.skill_routes) && report.skill_routes[0]?.id
    ? boundedString(report.skill_routes[0].id, '建议 Skill', 80)
    : null;
  if (recommendedSkillInput !== null && !RECOMMENDED_SKILLS.has(recommendedSkillInput)) {
    throw new GeoHandoffInputError('建议 Skill 不在诊断范围内');
  }
  const recommendedSkill = recommendedSkillInput;
  const receipt = {
    schema_version: GEO_HANDOFF_SCHEMA_VERSION,
    target_origin: targetOrigin,
    scan_fingerprint: report.scan_fingerprint,
    scanned_at: scannedAt,
    axes,
    evidence_gaps: gaps.map(sanitizeGap),
    recommended_skill: recommendedSkill,
    disclaimers: {
      ai_visibility: 'not_measured',
      business_outcome: 'not_measured',
    },
  };
  if (new TextEncoder().encode(JSON.stringify(receipt)).byteLength > MAX_RECEIPT_BYTES) {
    throw new GeoHandoffInputError('诊断结果超过交接上限');
  }
  return receipt;
}

function bytesToBase64Url(bytes) {
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/, '');
}

async function sha256Hex(value) {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

function defaultRandomBytes() {
  return crypto.getRandomValues(new Uint8Array(TOKEN_BYTES));
}

export async function issueGeoHandoff(report, store, options = {}) {
  if (!store?.insert) throw new Error('GEO handoff storage is unavailable');
  const receipt = buildGeoHandoffReceipt(report);
  const now = (options.now || (() => new Date()))();
  const bytes = (options.randomBytes || defaultRandomBytes)();
  if (!(bytes instanceof Uint8Array) || bytes.byteLength !== TOKEN_BYTES) throw new Error('GEO handoff token source must return 32 bytes');
  const token = bytesToBase64Url(bytes);
  const tokenHash = await sha256Hex(token);
  const expiresAt = new Date(now.getTime() + GEO_HANDOFF_TTL_SECONDS * 1000);
  await store.insert({
    token_hash: tokenHash,
    receipt,
    created_at: now.getTime(),
    expires_at: expiresAt.getTime(),
  });
  const continueUrl = new URL('/geo/claim', options.continueBaseUrl || 'https://wb.bflabs.app');
  continueUrl.hash = `token=${encodeURIComponent(token)}`;
  return {
    schema_version: GEO_HANDOFF_ISSUE_SCHEMA_VERSION,
    continue_url: continueUrl.toString(),
    expires_at: expiresAt.toISOString(),
  };
}

export async function attachGeoHandoff(report, store, requested, options = {}) {
  if (!requested) return report;
  try {
    return { ...report, geo_handoff: await issueGeoHandoff(report, store, options) };
  } catch {
    return { ...report, geo_handoff: null };
  }
}

export async function redeemGeoHandoff(token, store, options = {}) {
  if (!store?.consume || !TOKEN_PATTERN.test(String(token || ''))) throw new GeoHandoffUnavailableError();
  const tokenHash = await sha256Hex(token);
  const row = await store.consume(tokenHash, (options.now || (() => new Date()))().getTime());
  if (!row) throw new GeoHandoffUnavailableError();
  return row.receipt;
}

export function createMemoryGeoHandoffStore(rows = new Map()) {
  return {
    async insert(row) {
      if (rows.has(row.token_hash)) throw new Error('GEO handoff token collision');
      rows.set(row.token_hash, structuredClone({ ...row, consumed_at: null }));
    },
    async consume(tokenHash, nowMs) {
      const row = rows.get(tokenHash);
      if (!row || row.consumed_at !== null || row.expires_at <= nowMs) return null;
      row.consumed_at = nowMs;
      return { receipt: structuredClone(row.receipt) };
    },
    async purgeExpired(nowMs) {
      let deleted = 0;
      for (const [tokenHash, row] of rows) {
        if (row.expires_at <= nowMs) {
          rows.delete(tokenHash);
          deleted += 1;
        }
      }
      return deleted;
    },
    inspect() {
      return [...rows.values()].map((row) => structuredClone(row));
    },
  };
}

export function createD1GeoHandoffStore(database) {
  if (!database?.prepare) return null;
  return {
    async insert(row) {
      await database.prepare(`
        INSERT INTO geo_handoffs (token_hash, receipt_json, created_at, expires_at, consumed_at)
        VALUES (?, ?, ?, ?, NULL)
      `).bind(row.token_hash, JSON.stringify(row.receipt), row.created_at, row.expires_at).run();
    },
    async consume(tokenHash, nowMs) {
      const row = await database.prepare(`
        UPDATE geo_handoffs
        SET consumed_at = ?
        WHERE token_hash = ? AND consumed_at IS NULL AND expires_at > ?
        RETURNING receipt_json
      `).bind(nowMs, tokenHash, nowMs).first();
      if (!row?.receipt_json) return null;
      return { receipt: JSON.parse(row.receipt_json) };
    },
    async purgeExpired(nowMs) {
      const result = await database.prepare('DELETE FROM geo_handoffs WHERE expires_at <= ?').bind(nowMs).run();
      return Number(result?.meta?.changes || 0);
    },
  };
}

function jsonResponse(value, status = 200, contentType = 'application/json; charset=utf-8') {
  return new Response(JSON.stringify(value), {
    status,
    headers: {
      'content-type': contentType,
      'cache-control': 'no-store',
      'x-content-type-options': 'nosniff',
    },
  });
}

function problemResponse(error, instance) {
  const status = Number(error?.status) || 500;
  const statusCode = status === 429 ? 'rate_limit_exceeded' : status === 413 ? 'geo_handoff_too_large' : 'geo_handoff_invalid';
  const code = status >= 500 ? 'geo_handoff_failed' : (error.code || statusCode);
  const unavailable = code === 'geo_handoff_unavailable';
  const title = unavailable ? '继续链接已失效' : status >= 500 ? '继续链接暂时不可用' : '无法创建继续链接';
  const detail = status >= 500 ? '继续链接暂时不可用，请使用报告中的复制功能' : error.message;
  return jsonResponse({
    type: `https://readiness.bflabs.cn/problems/${code}`,
    title,
    status,
    code,
    detail,
    resolution: unavailable ? '返回诊断报告，重新生成一条继续链接。' : '使用当前诊断报告中的复制功能，或稍后重试。',
    instance,
  }, status, 'application/problem+json; charset=utf-8');
}

async function readBoundedJson(request) {
  const text = await request.text();
  if (new TextEncoder().encode(text).byteLength > 24 * 1024) {
    throw Object.assign(new GeoHandoffInputError('继续链接所需内容超过上限'), { status: 413, code: 'geo_handoff_too_large' });
  }
  try {
    return JSON.parse(text || '{}');
  } catch {
    throw new GeoHandoffInputError('继续链接请求格式无效');
  }
}

export async function handleGeoHandoffRequest(request, store, options = {}) {
  const url = new URL(request.url);
  const isRedeem = url.pathname === '/api/v1/geo-handoffs/redeem';
  if (!isRedeem) return null;
  if (request.method !== 'POST') {
    return problemResponse(Object.assign(new Error('请使用 POST 请求'), { status: 405, code: 'method_not_allowed' }), url.pathname);
  }
  if (!store) {
    return problemResponse(Object.assign(new Error('暂时无法创建或读取继续链接'), { status: 503 }), url.pathname);
  }
  try {
    const body = await readBoundedJson(request);
    const value = await redeemGeoHandoff(body.token, store, options);
    return jsonResponse(value);
  } catch (error) {
    return problemResponse(error, url.pathname);
  }
}
