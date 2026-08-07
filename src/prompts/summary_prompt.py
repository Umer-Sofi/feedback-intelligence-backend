"""Prompt for the weekly narrative summary (grounded in real feedback)."""

import json
from typing import Optional


def build_summary_messages(
    stats: dict, quotes: list[dict], period: Optional[dict] = None
) -> list[dict]:
    """Build messages for the weekly narrative from stats + quotes."""
    period_line = ""
    if period:
        period_line = (
            f"This report covers feedback for the week starting "
            f"{period['from']}. Do NOT state or infer an end date.\n\n"
        )
    system = (
        "You are an analyst writing a weekly customer-feedback summary for "
        "a product team. "
        + period_line
        + "The total volume and the sentiment breakdown are already shown "
        "to the reader as charts, so do NOT restate totals or per-sentiment "
        "counts. Instead write a concise narrative of 2-4 short paragraphs "
        "that:\n"
        "  - highlights the top recurring themes and any week-over-week "
        "movement,\n"
        "  - calls out notable issues (bugs, pricing, churn signals), with "
        "a real quote where useful,\n"
        "  - ends with 2-3 concrete, prioritized recommendations.\n\n"
        "Ground every claim in the provided data. Do NOT invent numbers or "
        "quotes. Plain prose, no JSON."
    )
    quote_lines = "\n".join(
        f'- ({q.get("category")}/{q.get("sentiment")}) "{q["text"]}"'
        for q in quotes
    )
    user = (
        "Aggregated stats (JSON):\n"
        f"{json.dumps(stats, default=str, indent=2)}\n\n"
        "Representative feedback quotes:\n"
        f"{quote_lines or '(none)'}\n\n"
        "Write the weekly summary now."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
