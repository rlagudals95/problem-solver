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


def label_row(record: dict, **overrides: str) -> dict[str, str]:
    title = record["title"]
    row = {
        "record_id": record["record_id"],
        "is_relevant": "true",
        "irrelevant_reason": "",
        "user_context": "정수기 렌탈을 검토하는 가정 사용자",
        "journey_stage": "비교/검토",
        "jtbd": "When comparing rental options, I want clear total cost and conditions, so I can choose without regret.",
        "primary_pain_point": "렌탈 조건 비교 어려움",
        "secondary_pain_point": "",
        "sentiment": "부정",
        "severity": "중간",
        "segment_candidate": "렌탈 신규 검토자",
        "evidence_quote": title,
        "confidence": "높음",
        "needs_review": "false",
    }
    row.update(overrides)
    return row


def write_labels_from_manifest(run_dir: Path) -> Path:
    manifest = json.loads((run_dir / "source_manifest.json").read_text(encoding="utf-8"))
    rows = []
    for record in manifest["records"]:
        if not record["included"]:
            continue
        title = record["title"]
        if "광고" in title:
            rows.append(
                label_row(
                    record,
                    is_relevant="false",
                    irrelevant_reason="promotional_or_deal",
                    user_context="",
                    journey_stage="",
                    jtbd="",
                    primary_pain_point="",
                    sentiment="중립",
                    severity="낮음",
                    segment_candidate="",
                    evidence_quote="",
                    confidence="높음",
                )
            )
        elif "관리" in title:
            rows.append(
                label_row(
                    record,
                    jtbd="When scheduling maintenance visits, I want narrower visit windows, so I do not lose work time.",
                    primary_pain_point="관리 일정 조율 어려움",
                    secondary_pain_point="방문 시간 불확실성",
                    severity="높음",
                    evidence_quote=title,
                )
            )
        else:
            rows.append(label_row(record))

    labels = run_dir / "labels" / "chunk-labels.csv"
    labels.parent.mkdir(parents=True, exist_ok=True)
    with labels.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=LABEL_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return labels


class RenderProblemDefinitionTests(unittest.TestCase):
    def test_csv_pipeline_renders_problem_definition_markdown(self) -> None:
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

            labels = write_labels_from_manifest(run_dir)
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
            codebook.write_text(
                "# Codebook\n\n- 렌탈 조건 비교 어려움\n- 관리 일정 조율 어려움\n",
                encoding="utf-8",
            )
            render = run_script(
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

            self.assertEqual(render.returncode, 0, render.stderr)
            problem_definition = (run_dir / "problem-definition.md").read_text(encoding="utf-8")
            self.assertIn("# Problem Definition", problem_definition)
            self.assertIn("Source rows: 6", problem_definition)
            self.assertIn("Included rows: 4", problem_definition)
            self.assertIn("Excluded rows: 2", problem_definition)
            self.assertIn("Validation result: coverage passed", problem_definition)
            self.assertIn("렌탈 조건 비교 어려움", problem_definition)
            self.assertIn("관리 일정 조율 어려움", problem_definition)
            self.assertIn("record_id", problem_definition)
            self.assertIn("## 7. Recommended Problem Definition", problem_definition)
            self.assertIn("## 9. Next Validation Questions", problem_definition)


if __name__ == "__main__":
    unittest.main()
