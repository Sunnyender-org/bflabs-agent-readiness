#!/usr/bin/env python3
"""Verify a site's public same-origin MCP surface with read-only task calls."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


USER_AGENT = "webmcp-enable/0.1 verification"


def request_json(url: str, payload: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, str]]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json, text/event-stream", "User-Agent": USER_AGENT}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method="GET" if data is None else "POST")
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read(2 * 1024 * 1024)
        return json.loads(body), {key.lower(): value for key, value in response.headers.items()}


def post_rpc(url: str, method: str, params: dict[str, Any], rpc_id: int, session_id: str | None) -> tuple[dict[str, Any], str | None]:
    payload = {"jsonrpc": "2.0", "id": rpc_id, "method": method, "params": params}
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=25) as response:
        body = response.read(2 * 1024 * 1024)
        next_session = response.headers.get("Mcp-Session-Id") or session_id
        return json.loads(body), next_session


def flatten_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(f"{key} {flatten_text(item)}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(flatten_text(item) for item in value)
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text("utf-8"))
    origin = plan["origin"].rstrip("/")
    mcp_url = plan.get("mcp_url") or f"{origin}/mcp"
    if urllib.parse.urlparse(mcp_url).netloc != urllib.parse.urlparse(origin).netloc:
        raise SystemExit("FAIL: this verifier only permits same-origin MCP URLs")

    receipt: dict[str, Any] = {
        "schema_version": "0.1.0",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "origin": origin,
        "mcp_url": mcp_url,
        "server_card": {"status": "not_checked"},
        "tools_list": {"status": "not_checked"},
        "tasks": [],
        "status": "failed",
    }

    try:
        card, _ = request_json(f"{origin}/.well-known/mcp/server-card.json")
        receipt["server_card"] = {"status": "pass", "name": card.get("name"), "remotes": card.get("remotes", [])}

        session_id = None
        initialize, session_id = post_rpc(
            mcp_url,
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "webmcp-enable-verifier", "version": "0.1.0"},
            },
            1,
            session_id,
        )
        if "error" in initialize:
            raise RuntimeError(f"initialize failed: {initialize['error']}")

        tools_result, session_id = post_rpc(mcp_url, "tools/list", {}, 2, session_id)
        tools = tools_result.get("result", {}).get("tools", [])
        tool_map = {tool.get("name"): tool for tool in tools}
        receipt["tools_list"] = {
            "status": "pass",
            "tools": [
                {
                    "name": tool.get("name"),
                    "annotations": tool.get("annotations", {}),
                    "has_input_schema": isinstance(tool.get("inputSchema"), dict),
                }
                for tool in tools
            ],
        }

        rpc_id = 10
        for task in plan.get("tasks", []):
            if task.get("read_only") is not True:
                raise RuntimeError(f"task {task.get('id')} is not explicitly read-only")
            tool_name = task["tool"]
            descriptor = tool_map.get(tool_name)
            if descriptor is None:
                receipt["tasks"].append({"id": task["id"], "tool": tool_name, "status": "fail", "error": "tool not advertised"})
                continue
            if descriptor.get("annotations", {}).get("readOnlyHint") is not True:
                receipt["tasks"].append({"id": task["id"], "tool": tool_name, "status": "fail", "error": "tool lacks readOnlyHint"})
                continue
            result, session_id = post_rpc(
                mcp_url,
                "tools/call",
                {"name": tool_name, "arguments": task.get("arguments", {})},
                rpc_id,
                session_id,
            )
            rpc_id += 1
            rendered = flatten_text(result)
            missing = [item for item in task.get("expected_contains", []) if item not in rendered]
            receipt["tasks"].append(
                {
                    "id": task["id"],
                    "tool": tool_name,
                    "status": "pass" if not missing and "error" not in result else "fail",
                    "missing_expected": missing,
                    "result": result,
                }
            )

        receipt["status"] = "pass" if receipt["tasks"] and all(task["status"] == "pass" for task in receipt["tasks"]) else "failed"
    except (OSError, ValueError, KeyError, RuntimeError, urllib.error.URLError) as exc:
        receipt["error"] = str(exc)

    rendered_receipt = json.dumps(receipt, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered_receipt + "\n", "utf-8")
    else:
        print(rendered_receipt)
    return 0 if receipt["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
