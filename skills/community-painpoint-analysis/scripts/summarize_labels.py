from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

from common import (
    IRRELEVANT_REASON_VALUES,
    MERGED_COLUMNS,
    SENTIMENT_VALUES,
    parse_bool,
    read_csv,
    write_json,
)

SEVERITY_SCORE = {"낮음": 1, "중간": 2, "높음": 3}
CONFIDENCE_SCORE = {"낮음": 1, "중간": 2, "높음": 3}
REQUIRED_RELEVANT_COLUMNS = ["primary_pain_point", "severity", "evidence_quote", "confidence"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize merged community pain point labels.")
    parser.add_argument("labeled_posts", help="Path to labeled_posts.csv.")
    parser.add_argument("output", help="Path to write label_summary.json.")
    return parser.parse_args()


def top_counter(counter: Counter[str]) -> list[dict[str, int | str]]:
    return [{"name": name, "count": count} for name, count in counter.most_common() if name]


def ensure_output_does_not_clobber_input(labeled_posts: Path, output: Path) -> None:
    if labeled_posts.resolve() == output.resolve():
        raise ValueError("output path must not match the labeled_posts input path")


def validate_schema(labeled_posts: Path, header: list[str]) -> None:
    if header != MERGED_COLUMNS:
        raise ValueError(
            f"{labeled_posts}: expected merged columns: {', '.join(MERGED_COLUMNS)}"
        )


def require_bool(labeled_posts: Path, line_number: int, row: dict[str, str], column: str) -> bool:
    parsed = parse_bool(row.get(column, ""))
    if parsed is None:
        raise ValueError(
            f"{labeled_posts}: line {line_number}: invalid {column}: {row.get(column, '')!r}"
        )
    return parsed


def validate_enum(
    errors: list[str],
    labeled_posts: Path,
    line_number: int,
    row: dict[str, str],
    column: str,
    allowed_values: set[str],
) -> None:
    value = row.get(column, "").strip()
    if value and value not in allowed_values:
        errors.append(f"{labeled_posts}: line {line_number}: unknown {column}: {value}")


def validate_rows(
    labeled_posts: Path,
    rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[str]]:
    relevant_rows = []
    irrelevant_rows = []
    needs_review_record_ids = []
    errors = []

    for line_number, row in enumerate(rows, start=2):
        is_relevant = require_bool(labeled_posts, line_number, row, "is_relevant")
        needs_review = require_bool(labeled_posts, line_number, row, "needs_review")
        if needs_review:
            needs_review_record_ids.append(row.get("record_id", ""))

        if is_relevant:
            for column in REQUIRED_RELEVANT_COLUMNS:
                if not row.get(column, "").strip():
                    errors.append(f"{labeled_posts}: line {line_number}: {column} is required")
            severity = row.get("severity", "")
            if severity and severity not in SEVERITY_SCORE:
                errors.append(f"{labeled_posts}: line {line_number}: unknown severity: {severity}")
            confidence = row.get("confidence", "")
            if confidence and confidence not in CONFIDENCE_SCORE:
                errors.append(f"{labeled_posts}: line {line_number}: unknown confidence: {confidence}")
            validate_enum(errors, labeled_posts, line_number, row, "sentiment", SENTIMENT_VALUES)
            relevant_rows.append(row)
        else:
            if not row.get("irrelevant_reason", "").strip():
                errors.append(f"{labeled_posts}: line {line_number}: irrelevant_reason is required")
            validate_enum(errors, labeled_posts, line_number, row, "irrelevant_reason", IRRELEVANT_REASON_VALUES)
            irrelevant_rows.append(row)

    if errors:
        raise ValueError("\n".join(errors))
    return relevant_rows, irrelevant_rows, needs_review_record_ids


def top_evidence_for_pain(
    evidence_rows: list[tuple[int, dict[str, str]]],
) -> list[dict[str, str]]:
    ranked_rows = sorted(
        evidence_rows,
        key=lambda item: (
            -SEVERITY_SCORE[item[1].get("severity", "")],
            -CONFIDENCE_SCORE[item[1].get("confidence", "")],
            0 if item[1].get("evidence_quote", "").strip() else 1,
            item[0],
        ),
    )
    return [
        {
            "record_id": row.get("record_id", ""),
            "quote": row.get("evidence_quote", ""),
            "url": row.get("url", ""),
            "title": row.get("title", ""),
        }
        for _order, row in ranked_rows[:5]
    ]


def summarize(labeled_posts: Path) -> dict:
    header, rows = read_csv(labeled_posts)
    validate_schema(labeled_posts, header)
    relevant_rows, irrelevant_rows, needs_review_record_ids = validate_rows(labeled_posts, rows)

    pain_counter: Counter[str] = Counter(row.get("primary_pain_point", "") for row in relevant_rows)
    segment_counter: Counter[str] = Counter(row.get("segment_candidate", "") for row in relevant_rows)
    journey_counter: Counter[str] = Counter(row.get("journey_stage", "") for row in relevant_rows)
    sentiment_counter: Counter[str] = Counter(row.get("sentiment", "") for row in relevant_rows)
    severity_counter: Counter[str] = Counter(row.get("severity", "") for row in relevant_rows)
    confidence_counter: Counter[str] = Counter(row.get("confidence", "") for row in relevant_rows)
    irrelevant_counter: Counter[str] = Counter(row.get("irrelevant_reason", "") for row in irrelevant_rows)

    evidence_by_pain: dict[str, list[tuple[int, dict[str, str]]]] = defaultdict(list)
    severity_by_pain: dict[str, list[int]] = defaultdict(list)
    for order, row in enumerate(relevant_rows):
        pain = row.get("primary_pain_point", "")
        severity_by_pain[pain].append(SEVERITY_SCORE.get(row.get("severity", ""), 0))
        evidence_by_pain[pain].append((order, row))

    pain_points = []
    for pain, count in pain_counter.most_common():
        scores = severity_by_pain[pain]
        average_severity = round(sum(scores) / len(scores), 2) if scores else 0
        top_evidence = top_evidence_for_pain(evidence_by_pain[pain])
        pain_points.append(
            {
                "name": pain,
                "count": count,
                "share": round(count / len(relevant_rows), 4) if relevant_rows else 0,
                "average_severity": average_severity,
                "evidence_record_ids": [item["record_id"] for item in top_evidence],
                "top_evidence": top_evidence,
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
        "confidence": top_counter(confidence_counter),
        "irrelevant_reasons": top_counter(irrelevant_counter),
        "needs_review_record_ids": needs_review_record_ids,
    }


def main() -> int:
    args = parse_args()
    try:
        labeled_posts = Path(args.labeled_posts)
        output = Path(args.output)
        ensure_output_does_not_clobber_input(labeled_posts, output)
        summary = summarize(labeled_posts)
        write_json(output, summary)
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"summary written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
