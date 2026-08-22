from __future__ import annotations

import io
import json
import unittest

from bflabs_readiness.remote import scan_public_site


class Response:
    def __init__(self, status, body, content_type="application/json"):
        self.status = status
        self.body = body.encode("utf-8")
        self.headers = {"Content-Type": content_type}

    def getcode(self):
        return self.status

    def read(self):
        return self.body


class RemoteScanTests(unittest.TestCase):
    def test_polls_local_async_contract_and_requests_markdown_for_final_report(self):
        requests = []
        responses = iter([
            Response(202, json.dumps({"status_url": "/api/v1/scans/rpt_1"})),
            Response(200, "# BFLabs report", "text/markdown; charset=utf-8"),
        ])

        def opener(request, timeout):
            requests.append(request)
            return next(responses)

        content_type, text = scan_public_site(
            "https://example.com", "http://127.0.0.1:4177", output_format="markdown",
            opener=opener, sleeper=lambda _seconds: None,
        )
        self.assertEqual(content_type, "text/markdown")
        self.assertEqual(text, "# BFLabs report")
        self.assertEqual(requests[1].get_header("Accept"), "text/markdown")

    def test_publish_flag_is_explicit(self):
        captured = []

        def opener(request, timeout):
            captured.append(json.loads(request.data.decode("utf-8")))
            return Response(200, '{"scan_fingerprint":"sha256:test"}')

        scan_public_site("https://example.com", "https://readiness.example", publish_to_leaderboard=True, opener=opener)
        self.assertEqual(captured[0]["publish_to_leaderboard"], True)


if __name__ == "__main__":
    unittest.main()
