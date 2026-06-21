from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import FIXTURES_DIR, run_script

LABEL_FIELDNAMES = [
    "record_id",
    "is_relevant",
    "irrelevant_reason",
    "user_context",
    "journey_stage",
    "jtbd",
    "primary_pain_point",
    "secondary_pain_point",
    "sentiment",
    "severity",
    "segment_candidate",
    "evidence_quote",
    "confidence",
    "needs_review",
]


def write_pipeline_labels(run_dir: Path) -> Path:
    manifest = json.loads((run_dir / "source_manifest.json").read_text(encoding="utf-8"))
    labels = run_dir / "labels" / "pipeline-labels.csv"
    labels.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for record in manifest["records"]:
        if not record["included"]:
            continue
        title = record["title"]
        if "광고" in title:
            rows.append(
                {
                    "record_id": record["record_id"],
                    "is_relevant": "false",
                    "irrelevant_reason": "promotional_or_deal",
                    "user_context": "",
                    "journey_stage": "",
                    "jtbd": "",
                    "primary_pain_point": "",
                    "secondary_pain_point": "",
                    "sentiment": "중립",
                    "severity": "낮음",
                    "segment_candidate": "",
                    "evidence_quote": "",
                    "confidence": "높음",
                    "needs_review": "false",
                }
            )
        elif "관리" in title:
            rows.append(
                {
                    "record_id": record["record_id"],
                    "is_relevant": "true",
                    "irrelevant_reason": "",
                    "user_context": "정수기 렌탈 이용 중 관리 방문을 조율하는 사용자",
                    "journey_stage": "사용/관리",
                    "jtbd": "관리 방문 일정을 잡을 때, 더 좁은 방문 시간대를 알고 싶다. 그래야 근무 시간을 잃지 않을 수 있다.",
                    "primary_pain_point": "관리 일정 조율 어려움",
                    "secondary_pain_point": "방문 시간 불확실성",
                    "sentiment": "부정",
                    "severity": "높음",
                    "segment_candidate": "기존 렌탈 이용자",
                    "evidence_quote": title,
                    "confidence": "높음",
                    "needs_review": "false",
                }
            )
        else:
            rows.append(
                {
                    "record_id": record["record_id"],
                    "is_relevant": "true",
                    "irrelevant_reason": "",
                    "user_context": "정수기 렌탈을 검토하는 가정 사용자",
                    "journey_stage": "비교/검토",
                    "jtbd": "정수기 렌탈 옵션을 비교할 때, 실제 총비용과 조건을 명확히 알고 싶다. 그래야 후회 없이 선택할 수 있다.",
                    "primary_pain_point": "렌탈 조건 비교 어려움",
                    "secondary_pain_point": "",
                    "sentiment": "부정",
                    "severity": "중간",
                    "segment_candidate": "렌탈 신규 검토자",
                    "evidence_quote": title,
                    "confidence": "높음",
                    "needs_review": "false",
                }
            )

    with labels.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=LABEL_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return labels


class PrePrdPipelineTests(unittest.TestCase):
    def test_csv_pipeline_renders_pre_prd_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "analysis-run"
            prepare = run_script(
                "prepare_dataset.py",
                "--topic",
                "rental",
                "--output-dir",
                str(run_dir),
                "--chunk-size",
                "2",
                str(FIXTURES_DIR / "community_posts.csv"),
                str(FIXTURES_DIR / "community_posts_extra.csv"),
            )
            self.assertEqual(prepare.returncode, 0, prepare.stderr)

            labels = write_pipeline_labels(run_dir)
            validate = run_script("validate_labels.py", str(run_dir / "source_manifest.json"), str(labels))
            self.assertEqual(validate.returncode, 0, validate.stderr)
            merge = run_script(
                "merge_labels.py",
                str(run_dir / "source_manifest.json"),
                str(run_dir / "labeled_posts.csv"),
                str(labels),
            )
            self.assertEqual(merge.returncode, 0, merge.stderr)
            summarize = run_script(
                "summarize_labels.py",
                str(run_dir / "labeled_posts.csv"),
                str(run_dir / "label_summary.json"),
            )
            self.assertEqual(summarize.returncode, 0, summarize.stderr)
            codebook = run_dir / "codebook.md"
            codebook.write_text("# 코드북\n\n- 렌탈 조건 비교 어려움\n- 관리 일정 조율 어려움\n", encoding="utf-8")
            problem_definition = run_script(
                "render_problem_definition.py",
                str(run_dir / "source_manifest.json"),
                str(run_dir / "labeled_posts.csv"),
                str(run_dir / "label_summary.json"),
                str(run_dir / "problem-definition.md"),
                "--codebook",
                str(codebook),
                "--audit",
                str(run_dir / "audit-report.md"),
            )
            self.assertEqual(problem_definition.returncode, 0, problem_definition.stderr)

            opportunity = run_script(
                "render_opportunity_brief.py",
                str(run_dir / "source_manifest.json"),
                str(run_dir / "labeled_posts.csv"),
                str(run_dir / "label_summary.json"),
                str(run_dir / "problem-definition.md"),
                str(run_dir / "opportunity-brief.md"),
            )
            self.assertEqual(opportunity.returncode, 0, opportunity.stderr)
            direction = run_script(
                "render_product_direction.py",
                str(run_dir / "label_summary.json"),
                str(run_dir / "opportunity-brief.md"),
                str(run_dir / "product-direction.md"),
            )
            self.assertEqual(direction.returncode, 0, direction.stderr)
            validation = run_script(
                "render_validation_plan.py",
                str(run_dir / "label_summary.json"),
                str(run_dir / "product-direction.md"),
                str(run_dir / "validation-plan.md"),
            )
            self.assertEqual(validation.returncode, 0, validation.stderr)
            readiness = run_script(
                "render_prd_readiness.py",
                str(run_dir / "source_manifest.json"),
                str(run_dir / "label_summary.json"),
                str(run_dir / "problem-definition.md"),
                str(run_dir / "opportunity-brief.md"),
                str(run_dir / "product-direction.md"),
                str(run_dir / "validation-plan.md"),
                str(run_dir / "prd-readiness.md"),
            )
            self.assertEqual(readiness.returncode, 0, readiness.stderr)

            opportunity_text = (run_dir / "opportunity-brief.md").read_text(encoding="utf-8")
            direction_text = (run_dir / "product-direction.md").read_text(encoding="utf-8")
            validation_text = (run_dir / "validation-plan.md").read_text(encoding="utf-8")
            readiness_text = (run_dir / "prd-readiness.md").read_text(encoding="utf-8")

            self.assertIn("# 기회 브리프", opportunity_text)
            self.assertIn("렌탈 조건 비교 어려움", opportunity_text)
            self.assertIn("## 4. 비즈니스 연결", opportunity_text)
            self.assertIn("# 제품 방향성", direction_text)
            self.assertIn("## 3. 솔루션 원칙", direction_text)
            self.assertIn("# 검증 계획", validation_text)
            self.assertIn("## 2. 위험 가정", validation_text)
            self.assertIn("# PRD 진입 판단", readiness_text)
            self.assertIn("판단: PRD 작성 보류", readiness_text)
            self.assertIn("다음 단계: 검증 계획을 먼저 실행", readiness_text)


if __name__ == "__main__":
    unittest.main()
