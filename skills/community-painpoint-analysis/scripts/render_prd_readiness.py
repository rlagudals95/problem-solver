from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import read_json
from render_opportunity_brief import top_pain
from render_problem_definition import ensure_output_does_not_clobber_inputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render PRD readiness decision before writing a PRD.")
    parser.add_argument("manifest", help="Path to source_manifest.json.")
    parser.add_argument("summary", help="Path to label_summary.json.")
    parser.add_argument("problem_definition", help="Path to problem-definition.md.")
    parser.add_argument("opportunity_brief", help="Path to opportunity-brief.md.")
    parser.add_argument("product_direction", help="Path to product-direction.md.")
    parser.add_argument("validation_plan", help="Path to validation-plan.md.")
    parser.add_argument("output", help="Path to write prd-readiness.md.")
    return parser.parse_args()


def readiness_decision(summary: dict) -> tuple[str, str]:
    pain = top_pain(summary)
    enough_research_signal = pain.get("count", 0) >= 3 and pain.get("share", 0) >= 0.3
    has_validation_evidence = False
    if enough_research_signal and has_validation_evidence:
        return "PRD 작성 가능", "문제 강도와 행동 검증이 모두 충분합니다."
    if not enough_research_signal:
        return "PRD 작성 보류", "커뮤니티 반복 신호가 아직 충분하지 않습니다."
    return "PRD 작성 보류", "커뮤니티 근거는 있으나 사용자 행동 검증이 아직 부족합니다."


def render(
    manifest: dict,
    summary: dict,
    problem_definition: Path,
    opportunity_brief: Path,
    product_direction: Path,
    validation_plan: Path,
) -> str:
    pain = top_pain(summary)
    decision, reason = readiness_decision(summary)
    manifest_summary = manifest.get("summary", {})
    return "\n".join(
        [
            "# PRD 진입 판단",
            "",
            "## 1. 판단",
            "",
            f"- 판단: {decision}",
            f"- 이유: {reason}",
            "",
            "## 2. 현재 근거",
            "",
            f"- 최우선 문제: {pain['name']}",
            f"- 관련 글 수: {pain.get('count', 0)}",
            f"- 유효 분석 글 내 비중: {pain.get('share', 0) * 100:.1f}%",
            f"- 원본 행 수: {manifest_summary.get('source_rows', 0)}",
            f"- 분석 포함 행 수: {manifest_summary.get('included_rows', 0)}",
            "",
            "## 3. 산출물 체크리스트",
            "",
            f"- 문제 정의: `{problem_definition}`",
            f"- 기회 브리프: `{opportunity_brief}`",
            f"- 제품 방향성: `{product_direction}`",
            f"- 검증 계획: `{validation_plan}`",
            "",
            "## 4. PRD 전에 남은 갭",
            "",
            "- 실제 사용자 인터뷰 결과가 아직 없다.",
            "- 문제 해결 시 전환/신뢰/구매 행동이 바뀌는지 검증되지 않았다.",
            "- 솔루션별 비용, 운영 가능성, 데이터 확보 가능성이 검증되지 않았다.",
            "",
            "## 5. 다음 단계",
            "",
            "- 다음 단계: 검증 계획을 먼저 실행",
            "- 검증 결과가 성공 기준을 넘으면 PRD를 작성한다.",
            "- 실패하거나 신호가 약하면 문제 정의 또는 타겟 세그먼트를 재조정한다.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    try:
        manifest_path = Path(args.manifest)
        summary_path = Path(args.summary)
        problem_definition = Path(args.problem_definition)
        opportunity_brief = Path(args.opportunity_brief)
        product_direction = Path(args.product_direction)
        validation_plan = Path(args.validation_plan)
        output = Path(args.output)
        ensure_output_does_not_clobber_inputs(
            output,
            [manifest_path, summary_path, problem_definition, opportunity_brief, product_direction, validation_plan],
        )
        manifest = read_json(manifest_path)
        summary = read_json(summary_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            render(manifest, summary, problem_definition, opportunity_brief, product_direction, validation_plan),
            encoding="utf-8",
        )
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"PRD readiness written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
