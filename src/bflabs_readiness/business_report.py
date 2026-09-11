"""Human-readable projection of the shared offline attribution result."""

from typing import Any


def _amounts(bucket: dict) -> str:
    return "、".join(f'{row["amount_major"]} {row["currency_label"]}（{code}）'
                    for code, row in sorted(bucket.items())) or "0"


def render_business_report(report: dict[str, Any]) -> str:
    if report["measurement_status"] == "not_measured":
        return "业务结果未测。可以先完成本阶段报告，取得业务数据后再补充。"
    counts = report["event_counts"]
    lines = [f'访问 {counts["visit"]} 次，注册 {counts["signup"]} 次，付款事件 {counts["purchase"]} 次。',
             f'所选数据的现金净收款：{_amounts(report["cashflow"]["totals_by_currency"])}。']
    if report.get("as_of"):
        lines.append(f'统计截至：{report["as_of"]}。')
    funnel = report.get("user_funnel")
    if funnel:
        for key, label in [("signup_rate", "可关联的访问用户注册率"), ("pay_rate", "已识别用户付费率")]:
            rate = funnel.get(key)
            if rate:
                lines.append(f'{label}：{rate["numerator"]}/{rate["denominator"]} 人。')
    else:
        lines.append("目前无法把访问和付款关联到同一人，仅展示事件次数。")
    views = report["views"]
    labels = {"first_observable_source": "最早记录的来源", "this_visit_source": "本次访问来源",
              "self_report": "用户自报来源", "page_touch": "访问过的页面"}
    channels = {"ai": "AI", "search": "搜索", "social": "社交", "direct": "直接访问", "unknown": "未知"}
    for key, label in labels.items():
        groups = views[key].get("by_channel", views[key].get("by_page", {}))
        if groups:
            lines.append(f'\n{label}关联的实付：')
            lines.extend(f'- {channels.get(name, name)}：{_amounts(amount)}' for name, amount in groups.items())
    if any(views[key].get("totals_by_currency") for key in labels):
        lines.append("\n同一订单可出现在多个来源视角中，各视角金额不能相加；来源关联不代表本轮优化带来的增量。")
    comparison = report.get("comparison")
    if comparison and comparison.get("comparable"):
        lines.append("\n业务前后对比（实付）：")
        for side, label in [("before", "改前"), ("after", "改后")]:
            row = comparison[side]
            lines.append(f'- {label}：{row["paid_orders"]} 笔，{_amounts(row["by_currency"])}。')
    elif comparison:
        lines.append(f'\n暂不能比较前后变化：{comparison.get("reason") or "记录条件不完整"}')
    for note in report.get("limitations", []):
        if note not in {report.get("view_warning")} and note not in lines:
            lines.append(note)
    return "\n".join(lines)
