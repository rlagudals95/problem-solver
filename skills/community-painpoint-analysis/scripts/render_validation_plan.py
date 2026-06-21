from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import read_json
from render_opportunity_brief import top_pain
from render_problem_definition import ensure_output_does_not_clobber_inputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render validation plan before PRD writing.")
    parser.add_argument("summary", help="Path to label_summary.json.")
    parser.add_argument("product_direction", help="Path to product-direction.md.")
    parser.add_argument("output", help="Path to write validation-plan.md.")
    return parser.parse_args()


def render(summary: dict, product_direction: Path) -> str:
    pain = top_pain(summary)
    top_segment = summary.get("segments", [{}])[0].get("name", "우선 세그먼트 미정") if summary.get("segments") else "우선 세그먼트 미정"
    return "\n".join(
        [
            "# 검증 계획",
            "",
            "## 1. 검증 목표",
            "",
            f"`{pain['name']}`이 실제 사용자의 강한 문제인지, 그리고 **{top_segment}**가 먼저 풀 가치가 있는 세그먼트인지 확인합니다.",
            f"제품 방향성 문서: `{product_direction}`",
            "",
            "## 2. 위험 가정",
            "",
            "- 커뮤니티에서 자주 언급된 문제가 실제 핵심 행동에도 영향을 준다.",
            "- 사용자는 문제의 원인과 선택 기준을 투명하게 이해하면 의사결정 속도와 신뢰가 개선된다.",
            "- 사용자는 바로 추천받기보다 먼저 자신의 상황에 맞는 판단 기준과 리스크 점검을 원한다.",
            "- 이 문제를 겪는 사용자는 충분히 반복 가능한 세그먼트로 묶인다.",
            "",
            "## 3. 인터뷰 질문",
            "",
            f"- 최근 `{pain['name']}`을 겪은 상황을 처음부터 끝까지 설명해 주세요.",
            "- 그때 어떤 정보를 찾았고, 무엇이 가장 이해하기 어려웠나요?",
            "- 결국 어떤 선택을 했고, 선택을 미루거나 포기한 이유가 있었나요?",
            "- 판단 기준과 리스크를 한 번에 정리해주는 자료가 있다면 어떤 부분을 가장 먼저 보겠나요?",
            "",
            "## 4. 실험 설계",
            "",
            "- 1차: 문제 인터뷰 5명으로 문제 강도와 표현을 검증한다.",
            "- 2차: 랜딩페이지에서 총비용/조건 점검 리포트 신청 전환을 측정한다.",
            "- 3차: 수동 컨시어지 방식으로 실제 비교 리포트를 만들어 사용자가 다시 요청하는지 본다.",
            "",
            "## 5. 성공 기준",
            "",
            "- 인터뷰 5명 중 3명 이상이 같은 문제를 최근 3개월 내 경험했다.",
            "- 랜딩페이지 방문자 중 10% 이상이 리포트 신청 또는 상담 요청을 남긴다.",
            "- 컨시어지 테스트 사용자 중 2명 이상이 결과를 의사결정에 사용했다고 말한다.",
            "",
            "## 6. 중단 기준",
            "",
            "- 사용자가 문제를 불편하다고 말하지만 실제 행동 변화가 없다.",
            "- 문제 원인이 해결 가능한 정보/판단 문제가 아니라 단순 취향이나 일회성 불만에 가깝다.",
            "- 특정 커뮤니티/특정 사건 이슈로만 반복되고 일반화 가능성이 낮다.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    try:
        summary_path = Path(args.summary)
        product_direction = Path(args.product_direction)
        output = Path(args.output)
        ensure_output_does_not_clobber_inputs(output, [summary_path, product_direction])
        summary = read_json(summary_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render(summary, product_direction), encoding="utf-8")
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"validation plan written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
