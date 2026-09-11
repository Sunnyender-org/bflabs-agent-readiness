"""Pure offline business attribution. Does not require AI observations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse


SCHEMA_VERSION = "1.1.0"
RULE_VERSION = "ba-1.1.0"
VIEW_WARNING = "各来源视角的金额不能相加。同一笔订单只计算一次。"
EVENT_TYPES = (
    "visit",
    "signup",
    "lead",
    "activation",
    "purchase",
    "refund",
    "first_success_call",
)
NOT_PAID_STATUSES = {"pending", "failed", "test"}
FORBIDDEN_LINK_EVIDENCE = {
    "ip",
    "ip_match",
    "ip_fingerprint",
    "same_page",
    "nearby_time",
    "same_page_nearby_time",
}
AI_REFERRER_HOSTS = {
    "chat.openai.com",
    "chatgpt.com",
    "www.chatgpt.com",
    "perplexity.ai",
    "www.perplexity.ai",
    "claude.ai",
    "www.claude.ai",
    "gemini.google.com",
}
CURRENCY_LABELS = {
    "USD": "美元",
    "EUR": "欧元",
    "GBP": "英镑",
    "CNY": "人民币",
    "JPY": "日元",
}
ZERO_DECIMAL_CURRENCIES = {"JPY", "KRW", "VND"}
RETURN_KEYS = (
    "schema_version",
    "as_of",
    "rule_version",
    "event_counts",
    "user_funnel",
    "session_funnel",
    "identity_conflicts",
    "views",
    "view_warning",
    "cashflow",
    "cohort_net",
    "unlinked_refunds",
    "test_or_self_promo",
    "unknown_source_visits",
    "comparison",
    "limitations",
    "measurement_status",
)


def analyze(
    events_doc: dict,
    *,
    experiment_doc: dict | None = None,
    identity_links: list | None = None,
    surveys: list | None = None,
    as_of: str | None = None,
    selected_import_ids: list[str] | None = None,
    metric: str | None = None,
    filters: dict | None = None,
) -> dict:
    """Pure offline analysis. Must not require AI observations or a baseline sample."""
    experiment = experiment_doc if isinstance(experiment_doc, dict) else {}
    imports = list((events_doc or {}).get("imports") or [])
    selected_ids = (
        list(selected_import_ids)
        if selected_import_ids is not None
        else list(experiment.get("selected_import_ids") or [])
    )
    metric_name = metric if metric is not None else experiment.get("selected_metric")
    applied_filters = filters if filters is not None else experiment.get("selected_filters") or {}
    links = identity_links if identity_links is not None else list((events_doc or {}).get("identity_links") or [])
    survey_rows = surveys if surveys is not None else list((events_doc or {}).get("surveys") or [])
    business_window = experiment.get("business_window") if isinstance(experiment.get("business_window"), dict) else None
    explicit_as_of = as_of or (business_window or {}).get("as_of")
    resolved_as_of = explicit_as_of

    if not imports:
        result = _empty_result(resolved_as_of)
        result["measurement_status"] = "not_measured"
        result["limitations"] = [
            "没有业务导出，这一阶段可以先完成内容和问题记录。业务结果未测。",
            "下一步是导入一段完整观察窗的业务记录，再判断来源和收款。",
            VIEW_WARNING,
        ]
        return result

    selected_imports = _select_imports(imports, selected_ids)
    known_import_ids = {batch.get("import_id") for batch in imports}
    unresolved_ids = [item for item in selected_ids if item not in known_import_ids]
    if selected_ids and not selected_imports:
        result = _empty_result(resolved_as_of)
        result["measurement_status"] = "not_measured"
        result["comparison"] = {
            "comparable": False,
            "reason": "选定的业务批次不存在，不能当作已测。",
            "selected_import_ids": selected_ids,
            "selected_metric": metric_name,
            "ai_window": None,
            "before": None,
            "after": None,
            "boundary_double_count": False,
            "cohort_maturity": None,
        }
        result["limitations"] = [
            VIEW_WARNING,
            "选定的业务批次不存在，业务结果未测。",
        ]
        return result

    identity, conflicts = _resolve_identity(links)
    rows = _collect_rows(selected_imports, identity, applied_filters)
    if resolved_as_of is None:
        resolved_as_of = _latest_occurred(rows)

    visible_rows = [row for row in rows if not row["event"].get("is_test")
                    and _on_or_before(row["occurred"], _parse_datetime(explicit_as_of))]
    event_counts = _count_events(visible_rows)
    user_funnel = _user_funnel(visible_rows)
    session_funnel = _session_funnel(visible_rows)
    refund_rows = _collect_rows(selected_imports, identity, {k: v for k, v in applied_filters.items() if k != "payment_status"})
    paid_orders, duplicate_skipped = _paid_orders(rows)
    refunds_by_order, unlinked_refunds = _bind_refunds(refund_rows, paid_orders)
    views = _build_views(rows, paid_orders, survey_rows, identity, resolved_as_of, explicit_as_of)
    cashflow = _cashflow(paid_orders, refunds_by_order, unlinked_refunds, business_window, resolved_as_of)
    cohort_net = _cohort_net(paid_orders, refunds_by_order, business_window, resolved_as_of)
    test_or_self_promo = _test_or_self_promo(rows)
    unknown_source_visits = _unknown_source_visits(rows)
    comparison = _comparison(
        experiment,
        selected_imports,
        selected_ids,
        rows,
        paid_orders,
        refunds_by_order,
        metric_name,
        business_window,
        unresolved_ids,
        resolved_as_of,
    )
    measurement_status = _measurement_status(selected_imports, event_counts, rows)
    limitations = _limitations(
        measurement_status,
        user_funnel,
        duplicate_skipped,
        unlinked_refunds,
        comparison,
        experiment,
        rows,
        paid_orders,
    )
    if any(batch.get("coverage") != "complete" for batch in selected_imports):
        limitations.append("数据覆盖尚不完整，以上仅代表已提供的记录。")
    return {
        "schema_version": SCHEMA_VERSION,
        "as_of": resolved_as_of,
        "rule_version": RULE_VERSION,
        "event_counts": event_counts,
        "user_funnel": user_funnel,
        "session_funnel": session_funnel,
        "identity_conflicts": conflicts,
        "views": views,
        "view_warning": VIEW_WARNING,
        "cashflow": cashflow,
        "cohort_net": cohort_net,
        "unlinked_refunds": unlinked_refunds,
        "test_or_self_promo": test_or_self_promo,
        "unknown_source_visits": unknown_source_visits,
        "comparison": comparison,
        "limitations": limitations,
        "measurement_status": measurement_status,
    }


def _empty_result(as_of: Optional[str]) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "as_of": as_of,
        "rule_version": RULE_VERSION,
        "event_counts": _zero_counts(),
        "user_funnel": None,
        "session_funnel": None,
        "identity_conflicts": [],
        "views": _empty_views(),
        "view_warning": VIEW_WARNING,
        "cashflow": {"totals_by_currency": {}, "by_period": [], "movements": []},
        "cohort_net": {"as_of": as_of, "by_currency": {}, "orders": []},
        "unlinked_refunds": [],
        "test_or_self_promo": [],
        "unknown_source_visits": [],
        "comparison": None,
        "limitations": [],
        "measurement_status": "not_measured",
    }


def _zero_counts() -> Dict[str, int]:
    return {name: 0 for name in EVENT_TYPES}


def _empty_views() -> Dict[str, Any]:
    return {
        "first_observable_source": {"by_channel": {}, "totals_by_currency": {}},
        "this_visit_source": {"by_channel": {}, "totals_by_currency": {}},
        "self_report": {"by_channel": {}, "totals_by_currency": {}},
        "page_touch": {"by_page": {}, "totals_by_currency": {}},
        "order_total": {},
        "orders": [],
    }


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _host(url_or_host: Optional[str]) -> str:
    if not url_or_host:
        return ""
    text = str(url_or_host).strip().lower()
    if "://" in text:
        return (urlparse(text).hostname or "").lower().rstrip(".")
    return text.split("/")[0].split(":")[0].rstrip(".")


def _is_google_search(host: str) -> bool:
    if not host:
        return False
    if host == "gemini.google.com":
        return False
    return host == "google.com" or host.endswith(".google.com") or host.startswith("google.")


def _is_ai_referrer(host: str) -> bool:
    return host in AI_REFERRER_HOSTS


def _utm_token(value: Optional[str]) -> str:
    return str(value or "").strip().lower()


def derive_channel(event: Dict[str, Any]) -> Tuple[str, str]:
    raw = event.get("raw_touch") if isinstance(event.get("raw_touch"), dict) else {}
    host = _host(raw.get("referrer_host") or raw.get("referrer_url"))
    if host and _is_google_search(host):
        return "search", "referrer 是 Google，记为搜索，不是 AI"
    if host and _is_ai_referrer(host):
        return "ai", "referrer 是 AI 对话来源"
    utm = _utm_token(raw.get("utm_source"))
    utm_host = _host(utm)
    if utm in {"google", "bing", "baidu"} or (utm_host and _is_google_search(utm_host)):
        return "search", "UTM 来源是搜索引擎"
    if utm in {"chatgpt", "openai", "perplexity", "claude"} or (utm_host and _is_ai_referrer(utm_host)):
        return "ai", "UTM 来源是 AI 对话"
    stored = event.get("source_type")
    if stored in {"ai", "search", "social", "direct", "unknown"}:
        return stored, "沿用记录里的来源类型，不改写原始触点"
    return "unknown", "没有可观察来源"


def _in_half_open(occurred: Optional[datetime], start: Optional[datetime], end: Optional[datetime]) -> bool:
    if occurred is None or start is None or end is None:
        return False
    return start <= occurred < end


def _select_imports(imports: List[Dict[str, Any]], selected_ids: List[str]) -> List[Dict[str, Any]]:
    if not selected_ids:
        return list(imports)
    wanted = set(selected_ids)
    return [batch for batch in imports if batch.get("import_id") in wanted]


def _on_or_before(occurred: Optional[datetime], cutoff: Optional[datetime]) -> bool:
    if occurred is None or cutoff is None:
        return cutoff is None
    return occurred <= cutoff


def _window_covers(batch_window: Any, target: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(batch_window, dict) or not isinstance(target, dict):
        return False
    start = _parse_datetime(batch_window.get("start"))
    end = _parse_datetime(batch_window.get("end"))
    target_start = _parse_datetime(target.get("start"))
    target_end = _parse_datetime(target.get("end"))
    if None in {start, end, target_start, target_end}:
        return False
    return start <= target_start and end >= target_end


def _resolve_identity(links: Iterable[Any]) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
    visitor_to_user: Dict[str, str] = {}
    session_to_user: Dict[str, str] = {}
    conflicts: List[Dict[str, Any]] = []
    for raw in links or []:
        if not isinstance(raw, dict):
            continue
        evidence = str(raw.get("evidence") or "")
        user_id = raw.get("user_id")
        if not user_id:
            continue
        if evidence in FORBIDDEN_LINK_EVIDENCE:
            conflicts.append(
                {
                    "link_id": raw.get("link_id"),
                    "reason": "拒绝按 IP、同页或相近时间猜同一个人",
                    "evidence": evidence,
                    "incoming_user_id": user_id,
                    "action": "ignored",
                }
            )
            continue
        for kind, key, mapping in (
            ("visitor_id", raw.get("visitor_id"), visitor_to_user),
            ("session_id", raw.get("session_id"), session_to_user),
        ):
            if not key:
                continue
            existing = mapping.get(key)
            if existing and existing != user_id:
                conflicts.append(
                    {
                        "link_id": raw.get("link_id"),
                        kind: key,
                        "existing_user_id": existing,
                        "incoming_user_id": user_id,
                        "evidence": evidence,
                        "action": "kept_existing",
                    }
                )
                continue
            mapping[key] = user_id
    return {"visitor": visitor_to_user, "session": session_to_user}, conflicts


def _resolved_user(event: Dict[str, Any], identity: Dict[str, Dict[str, str]]) -> Optional[str]:
    if event.get("user_id"):
        return str(event["user_id"])
    session_id = event.get("session_id")
    if session_id and session_id in identity.get("session", {}):
        return identity["session"][session_id]
    visitor_id = event.get("visitor_id")
    if visitor_id and visitor_id in identity.get("visitor", {}):
        return identity["visitor"][visitor_id]
    return None


def _passes_filters(event: Dict[str, Any], filters: Dict[str, Any], channel: str) -> bool:
    if not filters:
        return True
    if filters.get("exclude_test") and event.get("is_test"):
        return False
    if filters.get("exclude_self_promo") and event.get("is_self_promo"):
        return False
    if filters.get("currency") and event.get("currency") not in {None, filters["currency"]}:
        return False
    if filters.get("source_type") and channel != filters["source_type"]:
        return False
    if filters.get("payment_status") and event.get("payment_status") not in {None, filters["payment_status"]}:
        return False
    return True


def _collect_rows(
    imports: List[Dict[str, Any]],
    identity: Dict[str, Dict[str, str]],
    filters: Dict[str, Any],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for batch in imports:
        for event in batch.get("events") or []:
            if not isinstance(event, dict):
                continue
            channel, reason = derive_channel(event)
            if not _passes_filters(event, filters, channel):
                continue
            rows.append(
                {
                    "event": event,
                    "import_id": batch.get("import_id"),
                    "import_source": batch.get("source"),
                    "coverage": batch.get("coverage"),
                    "channel": channel,
                    "channel_reason": reason,
                    "user_id": _resolved_user(event, identity),
                    "occurred": _parse_datetime(event.get("occurred_at")),
                    "natural_ai": channel == "ai" and not event.get("is_test") and not event.get("is_self_promo"),
                }
            )
    rows.sort(key=lambda item: item["occurred"] or datetime.min.replace(tzinfo=timezone.utc))
    return rows


def _latest_occurred(rows: List[Dict[str, Any]]) -> Optional[str]:
    latest = None
    for row in rows:
        occurred = row["occurred"]
        if occurred is None:
            continue
        if latest is None or occurred > latest:
            latest = occurred
    if latest is None:
        return None
    return latest.isoformat().replace("+00:00", "Z")


def _count_events(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = _zero_counts()
    for row in rows:
        event = row["event"]
        name = event.get("type")
        if name in counts:
            counts[name] += 1
        if event.get("first_success_call") and name != "first_success_call":
            counts["first_success_call"] += 1
    return counts


def _rate(numerator: int, denominator: int) -> Optional[Dict[str, Any]]:
    if denominator <= 0:
        return None
    return {
        "numerator": numerator,
        "denominator": denominator,
        "text": "{}/{}".format(numerator, denominator),
    }


def _user_funnel(rows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    users = {row["user_id"] for row in rows if row["user_id"]}
    if not users:
        return None
    visited = {row["user_id"] for row in rows if row["user_id"] and row["event"].get("type") == "visit"}
    signed_up = {row["user_id"] for row in rows if row["user_id"] and row["event"].get("type") == "signup"}
    paid = {
        row["user_id"]
        for row in rows
        if row["user_id"] and _is_paid_purchase(row["event"])
    }
    linked_signups = signed_up & visited
    return {
        "users": len(users),
        "visited": len(visited),
        "signed_up": len(signed_up),
        "paid": len(paid),
        "pay_rate": _rate(len(paid), len(users)),
        "signup_rate": _rate(len(linked_signups), len(visited)) if visited else None,
    }


def _session_funnel(rows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    sessions = {row["event"].get("session_id") for row in rows if row["event"].get("session_id")}
    if not sessions:
        return None
    visited = {row["event"]["session_id"] for row in rows if row["event"].get("session_id") and row["event"].get("type") == "visit"}
    signed_up = {row["event"]["session_id"] for row in rows if row["event"].get("session_id") and row["event"].get("type") == "signup"}
    paid = {row["event"]["session_id"] for row in rows if row["event"].get("session_id") and _is_paid_purchase(row["event"])}
    return {
        "sessions": len(sessions),
        "visited": len(visited),
        "signed_up": len(signed_up),
        "paid": len(paid),
        "pay_rate": _rate(len(paid), len(sessions)),
    }


def _is_paid_purchase(event: Dict[str, Any]) -> bool:
    if event.get("type") != "purchase":
        return False
    if event.get("is_test") or event.get("is_topup"):
        return False
    if event.get("payment_status") in NOT_PAID_STATUSES:
        return False
    if event.get("amount_minor") is None or not event.get("currency"):
        return False
    return True


def _money(amount_minor: int, currency: str) -> Dict[str, Any]:
    if currency in ZERO_DECIMAL_CURRENCIES:
        major = str(int(amount_minor))
    else:
        major = "{:.2f}".format(amount_minor / 100.0)
    return {
        "amount_minor": amount_minor,
        "amount_major": major,
        "currency": currency,
        "currency_label": CURRENCY_LABELS.get(currency, currency),
    }


def _add_money(bucket: Dict[str, Dict[str, Any]], currency: str, amount_minor: int) -> None:
    current = bucket.get(currency)
    total = amount_minor if current is None else int(current["amount_minor"]) + amount_minor
    bucket[currency] = _money(total, currency)


def _order_key(event: Dict[str, Any], import_source: Any) -> Tuple[str, str]:
    del import_source
    if event.get("order_id"):
        return ("order", str(event["order_id"]))
    return ("external", str(event.get("external_id") or ""))


def _paid_orders(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    kept: Dict[Tuple[str, str], Dict[str, Any]] = {}
    skipped: List[Dict[str, Any]] = []
    for row in rows:
        event = row["event"]
        if not _is_paid_purchase(event):
            continue
        key = _order_key(event, row["import_source"])
        if key in kept:
            skipped.append(
                {
                    "order_id": event.get("order_id"),
                    "external_id": event.get("external_id"),
                    "import_id": row["import_id"],
                    "reason": "同一订单跨导出只计一次",
                }
            )
            continue
        kept[key] = {
            "key": key,
            "order_id": event.get("order_id"),
            "external_id": event.get("external_id"),
            "import_id": row["import_id"],
            "user_id": row["user_id"],
            "session_id": event.get("session_id"),
            "visitor_id": event.get("visitor_id"),
            "occurred": row["occurred"],
            "occurred_at": event.get("occurred_at"),
            "amount_minor": int(event["amount_minor"]),
            "currency": event["currency"],
            "channel": row["channel"],
            "natural_ai": row["natural_ai"],
            "page_url": event.get("page_url"),
            "purchase_kind": event.get("purchase_kind"),
            "source_type_recorded": event.get("source_type"),
        }
    return list(kept.values()), skipped


def _refund_identity(event: Dict[str, Any]) -> Tuple[str, str]:
    if event.get("refund_id"):
        return ("refund", str(event["refund_id"]))
    if event.get("external_id"):
        return ("refund", str(event["external_id"]))
    return (
        "refund",
        "|".join(
            [
                str(event.get("order_id") or ""),
                str(event.get("occurred_at") or ""),
                str(event.get("amount_minor") or ""),
            ]
        ),
    )


def _is_effective_refund(event: Dict[str, Any]) -> bool:
    if event.get("type") != "refund":
        return False
    if event.get("is_test") or event.get("is_topup"):
        return False
    if event.get("payment_status") in NOT_PAID_STATUSES:
        return False
    if event.get("amount_minor") is None or not event.get("currency"):
        return False
    return True


def _bind_refunds(
    rows: List[Dict[str, Any]],
    paid_orders: List[Dict[str, Any]],
) -> Tuple[Dict[Tuple[str, str], List[Dict[str, Any]]], List[Dict[str, Any]]]:
    by_order_id = {order["order_id"]: order for order in paid_orders if order.get("order_id")}
    by_key = {order["key"]: order for order in paid_orders}
    bound: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    unlinked: List[Dict[str, Any]] = []
    seen_refunds: set[Tuple[str, str]] = set()
    for row in rows:
        event = row["event"]
        if not _is_effective_refund(event):
            continue
        refund_key = _refund_identity(event)
        if refund_key in seen_refunds:
            continue
        seen_refunds.add(refund_key)
        refund = {
            "external_id": event.get("external_id"),
            "order_id": event.get("order_id"),
            "occurred": row["occurred"],
            "occurred_at": event.get("occurred_at"),
            "amount_minor": int(event["amount_minor"]),
            "currency": event["currency"],
            "import_id": row["import_id"],
            "channel": None,
        }
        order = None
        if event.get("order_id") and event["order_id"] in by_order_id:
            order = by_order_id[event["order_id"]]
        else:
            key = _order_key(event, row["import_source"])
            order = by_key.get(key)
        if order is None:
            unlinked.append(refund)
            continue
        refund["channel"] = order["channel"]
        refund["source_type_recorded"] = order["source_type_recorded"]
        bound.setdefault(order["key"], []).append(refund)
    return bound, unlinked


def _parse_respondent_ref(ref: str) -> Tuple[Optional[str], Optional[str]]:
    text = str(ref or "").strip()
    if not text:
        return None, None
    if text.startswith("user:"):
        return "user", text[5:]
    if text.startswith("visitor:"):
        return "visitor", text[8:]
    if text.startswith("session:"):
        return "session", text[8:]
    return None, text


def _survey_for_user(
    surveys: List[Any],
    user_id: Optional[str],
    visitor_id: Optional[str],
    session_id: Optional[str],
    identity: Dict[str, Dict[str, str]],
    as_of: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    visitor_to_user = identity.get("visitor", {})
    session_to_user = identity.get("session", {})
    as_of_dt = _parse_datetime(as_of)
    for raw in surveys or []:
        if not isinstance(raw, dict):
            continue
        asked = _parse_datetime(raw.get("asked_at"))
        if as_of_dt is not None and asked is not None and asked > as_of_dt:
            continue
        kind, value = _parse_respondent_ref(str(raw.get("respondent_ref") or ""))
        if not value:
            continue
        if kind == "user" and user_id and value == user_id:
            return raw
        if kind == "visitor":
            if visitor_id and value == visitor_id:
                return raw
            if user_id and visitor_to_user.get(value) == user_id:
                return raw
        if kind == "session":
            if session_id and value == session_id:
                return raw
            if user_id and session_to_user.get(value) == user_id:
                return raw
        if kind is None:
            if user_id and value == user_id:
                return raw
    return None


def _survey_channel(answer: Any) -> Optional[str]:
    if not isinstance(answer, dict):
        return None
    kind = answer.get("answer_kind")
    if kind in {"skip", "do_not_remember"}:
        return None
    if kind in {"ai", "search", "social", "direct"}:
        return kind
    if kind == "other":
        return "unknown"
    return None


def _timeline_for(rows: List[Dict[str, Any]], order: Dict[str, Any]) -> List[Dict[str, Any]]:
    matched = []
    cutoff = order.get("occurred")
    for row in rows:
        if cutoff is not None and not _on_or_before(row["occurred"], cutoff):
            continue
        event = row["event"]
        if order.get("user_id") and row["user_id"] == order["user_id"]:
            matched.append(row)
            continue
        if order.get("session_id") and event.get("session_id") == order["session_id"]:
            matched.append(row)
            continue
        if order.get("visitor_id") and event.get("visitor_id") == order["visitor_id"]:
            matched.append(row)
    return matched


def _usable_channel(channel: Optional[str], natural_ai: bool) -> Optional[str]:
    if not channel or channel == "unknown":
        return None
    if channel == "ai" and not natural_ai:
        return None
    return channel


def _first_observable_channel(rows: List[Dict[str, Any]], order: Dict[str, Any]) -> Optional[str]:
    for row in _timeline_for(rows, order):
        if row["event"].get("is_test") or row["event"].get("is_self_promo"):
            continue
        usable = _usable_channel(row["channel"], row["natural_ai"])
        if usable:
            return usable
    return _usable_channel(order["channel"], bool(order.get("natural_ai")))


def _this_visit_channel(rows: List[Dict[str, Any]], order: Dict[str, Any]) -> Optional[str]:
    prior = [
        row
        for row in _timeline_for(rows, order)
        if row["occurred"] is None or order["occurred"] is None or row["occurred"] <= order["occurred"]
    ]
    if order.get("session_id"):
        session_rows = [row for row in prior if row["event"].get("session_id") == order["session_id"]]
        if session_rows:
            prior = session_rows
    for row in reversed(prior):
        if row["event"].get("type") == "visit" and not row["event"].get("is_test") and not row["event"].get("is_self_promo"):
            usable = _usable_channel(row["channel"], row["natural_ai"])
            if usable:
                return usable
    return _usable_channel(order["channel"], bool(order.get("natural_ai")))


def _page_touch(rows: List[Dict[str, Any]], order: Dict[str, Any]) -> Optional[str]:
    if order.get("page_url"):
        return order["page_url"]
    for row in reversed(_timeline_for(rows, order)):
        if row["event"].get("page_url"):
            return row["event"]["page_url"]
    return None


def _build_views(
    rows: List[Dict[str, Any]],
    paid_orders: List[Dict[str, Any]],
    surveys: List[Any],
    identity: Dict[str, Dict[str, str]],
    as_of: Optional[str] = None,
    survey_as_of: Optional[str] = None,
) -> Dict[str, Any]:
    as_of_dt = _parse_datetime(as_of)
    views = _empty_views()
    for order in paid_orders:
        if not _on_or_before(order.get("occurred"), as_of_dt) and as_of_dt is not None:
            continue
        money = _money(order["amount_minor"], order["currency"])
        _add_money(views["order_total"], order["currency"], order["amount_minor"])
        first_channel = _first_observable_channel(rows, order)
        if first_channel == "ai":
            order["natural_ai"] = True
        if first_channel:
            channel_bucket = views["first_observable_source"]["by_channel"].setdefault(first_channel, {})
            _add_money(channel_bucket, order["currency"], order["amount_minor"])
            _add_money(views["first_observable_source"]["totals_by_currency"], order["currency"], order["amount_minor"])
        this_channel = _this_visit_channel(rows, order)
        if this_channel:
            channel_bucket = views["this_visit_source"]["by_channel"].setdefault(this_channel, {})
            _add_money(channel_bucket, order["currency"], order["amount_minor"])
            _add_money(views["this_visit_source"]["totals_by_currency"], order["currency"], order["amount_minor"])
        survey = _survey_for_user(surveys, order.get("user_id"), order.get("visitor_id"), order.get("session_id"), identity, survey_as_of)
        self_channel = _survey_channel((survey or {}).get("first_awareness"))
        if self_channel:
            channel_bucket = views["self_report"]["by_channel"].setdefault(self_channel, {})
            _add_money(channel_bucket, order["currency"], order["amount_minor"])
            _add_money(views["self_report"]["totals_by_currency"], order["currency"], order["amount_minor"])
        page = _page_touch(rows, order)
        if page:
            page_bucket = views["page_touch"]["by_page"].setdefault(page, {})
            _add_money(page_bucket, order["currency"], order["amount_minor"])
            _add_money(views["page_touch"]["totals_by_currency"], order["currency"], order["amount_minor"])
        order["money"] = money
        order["view_channels"] = {
            "first_observable_source": first_channel,
            "this_visit_source": this_channel,
            "self_report": self_channel,
            "page_touch": page,
        }
        views["orders"].append({
            "order_id": order.get("order_id"), "external_id": order["external_id"],
            "import_id": order["import_id"], "occurred_at": order["occurred_at"],
            "money": money, "views": dict(order["view_channels"]),
        })
    return views


def _cashflow(
    paid_orders: List[Dict[str, Any]],
    refunds_by_order: Dict[Tuple[str, str], List[Dict[str, Any]]],
    unlinked_refunds: List[Dict[str, Any]],
    business_window: Optional[Dict[str, Any]],
    as_of: Optional[str],
) -> Dict[str, Any]:
    as_of_dt = _parse_datetime(as_of)
    movements: List[Dict[str, Any]] = []
    totals: Dict[str, Dict[str, Any]] = {}
    for order in paid_orders:
        if as_of_dt is not None and not _on_or_before(order.get("occurred"), as_of_dt):
            continue
        movements.append(
            {
                "kind": "purchase",
                "order_id": order.get("order_id"),
                "occurred_at": order.get("occurred_at"),
                "amount_minor": order["amount_minor"],
                "currency": order["currency"],
                "channel": order["channel"],
            }
        )
        _add_money(totals, order["currency"], order["amount_minor"])
        for refund in refunds_by_order.get(order["key"], []):
            if as_of_dt is not None and not _on_or_before(refund.get("occurred"), as_of_dt):
                continue
            movements.append(
                {
                    "kind": "refund",
                    "order_id": refund.get("order_id"),
                    "occurred_at": refund.get("occurred_at"),
                    "amount_minor": -int(refund["amount_minor"]),
                    "currency": refund["currency"],
                    "channel": refund.get("channel") or order["channel"],
                }
            )
            _add_money(totals, refund["currency"], -int(refund["amount_minor"]))
    for refund in unlinked_refunds:
        if as_of_dt is not None and not _on_or_before(refund.get("occurred"), as_of_dt):
            continue
        movements.append(
            {
                "kind": "refund",
                "order_id": refund.get("order_id"),
                "occurred_at": refund.get("occurred_at"),
                "amount_minor": -int(refund["amount_minor"]),
                "currency": refund["currency"],
                "channel": None,
                "unlinked": True,
            }
        )
        _add_money(totals, refund["currency"], -int(refund["amount_minor"]))

    periods: List[Dict[str, Any]] = []
    if isinstance(business_window, dict):
        for label in ("before", "after"):
            window = business_window.get(label) or {}
            start = _parse_datetime(window.get("start"))
            end = _parse_datetime(window.get("end"))
            period_totals: Dict[str, Dict[str, Any]] = {}
            for item in movements:
                occurred = _parse_datetime(item.get("occurred_at"))
                if _in_half_open(occurred, start, end):
                    _add_money(period_totals, item["currency"], int(item["amount_minor"]))
            periods.append(
                {
                    "label": label,
                    "start": window.get("start"),
                    "end": window.get("end"),
                    "by_currency": period_totals,
                }
            )
        before_end = _parse_datetime((business_window.get("before") or {}).get("end"))
        after_start = _parse_datetime((business_window.get("after") or {}).get("start"))
        after_end = _parse_datetime((business_window.get("after") or {}).get("end"))
        outside_start = after_end
        if before_end and after_start and after_end:
            outside_totals: Dict[str, Dict[str, Any]] = {}
            for item in movements:
                occurred = _parse_datetime(item.get("occurred_at"))
                if occurred is None:
                    continue
                in_before = _in_half_open(occurred, _parse_datetime((business_window.get("before") or {}).get("start")), before_end)
                in_after = _in_half_open(occurred, after_start, after_end)
                if not in_before and not in_after:
                    _add_money(outside_totals, item["currency"], int(item["amount_minor"]))
            if outside_totals:
                periods.append(
                    {
                        "label": "outside",
                        "start": after_end.isoformat().replace("+00:00", "Z") if after_end else None,
                        "end": None,
                        "by_currency": outside_totals,
                    }
                )
        del outside_start
    return {"totals_by_currency": totals, "by_period": periods, "movements": movements}


def _cohort_net(
    paid_orders: List[Dict[str, Any]],
    refunds_by_order: Dict[Tuple[str, str], List[Dict[str, Any]]],
    business_window: Optional[Dict[str, Any]],
    as_of: Optional[str],
) -> Dict[str, Any]:
    as_of_dt = _parse_datetime(as_of)
    cohort_start = None
    cohort_end = None
    if isinstance(business_window, dict) and isinstance(business_window.get("before"), dict):
        cohort_start = _parse_datetime(business_window["before"].get("start"))
        cohort_end = _parse_datetime(business_window["before"].get("end"))
    orders_out: List[Dict[str, Any]] = []
    totals: Dict[str, Dict[str, Any]] = {}
    in_before = [
        order
        for order in paid_orders
        if cohort_start and cohort_end and _in_half_open(order["occurred"], cohort_start, cohort_end)
    ]
    if cohort_start and cohort_end:
        chosen = in_before
    else:
        chosen = [order for order in paid_orders if as_of_dt is None or _on_or_before(order.get("occurred"), as_of_dt)]
    for order in chosen:
        if as_of_dt is not None and not _on_or_before(order.get("occurred"), as_of_dt):
            continue
        refunded = 0
        source = order["channel"]
        recorded_source = order.get("source_type_recorded")
        for refund in refunds_by_order.get(order["key"], []):
            if as_of_dt is None or refund["occurred"] is None or refund["occurred"] <= as_of_dt:
                refunded += int(refund["amount_minor"])
                if refund.get("channel"):
                    source = refund["channel"]
        net = int(order["amount_minor"]) - refunded
        orders_out.append(
            {
                "order_id": order.get("order_id"),
                "paid_minor": order["amount_minor"],
                "refunded_minor": refunded,
                "net_minor": net,
                "currency": order["currency"],
                "channel": source,
                "original_channel": order["channel"],
                "recorded_source_type": recorded_source,
                "source_unchanged": source == order["channel"],
                "money": _money(net, order["currency"]),
            }
        )
        _add_money(totals, order["currency"], net)
    return {"as_of": as_of, "by_currency": totals, "orders": orders_out}


def _test_or_self_promo(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items = []
    for row in rows:
        event = row["event"]
        if event.get("is_test") or event.get("is_self_promo"):
            items.append(
                {
                    "external_id": event.get("external_id"),
                    "type": event.get("type"),
                    "is_test": bool(event.get("is_test")),
                    "is_self_promo": bool(event.get("is_self_promo")),
                    "recorded_source_type": event.get("source_type"),
                    "derived_channel": row["channel"],
                    "natural_ai": False,
                }
            )
    return items


def _unknown_source_visits(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items = []
    for row in rows:
        event = row["event"]
        if event.get("type") != "visit":
            continue
        if row["channel"] == "unknown" and not event.get("is_test") and not event.get("is_self_promo"):
            items.append(
                {
                    "external_id": event.get("external_id"),
                    "page_url": event.get("page_url"),
                    "derived_channel": "unknown",
                    "natural_ai": False,
                }
            )
    return items


def _window_days(window: Optional[Dict[str, Any]]) -> Optional[int]:
    if not isinstance(window, dict):
        return None
    start = _parse_datetime(window.get("start"))
    end = _parse_datetime(window.get("end"))
    if start is None or end is None or end <= start:
        return None
    return int((end - start).total_seconds() // 86400)


def _side_summary(
    label: str,
    window: Dict[str, Any],
    rows: List[Dict[str, Any]],
    paid_orders: List[Dict[str, Any]],
    refunds_by_order: Dict[Tuple[str, str], List[Dict[str, Any]]],
    metric_name: Optional[str],
    as_of: Optional[str] = None,
) -> Dict[str, Any]:
    start = _parse_datetime(window.get("start"))
    end = _parse_datetime(window.get("end"))
    as_of_dt = _parse_datetime(as_of)
    in_rows = [
        row
        for row in rows
        if _in_half_open(row["occurred"], start, end) and (as_of_dt is None or _on_or_before(row["occurred"], as_of_dt))
    ]
    in_orders = [
        order
        for order in paid_orders
        if _in_half_open(order["occurred"], start, end) and (as_of_dt is None or _on_or_before(order["occurred"], as_of_dt))
    ]
    counts = _count_events(in_rows)
    money: Dict[str, Dict[str, Any]] = {}
    for order in in_orders:
        _add_money(money, order["currency"], order["amount_minor"])
        if metric_name == "paid_amount":
            continue
    return {
        "label": label,
        "window": window,
        "event_counts": counts,
        "paid_orders": len(in_orders),
        "by_currency": money,
        "import_ids": sorted({row["import_id"] for row in in_rows if row.get("import_id")}),
    }


def _comparison(
    experiment: Dict[str, Any],
    selected_imports: List[Dict[str, Any]],
    selected_ids: List[str],
    rows: List[Dict[str, Any]],
    paid_orders: List[Dict[str, Any]],
    refunds_by_order: Dict[Tuple[str, str], List[Dict[str, Any]]],
    metric_name: Optional[str],
    business_window: Optional[Dict[str, Any]],
    unresolved_ids: Optional[List[str]] = None,
    as_of: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    ai_window = None
    baseline = experiment.get("baseline")
    if isinstance(baseline, dict) and isinstance(baseline.get("captured_window"), dict):
        ai_window = baseline["captured_window"]
    if not selected_ids and not business_window:
        return None
    if business_window and business_window.get("before") and business_window.get("after"):
        cutoff = as_of or business_window.get("as_of")
        before = _side_summary("before", business_window["before"], rows, paid_orders, refunds_by_order, metric_name, cutoff)
        after = _side_summary("after", business_window["after"], rows, paid_orders, refunds_by_order, metric_name, cutoff)
        before_end = _parse_datetime(business_window["before"].get("end"))
        after_start = _parse_datetime(business_window["after"].get("start"))
        double = False
        if before_end and after_start:
            for row in rows:
                occurred = row["occurred"]
                if occurred is None:
                    continue
                in_before = _in_half_open(
                    occurred,
                    _parse_datetime(business_window["before"].get("start")),
                    before_end,
                )
                in_after = _in_half_open(
                    occurred,
                    after_start,
                    _parse_datetime(business_window["after"].get("end")),
                )
                if in_before and in_after:
                    double = True
                    break
        lookback = experiment.get("first_paid_lookback") or {}
        maturity = experiment.get("cohort_maturity") or {}
        required_days = maturity.get("required_days")
        observed_days = maturity.get("observed_days")
        if required_days is None and isinstance(lookback, dict):
            required_days = lookback.get("days")
        if observed_days is None:
            observed_days = _window_days(business_window.get("after"))
        mature = None
        explanation = None
        if required_days is not None and observed_days is not None:
            mature = int(observed_days) >= int(required_days)
            if not mature:
                explanation = "改后只观察了 {} 天，首付回看需要 {} 天，不能和已观察满期的用户按同一标准比较。".format(
                    observed_days, required_days
                )
        coverage_ok = True
        reason = None
        for batch in selected_imports:
            if selected_ids and batch.get("import_id") not in selected_ids:
                continue
            if batch.get("coverage") != "complete":
                coverage_ok = False
                reason = "所选业务批次不是完整覆盖，不能当作等长对照。"
        before_covered = any(_window_covers(batch.get("window"), business_window.get("before")) for batch in selected_imports)
        after_covered = any(_window_covers(batch.get("window"), business_window.get("after")) for batch in selected_imports)
        if not before_covered or not after_covered:
            coverage_ok = False
            reason = reason or "改前或改后观察窗没有对应的完整业务批次，不能对照。"
        mature_ok = True
        if metric_name == "user_pay_rate" and mature is False:
            mature_ok = False
            reason = reason or explanation or "观察期未满，用户付费率不能对照。"
        if unresolved_ids:
            coverage_ok = False
            reason = reason or "有选定的业务批次无法对应，不能对照。"
        as_of_dt = _parse_datetime(cutoff)
        after_end = _parse_datetime((business_window.get("after") or {}).get("end"))
        if as_of_dt is not None and after_end is not None and as_of_dt < after_end:
            coverage_ok = False
            reason = reason or "改后观察窗尚未到声明的结束时间，不能当作完整等长对照。"
        if metric_name == "paid_amount":
            before_days = _window_days(business_window.get("before"))
            after_days = _window_days(business_window.get("after"))
            if before_days is not None and after_days is not None and before_days != after_days:
                coverage_ok = False
                reason = reason or "未归一化的付款金额只能比较等长窗口。"
        return {
            "comparable": bool(coverage_ok and not double and mature_ok),
            "reason": reason,
            "selected_import_ids": selected_ids,
            "selected_metric": metric_name,
            "ai_window": ai_window,
            "business_window": {
                "before": business_window.get("before"),
                "after": business_window.get("after"),
                "timezone": business_window.get("timezone"),
                "as_of": business_window.get("as_of"),
            },
            "before": before,
            "after": after,
            "boundary_double_count": double,
            "cohort_maturity": {
                "mature": mature,
                "required_days": required_days,
                "observed_days": observed_days,
                "explanation": explanation,
            },
        }
    return {
        "comparable": False,
        "reason": "已显式选择业务批次，但还没有独立的业务前后观察窗。",
        "selected_import_ids": selected_ids,
        "selected_metric": metric_name,
        "ai_window": ai_window,
        "before": None,
        "after": None,
        "boundary_double_count": False,
        "cohort_maturity": None,
    }


def _measurement_status(
    imports: List[Dict[str, Any]],
    event_counts: Dict[str, int],
    rows: List[Dict[str, Any]],
) -> str:
    if not imports:
        return "not_measured"
    coverages = [batch.get("coverage") for batch in imports]
    has_real = any(
        not row["event"].get("is_test")
        for row in rows
    )
    if all(item == "complete" for item in coverages) and not has_real:
        return "measured_zero"
    if all(item == "complete" for item in coverages) and sum(event_counts.values()) == 0:
        return "measured_zero"
    return "measured"


def _limitations(
    measurement_status: str,
    user_funnel: Optional[Dict[str, Any]],
    duplicate_skipped: List[Dict[str, Any]],
    unlinked_refunds: List[Dict[str, Any]],
    comparison: Optional[Dict[str, Any]],
    experiment: Dict[str, Any],
    rows: List[Dict[str, Any]],
    paid_orders: List[Dict[str, Any]],
) -> List[str]:
    lines = [VIEW_WARNING]
    if measurement_status == "not_measured":
        lines.append("没有业务导出，业务结果未测。")
        lines.append("下一步是导入完整观察窗的业务记录。")
    elif measurement_status == "measured_zero":
        lines.append("完整窗口里成交是 0，这是实测零，不是未测。")
        lines.append("下一步可继续处理已发现的内容和问题缺口。")
    if user_funnel is None:
        lines.append("没有身份标识时，只报事件次数，不计算用户比率。")
    if duplicate_skipped:
        lines.append("同一订单在分析与支付导出里只计一次。")
    if unlinked_refunds:
        lines.append("有 {} 笔退款无法关联到原订单，已单独列出。".format(len(unlinked_refunds)))
    if any(row["event"].get("is_topup") for row in rows):
        lines.append("充值没有当成确认收入。")
    if any(order.get("natural_ai") for order in paid_orders):
        lines.append("来源关联金额可以报告。本项目没有 AI 回答样本时，AI 表现仍未测。")
    if comparison is None:
        lines.append("尚未指定前后对比的数据与时间范围。")
    elif comparison.get("boundary_double_count"):
        lines.append("窗口边界出现了重复计入，对照不可直接使用。")
    elif comparison.get("cohort_maturity") and comparison["cohort_maturity"].get("explanation"):
        lines.append(comparison["cohort_maturity"]["explanation"])
    if comparison and comparison.get("ai_window") and comparison.get("business_window"):
        lines.append("AI 采样窗和业务前后观察窗分开计算，不拿采样时长当业务窗。")
    # unique preserve order
    seen = set()
    unique = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            unique.append(line)
    return unique
