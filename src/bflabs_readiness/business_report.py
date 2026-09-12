"""Human-readable projection of the shared offline attribution result."""

from typing import Any


def _amounts(bucket: dict) -> str:
    return "、".join(f'{row["amount_major"]} {row["currency_label"]}（{code}）'
                    for code, row in sorted(bucket.items())) or "0"


def render_business_report(report: dict[str, Any]) -> str:
    if report["measurement_status"] == "not_measured":
        note = next((item for item in report.get("limitations", []) if item != report.get("view_warning")), "业务结果未测。")
        return note + " 可以先完成本阶段报告，取得所需记录后再补充。"
    counts = report["event_counts"]
    lines = [f'访问 {counts["visit"]} 次，注册 {counts["signup"]} 次，付款事件 {counts["purchase"]} 次。',
             f'所选数据的现金净收款：{_amounts(report["cashflow"]["totals_by_currency"])}。']
    first_records = report.get("first_success_call_records")
    lines.append(f"导出中明确记录的首次成功调用：{first_records} 条。" if first_records is not None
                 else "首次成功调用：导出覆盖范围未确认，不能记为零。")
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
            lines.append(f'\n{label}关联的收款（未扣退款）：')
            lines.extend(f'- {channels.get(name, name)}：{_amounts(amount)}' for name, amount in groups.items())
    if any(views[key].get("totals_by_currency") for key in labels):
        lines.append("\n同一订单可出现在多个来源视角中，各视角金额不能相加；来源关联不代表本轮优化带来的增量。")
    comparison = report.get("comparison")
    if comparison and comparison.get("comparable"):
        metric = comparison.get("selected_metric")
        count_metrics = {"first_success_call": ("首次成功调用记录", "first_success_call"),
                         "visits": ("访问记录", "visit"), "signups": ("注册记录", "signup")}
        if metric in count_metrics:
            title, key = count_metrics[metric]
            lines.append(f"\n业务前后对比（{title}）：")
            for side, label in [("before", "改前"), ("after", "改后")]:
                lines.append(f'- {label}：{comparison[side]["event_counts"][key]} 条。')
        elif metric == "purchases":
            lines.append("\n业务前后对比（已付款订单）：")
            for side, label in [("before", "改前"), ("after", "改后")]:
                lines.append(f'- {label}：{comparison[side]["paid_orders"]} 笔。')
        elif metric == "user_pay_rate":
            lines.append("\n前后付费率尚无分别核对的用户分母，不以收款金额替代。")
        else:
            lines.append("\n业务前后对比（收款总额，未扣退款）：")
            for side, label in [("before", "改前"), ("after", "改后")]:
                row = comparison[side]
                lines.append(f'- {label}：{row["paid_orders"]} 笔，{_amounts(row["by_currency"])}。')
    elif comparison:
        lines.append(f'\n暂不能比较前后变化：{comparison.get("reason") or "记录条件不完整"}')
    for note in report.get("limitations", []):
        if note not in {report.get("view_warning")} and note not in lines:
            lines.append(note)
    return "\n".join(lines)
