const ENTRY_PREFIX = 'entry:';
export const LEADERBOARD_RETENTION_SECONDS = 30 * 24 * 60 * 60;

function numericScores(entry) {
  return entry.axes.map((axis) => axis.score).filter((score) => Number.isFinite(score));
}

export function buildLeaderboardEntry(report) {
  const origin = new URL(report.target.canonical_origin);
  return {
    schema_version: '1.0.0',
    host: origin.hostname,
    canonical_origin: origin.origin,
    axes: report.axes.map(({ id, label, score, status }) => ({ id, label, score, status })),
    scan_fingerprint: report.scan_fingerprint,
    scanned_at: report.scan.completed_at,
  };
}

export function rankLeaderboard(entries) {
  const enriched = entries.map((entry) => {
    const scores = numericScores(entry);
    const passCount = entry.axes.filter((axis) => axis.status === 'pass').length;
    return {
      ...entry,
      ranking_basis: {
        passed_axes: passCount,
        weakest_axis_score: scores.length ? Math.min(...scores) : null,
        average_axis_score: scores.length ? Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length) : null,
      },
    };
  });
  enriched.sort((left, right) => {
    const a = left.ranking_basis;
    const b = right.ranking_basis;
    return b.passed_axes - a.passed_axes
      || (b.weakest_axis_score ?? -1) - (a.weakest_axis_score ?? -1)
      || (b.average_axis_score ?? -1) - (a.average_axis_score ?? -1)
      || right.scanned_at.localeCompare(left.scanned_at)
      || left.host.localeCompare(right.host);
  });
  return enriched.map((entry, index) => ({ rank: index + 1, ...entry }));
}

export function memoryLeaderboardStore(map = new Map()) {
  return {
    async put(key, value) { map.set(key, value); },
    async get(key) { return map.get(key) || null; },
    async list({ prefix = '' } = {}) {
      return { keys: [...map.keys()].filter((key) => key.startsWith(prefix)).map((name) => ({ name })) };
    },
  };
}

export async function publishToLeaderboard(store, report) {
  if (!store) return { status: 'unavailable', reason: 'leaderboard-storage-not-configured' };
  const entry = buildLeaderboardEntry(report);
  try {
    await store.put(`${ENTRY_PREFIX}${entry.host}`, JSON.stringify(entry), {
      expirationTtl: LEADERBOARD_RETENTION_SECONDS,
    });
    return { status: 'published', host: entry.host, scanned_at: entry.scanned_at };
  } catch (error) {
    return { status: 'unavailable', reason: 'leaderboard-write-failed', detail: error.message };
  }
}

export async function readLeaderboard(store, limit = 100) {
  if (!store) {
    return { schema_version: '1.0.0', storage: 'unavailable', generated_at: new Date().toISOString(), entries: [] };
  }
  const listed = await store.list({ prefix: ENTRY_PREFIX, limit });
  const values = await Promise.all((listed.keys || []).slice(0, limit).map(async ({ name }) => {
    try {
      const value = await store.get(name);
      return value ? JSON.parse(value) : null;
    } catch {
      return null;
    }
  }));
  return {
    schema_version: '1.0.0',
    storage: 'ready',
    generated_at: new Date().toISOString(),
    ranking_method: 'passed_axes > weakest_axis_score > average_axis_score > scanned_at',
    entries: rankLeaderboard(values.filter(Boolean)),
  };
}

export async function readLeaderboardEntry(store, host) {
  const normalized = String(host || '').trim().toLowerCase();
  if (!store || !/^[a-z0-9.-]+$/.test(normalized) || normalized.startsWith('.') || normalized.endsWith('.')) return null;
  try {
    const value = await store.get(`${ENTRY_PREFIX}${normalized}`);
    return value ? JSON.parse(value) : null;
  } catch {
    return null;
  }
}
