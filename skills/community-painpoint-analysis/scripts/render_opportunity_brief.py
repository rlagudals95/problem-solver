from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import read_json
from render_problem_definition import ensure_output_does_not_clobber_inputs, load_labeled_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render an opportunity brief before PRD writing.")
    parser.add_argument("manifest", help="Path to source_manifest.json.")
    parser.add_argument("labeled_posts", help="Path to labeled_posts.csv.")
    parser.add_argument("summary", help="Path to label_summary.json.")
    parser.add_argument("problem_definition", help="Path to problem-definition.md.")
    parser.add_argument("output", help="Path to write opportunity-brief.md.")
    return parser.parse_args()


def top_pain(summary: dict) -> dict:
    pain_points = summary.get("pain_points", [])
    return pain_points[0] if pain_points else {"name": "검증된 페인포인트 없음", "count": 0, "share": 0}


def first_segment(summary: dict) -> str:
    segments = [item for item in summary.get("segments", []) if item.get("name")]
    if not segments:
        return "반복 세그먼트 없음"
    return f"{segments[0]['name']} ({segments[0]['count']}건)"


def render_evidence(pain: dict) -> list[str]:
    evidence = pain.get("top_evidence", [])
    if not evidence:
        return ["- 대표 근거 없음"]
    return [
        f"- record_id `{item.get('record_id', '')}`: {item.get('quote') or item.get('title', '')}"
        for item in evidence[:5]
    ]


def render(manifest: dict, labeled_rows: list[dict[str, str]], summary: dict, problem_definition: Path) -> str:
    pain = top_pain(summary)
    manifest_summary = manifest.get("summary", {})
    labeled_row_count = len(labeled_rows)
    relevant_rows = summary.get("relevant_rows", 0)
    needs_review = summary.get("needs_review_record_ids", [])
    confidence = "중간"
    if pain.get("count", 0) >= 3 and pain.get("share", 0) >= 0.3:
        confidence = "높음"
    elif pain.get("count", 0) <= 1:
        confidence = "낮음"

    return "\n".join(
        [
            "# 기회 브리프",
            "",
            "## 1. 기회 요약",
            "",
            f"가장 먼저 검토할 기회는 **{pain['name']}**입니다.",
            f"유효 분석 글 {relevant_rows}개 중 {pain.get('count', 0)}개에서 반복됐습니다.",
            f"문제정의 문서: `{problem_definition}`",
            "",
            "## 2. 우선 타겟 세그먼트",
            "",
            f"- 1차 세그먼트: {first_segment(summary)}",
            "- 세그먼트 선택 이유: 반복 빈도와 대표 근거가 가장 강한 문제에 연결되어 있습니다.",
            "",
            "## 3. 근거 강도",
            "",
            f"- 원본 행 수: {manifest_summary.get('source_rows', 0)}",
            f"- 분석 포함 행 수: {manifest_summary.get('included_rows', 0)}",
            f"- 라벨링 완료 행 수: {labeled_row_count}",
            f"- 유효 분석 글 수: {relevant_rows}",
            f"- 기회 신뢰도: {confidence}",
            "- 대표 근거:",
            *render_evidence(pain),
            "",
            "## 4. 비즈니스 연결",
            "",
            f"- 사용자가 `{pain['name']}`을 해결하지 못하면 탐색 비용, 의사결정 지연, 신뢰 저하가 커질 수 있습니다.",
            "- 이 문제를 줄이면 핵심 행동 완료율, 재방문, 문의/전환 같은 선행 지표를 개선할 가능성이 있습니다.",
            "- 아직 매출, 지불의사, 전환율 데이터는 없으므로 비즈니스 효과는 검증 가정으로 둡니다.",
            "",
            "## 5. 리스크와 보류점",
            "",
            f"- 추가 검토 필요 row 수: {len(needs_review)}",
            f"- 무관 라벨 row 수: {summary.get('irrelevant_rows', 0)}",
            "- 커뮤니티 데이터는 불만/질문이 과대표집될 수 있습니다.",
            "- PRD 작성 전 사용자 인터뷰 또는 행동 실험으로 문제 강도를 확인해야 합니다.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    try:
        manifest_path = Path(args.manifest)
        labeled_posts = Path(args.labeled_posts)
        summary_path = Path(args.summary)
        problem_definition = Path(args.problem_definition)
        output = Path(args.output)
        ensure_output_does_not_clobber_inputs(output, [manifest_path, labeled_posts, summary_path, problem_definition])
        manifest = read_json(manifest_path)
        labeled_rows = load_labeled_rows(labeled_posts)
        summary = read_json(summary_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render(manifest, labeled_rows, summary, problem_definition), encoding="utf-8")
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"opportunity brief written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
