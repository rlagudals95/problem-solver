from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import read_json
from render_opportunity_brief import top_pain
from render_problem_definition import ensure_output_does_not_clobber_inputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render product direction before PRD writing.")
    parser.add_argument("summary", help="Path to label_summary.json.")
    parser.add_argument("opportunity_brief", help="Path to opportunity-brief.md.")
    parser.add_argument("output", help="Path to write product-direction.md.")
    return parser.parse_args()


def render(summary: dict, opportunity_brief: Path) -> str:
    pain = top_pain(summary)
    segments = [item for item in summary.get("segments", []) if item.get("name")]
    primary_segment = segments[0]["name"] if segments else "우선 세그먼트 미정"
    return "\n".join(
        [
            "# 제품 방향성",
            "",
            "## 1. 방향성 한 줄",
            "",
            f"**{primary_segment}**가 `{pain['name']}`을 스스로 이해하고 다음 행동을 결정할 수 있게 돕는 방향을 우선 검토합니다.",
            "",
            "## 2. 제품 전략 가설",
            "",
            "- 사용자는 핵심 문제의 원인과 선택지를 이해하기 전까지 다음 행동을 확신하기 어렵습니다.",
            "- 따라서 첫 방향은 기능을 많이 만드는 것이 아니라, 의사결정에 필요한 정보와 리스크를 투명하게 정리하는 것입니다.",
            f"- 기회 브리프: `{opportunity_brief}`",
            "",
            "## 3. 솔루션 원칙",
            "",
            "- 사용자가 문제를 겪는 맥락, 제약, 의사결정 기준을 먼저 파악한다.",
            "- 하나의 정답보다 상황별 비교 기준과 다음 행동을 제시한다.",
            "- 추천이나 결론보다 근거, 판단 과정, 확인해야 할 리스크를 우선한다.",
            "- 확신이 부족한 정보는 단정하지 않고 추가 확인 대상으로 표시한다.",
            "",
            "## 4. 가능한 솔루션 테마",
            "",
            "- 문제 진단 체크리스트",
            "- 선택지 비교 리포트",
            "- 의사결정 리스크 질문지",
            "- 커뮤니티 근거 기반 실행 전 점검 리포트",
            "",
            "## 5. 지금 하지 않을 것",
            "",
            "- 바로 특정 솔루션 추천 랭킹을 만들지 않는다.",
            "- 커뮤니티 빈도만으로 시장 규모나 매출 효과를 단정하지 않는다.",
            "- PRD 작성 전에는 상세 기능 요구사항과 화면 설계를 확정하지 않는다.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    try:
        summary_path = Path(args.summary)
        opportunity_brief = Path(args.opportunity_brief)
        output = Path(args.output)
        ensure_output_does_not_clobber_inputs(output, [summary_path, opportunity_brief])
        summary = read_json(summary_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render(summary, opportunity_brief), encoding="utf-8")
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"product direction written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
