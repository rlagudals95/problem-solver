from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from common import MERGED_COLUMNS, read_csv, read_json
from summarize_labels import summarize


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a problem-definition.md from validated community labels.")
    parser.add_argument("manifest", help="Path to source_manifest.json.")
    parser.add_argument("labeled_posts", help="Path to labeled_posts.csv.")
    parser.add_argument("summary", help="Path to label_summary.json.")
    parser.add_argument("output", help="Path to write problem-definition.md.")
    parser.add_argument("--codebook", help="Optional codebook.md path used for the analysis.")
    parser.add_argument("--audit", help="Optional audit-report.md path used for the analysis.")
    return parser.parse_args()


def ensure_output_does_not_clobber_inputs(output: Path, inputs: list[Path]) -> None:
    resolved_output = output.resolve()
    for input_path in inputs:
        if resolved_output == input_path.resolve():
            raise ValueError(f"output path must not match input path: {input_path}")


def load_labeled_rows(labeled_posts: Path) -> list[dict[str, str]]:
    header, rows = read_csv(labeled_posts)
    if header != MERGED_COLUMNS:
        raise ValueError(f"{labeled_posts}: expected merged columns: {', '.join(MERGED_COLUMNS)}")
    return rows


def validation_result(audit_path: Path | None) -> str:
    if audit_path is None or not audit_path.exists():
        return "unknown"
    audit = audit_path.read_text(encoding="utf-8")
    if "- Result: coverage passed" in audit:
        return "coverage passed"
    if "- Result: coverage failed" in audit:
        return "coverage failed"
    return "unknown"


def verify_summary_is_current(labeled_posts: Path, summary: dict) -> None:
    recomputed = summarize(labeled_posts)
    if summary != recomputed:
        raise ValueError("label_summary.json is stale or does not match labeled_posts.csv")


def bullet_list(items: list[str], empty_text: str) -> list[str]:
    if not items:
        return [f"- {empty_text}"]
    return [f"- {item}" for item in items]


def format_share(value: float) -> str:
    return f"{value * 100:.1f}%"


