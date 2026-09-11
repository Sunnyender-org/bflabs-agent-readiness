"""One-time business evidence transfers through the existing GEO service API."""
from __future__ import annotations

from copy import deepcopy

CONTEXT_FIELDS = ("business_window", "selected_import_ids", "selected_metric", "selected_filters",
                  "first_paid_lookback", "cohort_maturity")


def to_service(document: dict, experiment: dict | None = None) -> list[dict]:
    batches = []
    context = {key: deepcopy(experiment[key]) for key in CONTEXT_FIELDS if experiment and key in experiment}
    for batch in document["imports"]:
        events = []
        for raw in batch["events"]:
            event = deepcopy(raw)
            event.setdefault("visitor_id", None)
            event.setdefault("session_id", None)
            if event["type"] == "refund" and event.get("order_id"):
                event["original_order_id"] = event["order_id"]
            events.append(event)
        links = [{"id": link["link_id"], "visitor_id": link.get("visitor_id"),
                  "session_id": link.get("session_id"), "user_id": link["user_id"],
                  "bind_evidence": link["evidence"], "bound_at": link["linked_at"]}
                 for link in document.get("identity_links", [])]
        surveys = []
        for raw in document.get("surveys", []):
            row = deepcopy(raw)
            row["id"] = row.pop("survey_id")
            surveys.append(row)
        metadata = {key: deepcopy(value) for key, value in batch.items() if key not in {"events", "window"}}
        metadata["timezone"] = batch["window"]["timezone"]
        metadata["schema_version"] = document["schema_version"]
        item = {"source": f'{batch["source"]}:{batch["import_id"]}',
                "period_start": batch["window"]["start"], "period_end": batch["window"]["end"],
                "events": events, "import_id": batch["import_id"],
                "portable_metadata": metadata, "record_context": context}
        if context.get("business_window"):
            item["as_of"] = context["business_window"]["as_of"]
        if "selected_import_ids" in context:
            item["selected_import_ids"] = context["selected_import_ids"]
        if "identity_links" in document:
            item["identity_links"] = links
        if "surveys" in document:
            item["surveys"] = surveys
        batches.append(item)
    return batches


def from_service(view: dict) -> dict:
    project = view["project"]
    imports = []
    versions = set()
    for batch in view["business_batches"]:
        ref = next((row for row in project.get("business_imports", [])
                    if row["source"] == batch["source"] and row["period_start"] == batch["period_start"]
                    and row["period_end"] == batch["period_end"]), None)
        if not ref or "portable_metadata" not in ref:
            raise ValueError("This export contains native service records; retain them as a service snapshot instead of guessing a portable mapping.")
        metadata = deepcopy(ref["portable_metadata"])
        versions.add(metadata.pop("schema_version"))
        timezone = metadata.pop("timezone")
        events = []
        for raw in batch["events"]:
            event = {key: deepcopy(value) for key, value in raw.items()
                     if key not in {"provenance", "original_order_id"}}
            # The native service has nullable identity slots; omit unknown optional IDs.
            for key in ("visitor_id", "session_id", "user_id"):
                if event.get(key) is None:
                    event.pop(key, None)
            events.append(event)
        imports.append({**metadata, "window": {"start": batch["period_start"], "end": batch["period_end"], "timezone": timezone}, "events": events})
    document = {"schema_version": "1.1.0" if "1.1.0" in versions else "1.0.0", "imports": imports}
    if "identity_links" in project:
        document["identity_links"] = [{"link_id": row["id"], "visitor_id": row.get("visitor_id"),
             "session_id": row.get("session_id"), "user_id": row["user_id"],
             "evidence": row["bind_evidence"], "linked_at": row["bound_at"]} for row in project["identity_links"]]
    if "surveys" in project:
        document["surveys"] = []
        for raw in project["surveys"]:
            if "respondent_ref" not in raw:
                raise ValueError("Native service surveys stay in the original snapshot; do not infer missing portable evidence.")
            row = deepcopy(raw)
            row["survey_id"] = row.pop("id")
            document["surveys"].append(row)
    return {"business_events": document, "experiment_business_fields": deepcopy(project.get("record_context", {}))}
