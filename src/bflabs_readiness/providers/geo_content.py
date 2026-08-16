"""Evidence-bounded content production for seven explicit modes."""

from __future__ import annotations

from typing import Any, Dict, List

from ..evidence import stable_claim_id
from ..quality import evaluate_content


MODES = ["title", "explainer", "comparison", "ranking", "page-blueprint", "refine", "article-friendly"]


def _title(brief: Dict[str, Any]) -> str:
    if brief["language"] == "zh-CN":
        suffix = {
            "title": "标题方案",
            "explainer": "是什么、怎么用与限制",
            "comparison": "对比与选择指南",
            "ranking": "榜单与方法说明",
            "page-blueprint": "价格、计费与接入答案页",
            "refine": "内容优化稿",
            "article-friendly": "AI 友好结构化文章",
        }[brief["mode"]]
        return "{}：{}".format(brief["subject"], suffix)
    suffix = {
        "title": "Title options",
        "explainer": "What it is, how it works, and limitations",
        "comparison": "Comparison and selection guide",
        "ranking": "Ranking with disclosed method",
        "page-blueprint": "Pricing, billing, and integration answer page",
        "refine": "Refined content",
        "article-friendly": "AI-friendly structured article",
    }[brief["mode"]]
    return "{}: {}".format(brief["subject"], suffix)


def _section_plan(brief: Dict[str, Any], claim_ids: List[str]) -> List[Dict[str, Any]]:
    zh = brief["language"] == "zh-CN"
    headings = {
        "title": ["标题候选" if zh else "Title options"],
        "explainer": ["简明解释" if zh else "Plain explanation", "事实与限制" if zh else "Facts and limitations"],
        "comparison": ["对比范围" if zh else "Comparison scope", "对称维度" if zh else "Symmetric dimensions", "如何选择" if zh else "How to choose"],
        "ranking": ["方法披露" if zh else "Method disclosure", "结果" if zh else "Results", "限制" if zh else "Limitations"],
        "page-blueprint": ["直接答案" if zh else "Direct answer", "价格与计费" if zh else "Pricing and billing", "接入方式" if zh else "Integration", "来源与更新时间" if zh else "Sources and freshness"],
        "refine": ["优化稿" if zh else "Refined copy", "事实核对" if zh else "Fact check"],
        "article-friendly": ["摘要" if zh else "Summary", "结构化正文" if zh else "Structured article", "事实与来源" if zh else "Facts and sources"],
    }[brief["mode"]]
    sections = []
    for index, heading in enumerate(headings):
        sections.append(
            {
                "id": "section-{}".format(index + 1),
                "heading": heading,
                "purpose": "Present only claims linked in the evidence units.",
                "claim_ids": claim_ids if index == 0 else [],
            }
        )
    return sections


def _markdown(brief: Dict[str, Any], title: str, sections: List[Dict[str, Any]], facts: List[Dict[str, Any]]) -> str:
    facts_by_id = {stable_claim_id(fact["text"]): fact for fact in facts}
    lines = ["# " + title, ""]
    if brief["mode"] == "ranking" and brief["ranking_method"] is not None:
        method = brief["ranking_method"]
        lines.extend([
            "## " + ("方法披露" if brief["language"] == "zh-CN" else "Method disclosure"),
            "",
            "{}；{}".format(method["title"], method["dataset_scope"]),
            "",
        ])
    for section in sections:
        lines.extend(["## " + section["heading"], ""])
        for claim_id in section["claim_ids"]:
            lines.append("- {} [^{}]".format(facts_by_id[claim_id]["text"], claim_id))
        if not section["claim_ids"]:
            lines.append("- " + ("本节只组织已确认事实，不新增未经支持的结论。" if brief["language"] == "zh-CN" else "This section organizes confirmed facts without adding unsupported conclusions."))
        lines.append("")
    lines.append("---")
    lines.append("")
    for claim_id in sorted(facts_by_id):
        fact = facts_by_id[claim_id]
        lines.append("[^{}]: evidence={} version={}".format(claim_id, ",".join(fact["evidence_ids"]), fact["fact_version"] or "static"))
    return "\n".join(lines) + "\n"


def run_geo_content(brief: Dict[str, Any]) -> Dict[str, Any]:
    facts = brief["facts"]
    claim_ids = [stable_claim_id(fact["text"]) for fact in facts]
    title = _title(brief)
    sections = _section_plan(brief, claim_ids)
    content_spec = {
        "schema_version": "1.0.0",
        "mode": brief["mode"],
        "subject": brief["subject"],
        "title": title,
        "audience": brief["audience"],
        "intent": brief["intent"],
        "document_format": "markdown",
        "sections": sections,
        "claim_ids": claim_ids,
        "discovery_context": brief["discovery_context"],
        "publication_gate": "owner-approval-required",
    }
    evidence_units = {
        "schema_version": "1.0.0",
        "units": [
            {
                "claim_id": stable_claim_id(fact["text"]),
                "text": fact["text"],
                "evidence_ids": fact["evidence_ids"],
                "support_level": fact["support_level"],
                "dynamic_fact": fact["dynamic_fact"],
                "fact_version": fact["fact_version"],
                "evidence_hash": fact["evidence_hash"],
            }
            for fact in facts
        ],
    }
    markdown = _markdown(brief, title, sections, facts)
    ledger = {
        "schema_version": "1.0.0",
        "items": [dict(item) for item in brief["evidence_sources"]],
        "claims": [
            {
                "id": stable_claim_id(fact["text"]),
                "text": fact["text"],
                "evidence_ids": fact["evidence_ids"],
                "support_level": fact["support_level"],
            }
            for fact in facts
        ],
    }
    quality = evaluate_content(brief, content_spec, markdown, ledger)
    return {
        "outputs": {
            "outputs/content-spec.json": (content_spec, "content-spec.schema.json"),
            "outputs/content-evidence-units.json": (evidence_units, "content-evidence-units.schema.json"),
            "outputs/content.md": (markdown, None, "text/markdown; charset=utf-8"),
        },
        "evidence_ledger": ledger,
        "quality_report": quality,
    }
