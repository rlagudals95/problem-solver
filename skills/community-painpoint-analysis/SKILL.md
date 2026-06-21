---
name: community-painpoint-analysis
description: Use when analyzing large community-analyzer CSV exports to identify user pain points, label posts, prevent row omissions, synthesize JTBD problem definitions, and produce evidence-backed research outputs.
---

# Community Painpoint Analysis

Use this skill to convert one or more `community-analyzer` CSV exports into a traceable problem-definition package.

## How It Works

The pipeline preserves row-level traceability from raw CSV to final Markdown:

1. `prepare_dataset.py` turns every source row into `source_manifest.json`. Each row is either included with a stable `record_id` or explicitly excluded with an `exclusion_reason`.
2. Included rows are split into chunk CSVs. Chunks are only processing units; they are not used for final conclusions.
3. Codex labels every included `record_id` into label CSVs using the fixed schema and calibrated codebook.
4. `validate_labels.py` blocks synthesis unless every included `record_id` appears exactly once and label values are schema-valid.
5. `merge_labels.py` joins labels back to source metadata in manifest order.
6. `summarize_labels.py` computes aggregate pain point evidence from merged row-level labels.
7. `render_problem_definition.py` renders `problem-definition.md` from the manifest, merged labels, summary, audit report, and codebook.

## Core Rule

Do not write the final `problem-definition.md` until script validation proves every source row is either labeled exactly once or explicitly excluded in `source_manifest.json`.

## Required Inputs

- One or more source CSV files from `community-analyzer`.
- A short topic name for the run.
- A workspace output directory.

## Workflow

Resolve the installed skill directory before running scripts:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/community-painpoint-analysis"
```

Use a fresh analysis run directory unless the user explicitly confirms reuse. `prepare_dataset.py` writes or replaces `source_manifest.json` and `audit-report.md`, and recreates `chunks/` on successful runs.

1. Run dataset preparation:

```bash
python3 "$SKILL_DIR/scripts/prepare_dataset.py" \
  --topic "<topic>" \
  --output-dir "analysis-runs/YYYY-MM-DD-topic" \
  --chunk-size 100 \
  path/to/source.csv
```

2. Read `source_manifest.json` and inspect `audit-report.md`.

3. Calibrate `codebook.md` from a representative sample of 30-50 rows. Read `references/labeling-codebook-guide.md` before writing the codebook.

4. Label every chunk in `chunks/`. Save one label CSV per chunk in `labels/` using exactly these columns:

```text
record_id,is_relevant,irrelevant_reason,user_context,journey_stage,jtbd,primary_pain_point,secondary_pain_point,sentiment,severity,segment_candidate,evidence_quote,confidence,needs_review
```

5. Validate labels:

```bash
python3 "$SKILL_DIR/scripts/validate_labels.py" \
  analysis-runs/YYYY-MM-DD-topic/source_manifest.json \
  analysis-runs/YYYY-MM-DD-topic/labels/*.csv
```

6. If validation fails, fix the specific missing, duplicate, invalid, empty, or schema-invalid rows. Do not synthesize yet.

7. Merge labels:

```bash
python3 "$SKILL_DIR/scripts/merge_labels.py" \
  analysis-runs/YYYY-MM-DD-topic/source_manifest.json \
  analysis-runs/YYYY-MM-DD-topic/labeled_posts.csv \
  analysis-runs/YYYY-MM-DD-topic/labels/*.csv
```

8. Summarize labels:

```bash
python3 "$SKILL_DIR/scripts/summarize_labels.py" \
  analysis-runs/YYYY-MM-DD-topic/labeled_posts.csv \
  analysis-runs/YYYY-MM-DD-topic/label_summary.json
```

Merge and summarize reject input/output path collisions, and output files may be overwritten if paths are reused. Keep outputs as the standard separate paths: `labeled_posts.csv` and `label_summary.json`.

9. Reconcile taxonomy drift using the merged labels. Preserve raw labels in `labeled_posts.csv`; document normalized clusters in the final Markdown.

10. Render the initial problem definition:

```bash
python3 "$SKILL_DIR/scripts/render_problem_definition.py" \
  analysis-runs/YYYY-MM-DD-topic/source_manifest.json \
  analysis-runs/YYYY-MM-DD-topic/labeled_posts.csv \
  analysis-runs/YYYY-MM-DD-topic/label_summary.json \
  analysis-runs/YYYY-MM-DD-topic/problem-definition.md \
  --codebook analysis-runs/YYYY-MM-DD-topic/codebook.md \
  --audit analysis-runs/YYYY-MM-DD-topic/audit-report.md
```

11. Read `references/problem-definition-template.md` and review `problem-definition.md`. You may improve clarity and product judgment, but do not remove coverage numbers, `record_id` evidence, risks, or counter-evidence.

## Quality Gates

- `source_manifest.json` exists.
- `codebook.md` exists.
- Validation passes with no missing included rows.
- Excluded rows have explicit `exclusion_reason`.
- `labeled_posts.csv` exists and contains one row per included `record_id`.
- `label_summary.json` exists.
- `problem-definition.md` exists and cites source evidence.
- Every major claim in `problem-definition.md` cites representative `record_id` values.
- Risks and counter-evidence are included.

## Judgment Rules

- Treat chunks as processing units, not conclusion units.
- Make final claims only from merged row-level labels.
- Prefer direct user evidence over elegant categories.
- Use `needs_review=true` for ambiguous rows.
- Do not infer market size, revenue, or willingness to pay without evidence.
- Avoid jumping from pain point to feature before stating the problem clearly.
