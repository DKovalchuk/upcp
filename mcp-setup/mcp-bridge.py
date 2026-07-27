#!/usr/bin/env python3
"""Stdio-HTTP bridge for UPCP MCP server.

Reads JSON-RPC 2.0 messages from stdin, forwards them to the UPCP HTTP
endpoint, and writes responses to stdout. Stderr is used for logging.

Usage:
    python3 mcp-bridge.py
    python3 mcp-bridge.py --upcp-url http://your-host:3080/mcp/
    UPCP_MCP_URL=http://your-host:3080/mcp/ python3 mcp-bridge.py
"""

import json
import os
import sys
import urllib.error
import urllib.request


def resolve_url() -> str:
    """Resolve UPCP MCP URL from args, env, or default."""
    for i, arg in enumerate(sys.argv):
        if arg == "--upcp-url" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return os.environ.get("UPCP_MCP_URL", "http://upcp.local:3080/mcp/")


UPCP_URL = resolve_url()
DEBUG = os.environ.get("UPCP_MCP_DEBUG", "").lower() in ("1", "true", "yes")


def log(msg: str) -> None:
    if DEBUG:
        sys.stderr.write(f"[upcp-bridge] {msg}\n")
        sys.stderr.flush()


def send_error(req_id: object, code: int, message: str) -> None:
    resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()


def forward(request: dict) -> dict:
    """Forward a JSON-RPC request to the UPCP MCP server via HTTP POST."""
    payload = json.dumps(request).encode("utf-8")
    http_req = urllib.request.Request(
        UPCP_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    req_id = request.get("id")

    try:
        with urllib.request.urlopen(http_req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            log(f"HTTP {resp.status} for {request.get('method')}")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        log(f"HTTP {exc.code}: {err_body[:200]}")
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": f"HTTP {exc.code}: {err_body[:500]}"},
        }
    except urllib.error.URLError as exc:
        log(f"Connection error: {exc.reason}")
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": f"Cannot reach UPCP at {UPCP_URL}: {exc.reason}"},
        }
    except Exception as exc:
        log(f"Unexpected error: {exc}")
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32603, "message": str(exc)},
        }


def main() -> None:
    log(f"Bridge started, UPCP URL: {UPCP_URL}")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            send_error(None, -32700, "Parse error")
            continue

        log(f" <- {request.get('method', '?')} id={request.get('id', 'N/A')}")

        # Notifications (no id) get no response per JSON-RPC spec
        if "id" not in request:
            log("   (notification, skipped)")
            continue

        response = forward(request)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()

    log("Bridge stdin closed")


if __name__ == "__main__":
    main()
