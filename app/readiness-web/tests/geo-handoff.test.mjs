import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import {
  GEO_HANDOFF_TTL_SECONDS,
  GeoHandoffUnavailableError,
  attachGeoHandoff,
  buildGeoHandoffReceipt,
  createD1GeoHandoffStore,
  createMemoryGeoHandoffStore,
  handleGeoHandoffRequest,
  issueGeoHandoff,
  redeemGeoHandoff,
} from '../src/geo-handoff.mjs';

function tokenFromContinueUrl(value) {
  return new URLSearchParams(new URL(value).hash.slice(1)).get('token');
}

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const contractFixture = JSON.parse(fs.readFileSync(path.join(root, 'tests/fixtures/geo-handoff-contract.json'), 'utf8'));

function completedReport() {
  return {
    target: { canonical_origin: 'https://example.com/' },
    scan_fingerprint: `sha256:${'a'.repeat(64)}`,
    scan: { status: 'complete', completed_at: '2026-08-26T10:00:00.000Z' },
    axes: [
      { id: 'discoverable', label: '可发现', score: 100, status: 'pass', checks: [{ rule_id: 'D-1', label: '首页可访问' }] },
      { id: 'understandable', label: '可理解', score: 75, status: 'partial', checks: [] },
      { id: 'actionable', label: '可操作', score: 50, status: 'partial', checks: [] },
    ],
    evidence_gaps: [{ rule_id: 'A-WEBMCP', title: '缺少可发现的 Agent 操作入口', state: 'unknown', owner_route: 'webmcp-enable', ignored: 'do-not-copy' }],
    skill_routes: [{ id: 'webmcp-enable', href: '/skills/webmcp-enable' }],
    disclaimers: { ai_visibility: 'not_measured', business_outcome: 'not_measured' },
    evidence: [{ excerpt: 'must not be transferred' }],
    agent_prompt: 'must not be transferred',
  };
}

test('completed public scan becomes the exact bounded GEO handoff receipt', () => {
  const receipt = buildGeoHandoffReceipt(completedReport());
  assert.deepEqual(receipt, contractFixture.receipt);
  assert.equal('evidence' in receipt, false);
  assert.equal('agent_prompt' in receipt, false);
  assert.equal(JSON.stringify(receipt).includes('must not be transferred'), false);
});

test('handoff rejects incomplete, non-HTTPS, and boundary-breaking reports', () => {
  assert.throws(() => buildGeoHandoffReceipt({ ...completedReport(), scan: { status: 'scanning' } }), /完成诊断/);
  assert.throws(() => buildGeoHandoffReceipt({ ...completedReport(), target: { canonical_origin: 'http://example.com/' } }), /HTTPS/);
  assert.throws(() => buildGeoHandoffReceipt({
    ...completedReport(),
    disclaimers: { ai_visibility: 'measured', business_outcome: 'not_measured' },
  }), /未测量/);
  assert.throws(() => buildGeoHandoffReceipt({
    ...completedReport(),
    skill_routes: [{ id: 'unregistered-skill' }],
  }), /不在诊断范围/);
});

test('issue stores only a SHA-256 token hash and returns a 15-minute WorkBuddy continuation', async () => {
  const now = new Date('2026-08-26T10:00:00.000Z');
  const store = createMemoryGeoHandoffStore();
  const result = await issueGeoHandoff(completedReport(), store, {
    now: () => now,
    randomBytes: () => Uint8Array.from({ length: 32 }, (_, index) => index),
  });

  assert.equal(GEO_HANDOFF_TTL_SECONDS, 900);
  assert.equal(result.schema_version, 'bflabs.geo-handoff-issue/1.0.0');
  assert.equal(result.expires_at, '2026-08-26T10:15:00.000Z');
  const token = tokenFromContinueUrl(result.continue_url);
  assert.equal(new URL(result.continue_url).search, '');
  assert.match(token, /^[A-Za-z0-9_-]{43}$/);

  const rows = store.inspect();
  assert.equal(rows.length, 1);
  assert.match(rows[0].token_hash, /^[a-f0-9]{64}$/);
  assert.notEqual(rows[0].token_hash, token);
  assert.equal(JSON.stringify(rows).includes(token), false);
  assert.deepEqual(rows[0].receipt, contractFixture.receipt);
});

test('redeem has one winner and replay is terminal 410', async () => {
  const now = new Date('2026-08-26T10:00:00.000Z');
  const store = createMemoryGeoHandoffStore();
  const issue = await issueGeoHandoff(completedReport(), store, {
    now: () => now,
    randomBytes: () => new Uint8Array(32).fill(7),
  });
  const token = tokenFromContinueUrl(issue.continue_url);

  const attempts = await Promise.allSettled([
    redeemGeoHandoff(token, store, { now: () => now }),
    redeemGeoHandoff(token, store, { now: () => now }),
  ]);
  assert.equal(attempts.filter((item) => item.status === 'fulfilled').length, 1);
  assert.equal(attempts.filter((item) => item.status === 'rejected').length, 1);
  assert.deepEqual(attempts.find((item) => item.status === 'fulfilled').value, contractFixture.receipt);
  const failure = attempts.find((item) => item.status === 'rejected').reason;
  assert.equal(failure instanceof GeoHandoffUnavailableError, true);
  assert.equal(failure.status, 410);
});

