"""Deterministic bilingual routing to one minimum capability or one exact workflow."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Iterable, List, Optional, Pattern, Sequence, Tuple

from .registry import CapabilityRegistry
from .schemas import validate_instance


PatternGroup = Sequence[Pattern[str]]


def _patterns(*values: str) -> List[Pattern[str]]:
    return [re.compile(value, re.I) for value in values]


FORBIDDEN: PatternGroup = _patterns(
    r"(?:保证|确保).{0,12}(?:排名第一|收录|引用|推荐|收入)",
    r"guarantee.{0,50}(?:rank|index|citation|recommend|revenue|first\s+place)",
    r"(?:批量|一次).{0,10}(?:生成|发布).{0,8}(?:[一二两三四五六七八九十百千万0-9]+篇|内容农场)",
    r"(?:bulk|mass).{0,12}(?:generate|publish).{0,40}(?:articles|content)",
    r"(?:暴露|开放).{0,10}(?:后台|管理员|私有).{0,8}(?:接口|权限)",
    r"expose.{0,20}(?:admin|private).{0,12}(?:api|permission)",
    r"(?:绕过|跳过).{0,8}(?:登录|鉴权|授权)",
    r"bypass.{0,12}(?:login|auth|permission)",
    r"(?:自动|自主).{0,8}(?:付款|支付)",
    r"autonomous.{0,12}(?:payment|purchase)",
)

AMBIGUOUS: PatternGroup = _patterns(
    r"^(?:帮我|给我)?\s*(?:做|搞|优化)?\s*(?:一下)?\s*(?:GEO|SEO|网站)\s*[。.!！]?$",
    r"^(?:help|do|improve)\s+(?:geo|seo|website)\s*[.!]?$",
)

WORKFLOW_PATTERNS: List[Tuple[str, PatternGroup]] = [
    (
        "discover-diagnose",
        _patterns(
            r"(?:先|首先).{0,40}(?:问题|意图|机会).{0,16}(?:发现|挖掘|研究).{0,40}(?:再|然后|之后).{0,30}(?:诊断|审计|检查)",
            r"(?:先|首先).{0,20}(?:发现|挖掘|研究).{0,30}(?:问题|意图|机会).{0,40}(?:再|然后|之后).{0,30}(?:诊断|审计|检查)",
            r"(?:discover|find|research).{0,35}(?:questions|intents|opportunities).{0,30}(?:then|and then|before).{0,30}(?:diagnos(?:e|ing)|audit|assess)",
        ),
    ),
    (
        "discover-content",
        _patterns(
            r"(?:先|首先).{0,40}(?:问题|意图|机会).{0,16}(?:发现|挖掘|研究).{0,40}(?:再|然后|之后).{0,30}(?:内容|页面|文章|蓝图|改写)",
            r"(?:先|首先).{0,20}(?:发现|挖掘|研究).{0,30}(?:问题|意图|机会).{0,40}(?:再|然后|之后).{0,30}(?:内容|页面|文章|蓝图|改写|对比页|价格页)",
            r"(?:discover|find|research).{0,35}(?:questions|intents|opportunities).{0,30}(?:then|and then|before).{0,30}(?:create|write|produce|build|refine).{0,20}(?:content|page|article|blueprint)",
        ),
    ),
]

CAPABILITY_PATTERNS: List[Tuple[str, PatternGroup]] = [
    (
        "webmcp-enable",
        _patterns(
            r"webmcp",
            r"modelcontext.{0,12}(?:tool|工具)",
            r"(?:浏览器|browser).{0,12}(?:agent|智能体).{0,12}(?:工具|tool|调用|办事)",
            r"typed\s+tools.{0,30}browser\s+agent",
            r"(?:启用|实现|接入|验证).{0,12}(?:site\s+)?mcp",
            r"(?:enable|implement|bridge|verify).{0,30}(?:site\s+)?mcp",
        ),
    ),
    (
        "geo-measure",
        _patterns(
            r"(?:导入|聚合|统计|复算).{0,15}(?:样本|观测|回答|引用)",
            r"(?:联网率|引用率|吸收率|品牌出现率|推荐率|价格正确率)",
            r"(?:aggregate|import|measure|recalculate).{0,60}(?:observations|samples|answers|citations)",
        ),
    ),
    (
        "seo-plan",
        _patterns(
            r"(?:搜索控制台|search\s+console|indexnow)",
            r"(?:自然流量|organic\s+traffic).{0,16}(?:下降|恢复|drop|recover)",
            r"(?:网站迁移|site\s+migration).{0,18}(?:seo|索引|收录|redirect|canonical)",
            r"(?:技术\s*seo|technical\s+seo|国际\s*seo|international\s+seo)",
            r"(?:规划|plan).{0,12}(?:网站\s*)?seo|seo.{0,12}(?:规划|plan)",
        ),
    ),
    (
        "geo-discover",
        _patterns(
            r"(?:发现|挖掘|研究|拓展).{0,20}(?:问题|意图|机会|提问词)",
            r"(?:问题|意图|机会|提问词).{0,20}(?:发现|挖掘|研究|地图|清单)",
            r"(?:discover|find|research|expand).{0,24}(?:questions|intents|opportunities|queries)",
            r"(?:question|intent|opportunity|query)\s+(?:map|discovery|research)",
        ),
    ),
    (
        "geo-content",
        _patterns(
            r"(?:生成|写|创建|制作).{0,16}(?:标题|科普|对比页|榜单|页面蓝图|文章)",
            r"(?:内容|文章).{0,10}(?:友好改写|重写|优化润色)",
            r"(?:create|write|produce|build).{0,16}(?:title|explainer|comparison page|ranking|page blueprint|article)",
            r"(?:refine|rewrite).{0,16}(?:content|article)",
        ),
    ),
    (
        "bflabs-agent-readiness",
        _patterns(
            r"(?:可发现|可理解|可操作).{0,20}(?:三轴|报告|准备度)?",
            r"(?:discoverable|understandable|actionable).{0,20}(?:axes|report|readiness)?",
            r"(?:ai|agent|智能体).{0,12}(?:网站|website).{0,12}(?:准备度|readiness)",
        ),
    ),
    (
        "geo-optimize",
        _patterns(
            r"(?:诊断|审计|检查|评估).{0,20}(?:品牌|网站|官网|页面|geo|准备度)",
            r"(?:品牌|网站|官网|页面|geo).{0,20}(?:诊断|审计|检查|评估)",
            r"(?:修复|优化|更新).{0,20}(?:价格页|答案页|llms\.txt|sitemap|schema|公开事实)",
            r"(?:diagnose|audit|assess|check).{0,20}(?:brand|site|website|page|geo|readiness)",
            r"(?:fix|optimize|update).{0,20}(?:pricing page|answer page|llms\.txt|sitemap|schema|public facts)",
        ),
    ),
]


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _matches(text: str, patterns: Iterable[Pattern[str]]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def _selected_capability(registry: CapabilityRegistry, capability_id: str) -> Dict[str, Any]:
    capability = registry.resolve(capability_id)
    return {
        "type": "capability",
        "id": capability.id,
        "status": capability.status,
        "entrypoint": capability.entrypoint,
        "steps": [],
    }


def _decision_for_capability(
    original: str,
    normalized: str,
    registry: CapabilityRegistry,
    capability_id: str,
    explicit: bool = False,
) -> Dict[str, Any]:
    capability = registry.resolve(capability_id)
    active = capability.status in {"active", "deprecated"}
    fallback: Optional[Dict[str, str]] = None
    if not active:
        fallback_id = capability.degrades_to
        if fallback_id in {item.id for item in registry.list_capabilities("active")}:
            fallback = {
                "capability_id": fallback_id,
                "reason": "requested capability is {} and cannot execute".format(capability.status),
            }
    decision = {
        "schema_version": "1.0.0",
        "request_text": original,
        "normalized_text": normalized,
        "kind": "capability",
        "selected": _selected_capability(registry, capability_id),
        "executable": active,
        "reason_code": "explicit-capability" if explicit and active else ("planned-capability" if not active else "minimum-active-capability"),
        "fallback": fallback,
        "required_gates": capability.external_gates if active else [],
    }
    validate_instance(decision, "route-decision.schema.json")
    return decision


def _decision_for_workflow(
    original: str,
    normalized: str,
    registry: CapabilityRegistry,
    workflow_id: str,
) -> Dict[str, Any]:
    workflow = registry.resolve_workflow(workflow_id)
    executable = workflow.status == "active"
    fallback_id = "geo-optimize" if workflow_id == "discover-diagnose" else "geo-optimize"
    decision = {
        "schema_version": "1.0.0",
        "request_text": original,
        "normalized_text": normalized,
        "kind": "workflow",
        "selected": {
            "type": "workflow",
            "id": workflow.id,
            "status": workflow.status,
            "entrypoint": None,
            "steps": workflow.steps,
        },
        "executable": executable,
        "reason_code": "explicit-workflow" if executable else "planned-workflow",
        "fallback": None if executable else {
            "capability_id": fallback_id,
            "reason": "workflow is planned; run the active diagnosis capability without hidden discovery/content execution",
        },
        "required_gates": [],
    }
    validate_instance(decision, "route-decision.schema.json")
    return decision


def _terminal_decision(original: str, normalized: str, rejected: bool) -> Dict[str, Any]:
    decision = {
        "schema_version": "1.0.0",
        "request_text": original,
        "normalized_text": normalized,
        "kind": "rejected" if rejected else "needs_clarification",
        "selected": None,
        "executable": False,
        "reason_code": "forbidden-request" if rejected else "ambiguous-request",
        "fallback": None,
        "required_gates": [],
    }
    validate_instance(decision, "route-decision.schema.json")
    return decision


def route(text: str, registry: Optional[CapabilityRegistry] = None) -> Dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("route text must be a non-empty string")
    registry = registry or CapabilityRegistry()
    original = text.strip()
    normalized = normalize_text(original)

    if _matches(normalized, FORBIDDEN):
        return _terminal_decision(original, normalized, rejected=True)
    if _matches(normalized, AMBIGUOUS):
        return _terminal_decision(original, normalized, rejected=False)

    for workflow_id, patterns in WORKFLOW_PATTERNS:
        if _matches(normalized, patterns):
            return _decision_for_workflow(original, normalized, registry, workflow_id)

    explicit_ids = [capability.id for capability in registry.list_capabilities() if capability.id in normalized.lower()]
    if len(explicit_ids) == 1:
        return _decision_for_capability(original, normalized, registry, explicit_ids[0], explicit=True)
    if len(explicit_ids) > 1:
        return _terminal_decision(original, normalized, rejected=False)

    for capability_id, patterns in CAPABILITY_PATTERNS:
        if _matches(normalized, patterns):
            return _decision_for_capability(original, normalized, registry, capability_id)
    return _terminal_decision(original, normalized, rejected=False)
