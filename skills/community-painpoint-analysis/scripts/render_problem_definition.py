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
    if "- 결과: coverage passed" in audit or "- Result: coverage passed" in audit:
        return "coverage passed"
    if "- 결과: coverage failed" in audit or "- Result: coverage failed" in audit:
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
    top_pain_name = top_pain.get("name", "검증된 페인포인트 없음")
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
        "# 문제 정의",
        "",
        "## 1. 핵심 요약",
        "",
        f"가장 강하게 검증된 문제는 **{top_pain_name}**입니다.",
        f"관련 글은 {top_pain.get('count', 0)}개이며, 유효 분석 글의 {format_share(top_pain.get('share', 0))}를 차지합니다.",
        f"대표 근거 record_id: {', '.join(top_pain.get('evidence_record_ids', [])) or '없음'}.",
        "",
        "## 2. 데이터 커버리지",
        "",
        f"- 주제: {manifest.get('topic', '')}",
        f"- 원본 행 수: {manifest_summary.get('source_rows', 0)}",
        f"- 분석 포함 행 수: {manifest_summary.get('included_rows', 0)}",
        f"- 제외 행 수: {manifest_summary.get('excluded_rows', 0)}",
        f"- 청크 수: {manifest_summary.get('chunks', 0)}",
        f"- 검증 결과: {validation}",
        f"- 코드북: {codebook_path if codebook_path else '제공되지 않음'}",
        "",
        "## 3. 주요 페인포인트",
        "",
    ]

    if pain_points:
        for index, pain in enumerate(pain_points, start=1):
            lines.extend(
                [
                    f"### {index}. {pain['name']}",
                    "",
                    f"- 건수: {pain['count']}",
                    f"- 유효 분석 글 내 비중: {format_share(pain['share'])}",
                    f"- 평균 심각도 점수: {pain['average_severity']}",
                    "- 대표 근거:",
                    *render_evidence(pain.get("top_evidence", [])),
                    "",
                ]
            )
    else:
        lines.extend(["검증된 유효 페인포인트가 없습니다.", ""])

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
            "## 4. 타겟 세그먼트",
            "",
            *bullet_list(segment_lines, "반복적으로 나타난 타겟 세그먼트가 없습니다."),
            "",
            "## 5. JTBD 문제 진술",
            "",
            *bullet_list(jtbd_lines[:5], "사용 가능한 JTBD 진술이 없습니다."),
            "",
            "## 6. 기회 우선순위",
            "",
        ]
    )

    for index, pain in enumerate(pain_points[:5], start=1):
        lines.append(
            f"- {index}순위: {pain['name']} - 빈도 {pain['count']}건, "
            f"비중 {format_share(pain['share'])}, 평균 심각도 {pain['average_severity']}."
        )
    if not pain_points:
        lines.append("- 유효 근거가 없어 우선순위를 정할 수 없습니다.")

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
            "## 7. 추천 문제 정의",
            "",
            f"가장 먼저 검증할 문제는 **{top_pain_name}**입니다.",
            f"문제 진술: {recommended_jtbd or '추가 JTBD 정리가 필요합니다.'}",
            "",
            "## 8. 리스크와 반대 근거",
            "",
            f"- 추가 검토 필요 row: {', '.join(needs_review) if needs_review else '없음'}",
            f"- 무관 라벨 row 수: {summary.get('irrelevant_rows', 0)}",
            *bullet_list([f"무관 라벨 사유: {item}" for item in irrelevant_reasons], "병합 라벨에 무관 사유가 없습니다."),
            *bullet_list([f"원본 제외 사유: {item}" for item in excluded_lines], "제외된 원본 row가 없습니다."),
            "",
            "## 9. 다음 검증 질문",
            "",
            f"- 인터뷰에서 사용자가 최근 `{top_pain_name}`을 겪은 순간을 구체적으로 설명하게 한다.",
            "- 솔루션 설계 전에 이 문제가 다른 문제보다 더 중요한지 사용자가 직접 우선순위를 매기게 한다.",
            "- 제품 방향을 확정하기 전에 컨시어지 테스트나 랜딩페이지 테스트로 문제 강도를 검증한다.",
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