test('expired and malformed tokens fail closed without revealing row state', async () => {
  const issuedAt = new Date('2026-08-26T10:00:00.000Z');
  const store = createMemoryGeoHandoffStore();
  const issue = await issueGeoHandoff(completedReport(), store, {
    now: () => issuedAt,
    randomBytes: () => new Uint8Array(32).fill(9),
  });
  const token = tokenFromContinueUrl(issue.continue_url);

  await assert.rejects(
    () => redeemGeoHandoff(token, store, { now: () => new Date('2026-08-26T10:15:00.001Z') }),
    (error) => error.status === 410 && /失效/.test(error.message),
  );
  await assert.rejects(
    () => redeemGeoHandoff('not-a-token', store, { now: () => issuedAt }),
    (error) => error.status === 410 && /失效/.test(error.message),
  );
});

test('only a server-owned completed scan can attach a handoff issue response', async () => {
  const now = new Date('2026-08-26T10:00:00.000Z');
  const store = createMemoryGeoHandoffStore();
  const report = completedReport();
  const withHandoff = await attachGeoHandoff(report, store, true, {
    now: () => now,
    randomBytes: () => new Uint8Array(32).fill(11),
  });
  const issue = withHandoff.geo_handoff;
  assert.equal(issue.schema_version, 'bflabs.geo-handoff-issue/1.0.0');
  const token = tokenFromContinueUrl(issue.continue_url);
  assert.deepEqual((await redeemGeoHandoff(token, store, { now: () => now })).scan_fingerprint, report.scan_fingerprint);

  const withoutHandoff = await attachGeoHandoff(report, createMemoryGeoHandoffStore(), false, { now: () => now });
  assert.equal('geo_handoff' in withoutHandoff, false);
  const unavailable = await attachGeoHandoff(report, null, true, { now: () => now });
  assert.equal(unavailable.geo_handoff, null);
  assert.equal(unavailable.scan_fingerprint, report.scan_fingerprint);
});

test('public client-supplied issue route is not exposed and redeem preserves the contract', async () => {
  const now = new Date('2026-08-26T10:00:00.000Z');
  const store = createMemoryGeoHandoffStore();
  const forgedIssue = await handleGeoHandoffRequest(new Request('https://readiness.bflabs.cn/api/v1/geo-handoffs', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ report: completedReport() }),
  }), store);
  assert.equal(forgedIssue, null);

  const issue = await issueGeoHandoff(completedReport(), store, {
    now: () => now,
    randomBytes: () => new Uint8Array(32).fill(12),
  });
  const token = tokenFromContinueUrl(issue.continue_url);

  const redeemRequest = () => new Request('https://readiness.bflabs.cn/api/v1/geo-handoffs/redeem', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ token }),
  });
  const redeemed = await handleGeoHandoffRequest(redeemRequest(), store, { now: () => now });
  assert.equal(redeemed.status, 200);
  assert.deepEqual(await redeemed.json(), contractFixture.receipt);

  const replay = await handleGeoHandoffRequest(redeemRequest(), store, { now: () => now });
  assert.equal(replay.status, 410);
  assert.equal((await replay.json()).code, 'geo_handoff_unavailable');
});

test('D1 store redeems with one conditional UPDATE RETURNING statement', async () => {
  const calls = [];
  const database = {
    prepare(sql) {
      const call = { sql, values: [] };
      calls.push(call);
      return {
        bind(...values) {
          call.values = values;
          return {
            async first() { return { receipt_json: JSON.stringify(contractFixture.receipt) }; },
          };
        },
      };
    },
  };
  const row = await createD1GeoHandoffStore(database).consume('a'.repeat(64), Date.parse('2026-08-26T10:00:00.000Z'));
  assert.deepEqual(row.receipt, contractFixture.receipt);
  assert.match(calls[0].sql, /UPDATE geo_handoffs[\s\S]*consumed_at IS NULL[\s\S]*expires_at > \?[\s\S]*RETURNING receipt_json/);
  assert.equal(calls.length, 1);
});

test('expired handoffs are purged without deleting a still-valid link', async () => {
  const store = createMemoryGeoHandoffStore();
  const issuedAt = new Date('2026-08-26T10:00:00.000Z');
  await issueGeoHandoff(completedReport(), store, {
    now: () => issuedAt,
    randomBytes: () => new Uint8Array(32).fill(13),
  });
  assert.equal(await store.purgeExpired(Date.parse('2026-08-26T10:14:59.999Z')), 0);
  assert.equal(store.inspect().length, 1);
  assert.equal(await store.purgeExpired(Date.parse('2026-08-26T10:15:00.000Z')), 1);
  assert.equal(store.inspect().length, 0);
});
