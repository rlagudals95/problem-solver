from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

from common import parse_bool, read_csv, write_json

SEVERITY_SCORE = {"낮음": 1, "중간": 2, "높음": 3}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize merged community pain point labels.")
    parser.add_argument("labeled_posts", help="Path to labeled_posts.csv.")
    parser.add_argument("output", help="Path to write label_summary.json.")
    return parser.parse_args()


def top_counter(counter: Counter[str]) -> list[dict[str, int | str]]:
    return [{"name": name, "count": count} for name, count in counter.most_common() if name]


def summarize(labeled_posts: Path) -> dict:
    _, rows = read_csv(labeled_posts)
    relevant_rows = [row for row in rows if parse_bool(row.get("is_relevant", "")) is True]
    irrelevant_rows = [row for row in rows if parse_bool(row.get("is_relevant", "")) is False]

    pain_counter: Counter[str] = Counter(row.get("primary_pain_point", "") for row in relevant_rows)
    segment_counter: Counter[str] = Counter(row.get("segment_candidate", "") for row in relevant_rows)
    journey_counter: Counter[str] = Counter(row.get("journey_stage", "") for row in relevant_rows)
    sentiment_counter: Counter[str] = Counter(row.get("sentiment", "") for row in relevant_rows)
    severity_counter: Counter[str] = Counter(row.get("severity", "") for row in relevant_rows)
    irrelevant_counter: Counter[str] = Counter(row.get("irrelevant_reason", "") for row in irrelevant_rows)

    evidence_by_pain: dict[str, list[dict[str, str]]] = defaultdict(list)
    severity_by_pain: dict[str, list[int]] = defaultdict(list)
    for row in relevant_rows:
        pain = row.get("primary_pain_point", "")
        if not pain:
            continue
        severity_by_pain[pain].append(SEVERITY_SCORE.get(row.get("severity", ""), 0))
        if len(evidence_by_pain[pain]) < 5:
            evidence_by_pain[pain].append(
                {
                    "record_id": row.get("record_id", ""),
                    "quote": row.get("evidence_quote", ""),
                    "url": row.get("url", ""),
                    "title": row.get("title", ""),
                }
            )

    pain_points = []
    for pain, count in pain_counter.most_common():
        if not pain:
            continue
        scores = severity_by_pain[pain]
        average_severity = round(sum(scores) / len(scores), 2) if scores else 0
        pain_points.append(
            {
                "name": pain,
                "count": count,
                "share": round(count / len(relevant_rows), 4) if relevant_rows else 0,
                "average_severity": average_severity,
                "evidence_record_ids": [item["record_id"] for item in evidence_by_pain[pain]],
                "top_evidence": evidence_by_pain[pain],
            }
        )

    return {
        "total_rows": len(rows),
        "relevant_rows": len(relevant_rows),
        "irrelevant_rows": len(irrelevant_rows),
        "pain_points": pain_points,
        "segments": top_counter(segment_counter),
        "journey_stages": top_counter(journey_counter),
        "sentiment": top_counter(sentiment_counter),
        "severity": top_counter(severity_counter),
        "irrelevant_reasons": top_counter(irrelevant_counter),
        "needs_review_record_ids": [
            row.get("record_id", "")
            for row in rows
            if parse_bool(row.get("needs_review", "")) is True
        ],
    }


def main() -> int:
    args = parse_args()
    try:
        summary = summarize(Path(args.labeled_posts))
        write_json(Path(args.output), summary)
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"summary written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