def rows_by_pain(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        if row.get("is_relevant", "").lower() != "true":
            continue
        pain = row.get("primary_pain_point", "").strip()
        if pain:
            grouped.setdefault(pain, []).append(row)
    return grouped


def render_evidence(evidence: list[dict]) -> list[str]:
    lines = []
    for item in evidence:
        quote = item.get("quote", "")
        title = item.get("title", "")
        record_id = item.get("record_id", "")
        url = item.get("url", "")
        suffix = f" ({url})" if url else ""
        lines.append(f"  - record_id `{record_id}`: {quote or title}{suffix}")
    return lines or ["  - No representative evidence available."]


def render_problem_definition(
    manifest: dict,
    labeled_rows: list[dict[str, str]],
    summary: dict,
    audit_path: Path | None,
    codebook_path: Path | None,
) -> str:
    manifest_summary = manifest["summary"]
    pain_points = summary.get("pain_points", [])
    top_pain = pain_points[0] if pain_points else {}
    top_pain_name = top_pain.get("name", "No validated pain point")
    grouped_rows = rows_by_pain(labeled_rows)
    recommended_rows = grouped_rows.get(top_pain_name, [])
    recommended_jtbd = recommended_rows[0].get("jtbd", "") if recommended_rows else ""
    validation = validation_result(audit_path)
    excluded_reasons = Counter(
        record.get("exclusion_reason", "")
        for record in manifest.get("records", [])
        if not record.get("included")
    )

    lines = [
        "# Problem Definition",
        "",
        "## 1. Executive Summary",
        "",
        f"The strongest validated problem is **{top_pain_name}**.",
        f"It appears in {top_pain.get('count', 0)} rows ({format_share(top_pain.get('share', 0))} of relevant rows).",
        f"Representative record_id values: {', '.join(top_pain.get('evidence_record_ids', [])) or 'none'}.",
        "",
        "## 2. Dataset Coverage",
        "",
        f"- Topic: {manifest.get('topic', '')}",
        f"- Source rows: {manifest_summary.get('source_rows', 0)}",
        f"- Included rows: {manifest_summary.get('included_rows', 0)}",
        f"- Excluded rows: {manifest_summary.get('excluded_rows', 0)}",
        f"- Chunks: {manifest_summary.get('chunks', 0)}",
        f"- Validation result: {validation}",
        f"- Codebook: {codebook_path if codebook_path else 'not provided'}",
        "",
        "## 3. Top Pain Points",
        "",
    ]

    if pain_points:
        for index, pain in enumerate(pain_points, start=1):
            lines.extend(
                [
                    f"### {index}. {pain['name']}",
                    "",
                    f"- Count: {pain['count']}",
                    f"- Share of relevant rows: {format_share(pain['share'])}",
                    f"- Average severity score: {pain['average_severity']}",
                    "- Evidence:",
                    *render_evidence(pain.get("top_evidence", [])),
                    "",
                ]
            )
    else:
        lines.extend(["No relevant pain points were validated.", ""])

    segment_lines = [
        f"{item['name']} ({item['count']} rows)"
        for item in summary.get("segments", [])
        if item.get("name")
    ]
    jtbd_lines = []
    seen_jtbd = set()
    for row in labeled_rows:
        jtbd = row.get("jtbd", "").strip()
        if row.get("is_relevant", "").lower() == "true" and jtbd and jtbd not in seen_jtbd:
            seen_jtbd.add(jtbd)
            jtbd_lines.append(jtbd)

    lines.extend(
        [
            "## 4. Target Segments",
            "",
            *bullet_list(segment_lines, "No repeated target segment identified."),
            "",
            "## 5. JTBD Problem Statements",
            "",
            *bullet_list(jtbd_lines[:5], "No JTBD statements available."),
            "",
            "## 6. Opportunity Prioritization",
            "",
        ]
    )

    for index, pain in enumerate(pain_points[:5], start=1):
        lines.append(
            f"- Rank {index}: {pain['name']} - frequency {pain['count']}, "
            f"share {format_share(pain['share'])}, severity {pain['average_severity']}."
        )
    if not pain_points:
        lines.append("- No opportunity can be prioritized without relevant evidence.")

    needs_review = summary.get("needs_review_record_ids", [])
    irrelevant_reasons = [
        f"{item['name']} ({item['count']})"
        for item in summary.get("irrelevant_reasons", [])
        if item.get("name")
    ]
    excluded_lines = [f"{reason}: {count}" for reason, count in excluded_reasons.items() if reason]

    lines.extend(
        [
            "",
            "## 7. Recommended Problem Definition",
            "",
            f"Investigate **{top_pain_name}** first.",
            f"Problem statement: {recommended_jtbd or 'Needs follow-up JTBD synthesis.'}",
            "",
            "## 8. Risks And Counter-Evidence",
            "",
            f"- Rows requiring review: {', '.join(needs_review) if needs_review else 'none'}",
            f"- Irrelevant labeled rows: {summary.get('irrelevant_rows', 0)}",
            *bullet_list([f"Irrelevant reason: {item}" for item in irrelevant_reasons], "No irrelevant reasons in merged labels."),
            *bullet_list([f"Excluded source row reason: {item}" for item in excluded_lines], "No excluded source rows."),
            "",
            "## 9. Next Validation Questions",
            "",
            f"- In interviews, ask users to describe the last time they experienced `{top_pain_name}`.",
            "- Test whether users can rank the pain against alternative problems before solution design.",
            "- Run a concierge or landing-page test that validates the problem before committing to a product direction.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    try:
        manifest_path = Path(args.manifest)
        labeled_posts = Path(args.labeled_posts)
        summary_path = Path(args.summary)
        output = Path(args.output)
        codebook_path = Path(args.codebook) if args.codebook else None
        audit_path = Path(args.audit) if args.audit else None
        inputs = [manifest_path, labeled_posts, summary_path]
        if codebook_path:
            inputs.append(codebook_path)
        if audit_path:
            inputs.append(audit_path)
        ensure_output_does_not_clobber_inputs(output, inputs)

        manifest = read_json(manifest_path)
        summary = read_json(summary_path)
        verify_summary_is_current(labeled_posts, summary)
        labeled_rows = load_labeled_rows(labeled_posts)
        markdown = render_problem_definition(manifest, labeled_rows, summary, audit_path, codebook_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"problem definition written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
