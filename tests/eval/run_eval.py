"""Evaluate the classifier against labeled samples; write ACCURACY.md.

Runs the live classifier over tests/eval/labeled_samples.csv, compares its
predicted category/sentiment to the ground-truth labels, and writes accuracy
metrics to ACCURACY.md.

Run from the backend/ directory:
    python -m tests.eval.run_eval
"""

from collections import defaultdict
from pathlib import Path

import pandas as pd

from src.services.classifier import classify

SAMPLES_PATH = Path("tests/eval/labeled_samples.csv")
OUTPUT_PATH = Path("ACCURACY.md")


def run_eval() -> dict:
    """Classify each labeled sample and compute accuracy metrics."""
    df = pd.read_csv(SAMPLES_PATH)
    total = len(df)
    cat_correct = 0
    sent_correct = 0
    per_cat = defaultdict(lambda: {"total": 0, "correct": 0})

    for _, row in df.iterrows():
        result = classify(str(row["text"]))
        true_cat = str(row["category"])
        predicted_cats = [c.value for c in result.category]
        cat_ok = true_cat in predicted_cats
        sent_ok = result.sentiment.value == str(row["sentiment"])
        cat_correct += int(cat_ok)
        sent_correct += int(sent_ok)
        per_cat[true_cat]["total"] += 1
        per_cat[true_cat]["correct"] += int(cat_ok)

    metrics = {
        "total": total,
        "category_accuracy": cat_correct / total,
        "sentiment_accuracy": sent_correct / total,
        "per_category": dict(per_cat),
    }
    _write_report(metrics)
    return metrics


def _write_report(m: dict) -> None:
    """Write the metrics to ACCURACY.md as a readable report."""
    lines = [
        "# Accuracy Report",
        "",
        f"Evaluated **{m['total']}** labeled samples from "
        "`tests/eval/labeled_samples.csv`.",
        "",
        "> The dataset is synthetic; ground-truth labels are the generation "
        "labels. Figures reflect classifier agreement with those labels.",
        "",
        "## Overall",
        "",
        f"- **Category accuracy:** {m['category_accuracy'] * 100:.1f}%",
        f"- **Sentiment accuracy:** {m['sentiment_accuracy'] * 100:.1f}%",
        "",
        "## Per-category accuracy",
        "",
        "| Category | Samples | Correct | Accuracy |",
        "|---|---|---|---|",
    ]
    for cat, v in sorted(m["per_category"].items()):
        acc = v["correct"] / v["total"] * 100 if v["total"] else 0.0
        lines.append(f"| {cat} | {v['total']} | {v['correct']} | {acc:.0f}% |")
    OUTPUT_PATH.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    result = run_eval()
    print(f"Category accuracy : {result['category_accuracy'] * 100:.1f}%")
    print(f"Sentiment accuracy: {result['sentiment_accuracy'] * 100:.1f}%")
    print(f"Report written to {OUTPUT_PATH}")
