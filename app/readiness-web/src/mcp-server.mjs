import { methodology, problemDetails, reportToMarkdown } from './product-contract.mjs';

const TOOLS = [
  {
    name: 'bflabs_scan_public_site',
    description: 'Run a fresh, bounded BFLabs Agent Readiness scan for a public website. This does not publish the result to the leaderboard.',
    inputSchema: { type: 'object', properties: { url: { type: 'string' } }, required: ['url'], additionalProperties: false },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: false, openWorldHint: true },
  },
  {
    name: 'bflabs_get_methodology',
    description: 'Explain the three readiness axes, leaderboard ordering, and measurement boundaries.',
    inputSchema: { type: 'object', properties: {}, additionalProperties: false },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
  },
  {
    name: 'bflabs_get_skill',
    description: 'Read the BFLabs Agent Readiness root Skill or one registered child Skill.',
    inputSchema: { type: 'object', properties: { skill_id: { type: 'string' } }, required: ['skill_id'], additionalProperties: false },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
  },
  {
    name: 'bflabs_get_leaderboard',
    description: 'Read the opt-in public Agent Readiness leaderboard. It contains readiness only, never AI visibility or business outcome.',
    inputSchema: { type: 'object', properties: {}, additionalProperties: false },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
  },
];

const response = (id, result, status = 200) => new Response(JSON.stringify({ jsonrpc: '2.0', id, result }), {
  status,
  headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', 'mcp-protocol-version': '2025-06-18' },
});

const errorResponse = (id, code, message, data = null, status = 400) => new Response(JSON.stringify({
  jsonrpc: '2.0', id, error: { code, message, ...(data ? { data } : {}) },
}), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' } });

function toolResult(text, structuredContent) {
  return { content: [{ type: 'text', text }], structuredContent };
}

export async function handleMcp(request, context) {
  if (request.method !== 'POST') {
    return errorResponse(null, -32600, 'Use POST with a JSON-RPC 2.0 request.', null, 405);
  }
  let payload;
  try {
    payload = await request.json();
  } catch (error) {
    return errorResponse(null, -32700, 'Invalid JSON.', problemDetails(error, '/mcp'));
  }
  const { id = null, method, params = {} } = payload || {};
  if (method === 'initialize') {
    return response(id, {
      protocolVersion: '2025-06-18',
      capabilities: { tools: { listChanged: false } },
      serverInfo: { name: 'io.bflabs.agent-readiness', title: 'BFLabs Agent Readiness', version: '1.0.0' },
    });
  }
  if (method === 'notifications/initialized') return new Response(null, { status: 202 });
  if (method === 'ping') return response(id, {});
  if (method === 'tools/list') return response(id, { tools: TOOLS });
  if (method !== 'tools/call') return errorResponse(id, -32601, `Unknown method: ${method}`);

  const name = params?.name;
  const args = params?.arguments || {};
  try {
    if (name === 'bflabs_scan_public_site') {
      if (!args.url) return errorResponse(id, -32602, 'url is required');
      const report = await context.scan(args.url);
      return response(id, toolResult(reportToMarkdown(report), report));
    }
    if (name === 'bflabs_get_methodology') {
      const value = methodology();
      return response(id, toolResult(JSON.stringify(value, null, 2), value));
    }
    if (name === 'bflabs_get_skill') {
      const body = context.skills?.[args.skill_id];
      if (!body) return errorResponse(id, -32602, `Unknown skill_id: ${args.skill_id}`);
      return response(id, toolResult(body, { skill_id: args.skill_id, body }));
    }
    if (name === 'bflabs_get_leaderboard') {
      const board = await context.leaderboard();
      return response(id, toolResult(JSON.stringify(board, null, 2), board));
    }
    return errorResponse(id, -32602, `Unknown tool: ${name}`);
  } catch (error) {
    const problem = problemDetails(error, '/mcp');
    return errorResponse(id, -32000, problem.title, problem, problem.status >= 500 ? 500 : 400);
  }
}

export { TOOLS as MCP_TOOLS };
