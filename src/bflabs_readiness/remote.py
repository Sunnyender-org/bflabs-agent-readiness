"""Public diagnostic API client used by the packaged CLI."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Tuple


def _read_response(response) -> Tuple[int, str, str]:
    status = getattr(response, "status", response.getcode())
    content_type = response.headers.get("Content-Type", "application/json").split(";", 1)[0].strip()
    return status, content_type, response.read().decode("utf-8")


def _request(opener, request, timeout: float) -> Tuple[int, str, str]:
    try:
        return _read_response(opener(request, timeout=timeout))
    except urllib.error.HTTPError as error:
        return _read_response(error)


def _raise_problem(text: str, status: int) -> None:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError("diagnostic API returned HTTP {}".format(status))
    detail = value.get("detail") or value.get("error") or "diagnostic API failed"
    resolution = value.get("resolution")
    raise RuntimeError("{}{}".format(detail, " Resolution: {}".format(resolution) if resolution else ""))


def scan_public_site(
    target: str,
    endpoint: str,
    output_format: str = "json",
    publish_to_leaderboard: bool = False,
    timeout: float = 90.0,
    opener: Callable = urllib.request.urlopen,
    sleeper: Callable[[float], None] = time.sleep,
) -> Tuple[str, str]:
    base = endpoint.rstrip("/")
    accept = "text/markdown" if output_format == "markdown" else "application/json"
    body = json.dumps({"url": target, "publish_to_leaderboard": publish_to_leaderboard}).encode("utf-8")
    request = urllib.request.Request(
        base + "/api/v1/scans",
        data=body,
        headers={"Accept": accept, "Content-Type": "application/json", "User-Agent": "bflabs-readiness-cli/0.3"},
        method="POST",
    )
    started = time.monotonic()
    status, content_type, text = _request(opener, request, timeout)
    if status >= 400:
        _raise_problem(text, status)
    if status == 200:
        return content_type, text
    if status != 202:
        raise RuntimeError("diagnostic API returned unexpected HTTP {}".format(status))
    value = json.loads(text)
    status_url = urllib.parse.urljoin(base + "/", value["status_url"])

    while time.monotonic() - started < timeout:
        poll = urllib.request.Request(status_url, headers={"Accept": accept, "User-Agent": "bflabs-readiness-cli/0.3"})
        status, content_type, text = _request(opener, poll, timeout)
        if status >= 400:
            _raise_problem(text, status)
        if content_type == "text/markdown":
            return content_type, text
        report = json.loads(text)
        if report.get("status") in {"complete", "partial", "blocked"} or "scan_fingerprint" in report:
            return content_type, text
        sleeper(0.7)
    raise RuntimeError("diagnostic scan did not complete within {:.0f} seconds".format(timeout))
