"""Evidence normalization and claim linkage."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Iterable, List, Tuple


def stable_claim_id(text: str) -> str:
    return "claim_{}".format(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12])


def build_ledger(
    evidence_sources: List[Dict[str, Any]],
    claims: Iterable[Tuple[str, str]],
) -> Dict[str, Any]:
    by_summary = {item["summary"]: item for item in evidence_sources}
    ledger_claims = []
    seen_claims = set()
    for text, support_level in claims:
        if text in seen_claims:
            continue
        seen_claims.add(text)
        source = by_summary.get(text)
        evidence_ids = [source["id"]] if source else []
        ledger_claims.append(
            {
                "id": stable_claim_id(text),
                "text": text,
                "evidence_ids": evidence_ids,
                "support_level": support_level if source else "unsupported",
            }
        )

    items = []
    for source in evidence_sources:
        item = dict(source)
        item.setdefault("fact_version", None)
        items.append(item)
    return {"schema_version": "1.0.0", "items": items, "claims": ledger_claims}
