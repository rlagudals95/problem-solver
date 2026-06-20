---
name: community-painpoint-analysis
description: Use when analyzing large community-analyzer CSV exports to identify user pain points, label posts, prevent row omissions, synthesize JTBD problem definitions, and produce evidence-backed research outputs.
---

# Community Painpoint Analysis

Use this skill to convert one or more `community-analyzer` CSV exports into a traceable problem-definition package.

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

10. Read `references/problem-definition-template.md` and write `problem-definition.md` from `labeled_posts.csv`, `label_summary.json`, `source_manifest.json`, `codebook.md`, and `audit-report.md`.

## Quality Gates

- `source_manifest.json` exists.
- `codebook.md` exists.
- Validation passes with no missing included rows.
- Excluded rows have explicit `exclusion_reason`.
- `labeled_posts.csv` exists and contains one row per included `record_id`.
- `label_summary.json` exists.
- Every major claim in `problem-definition.md` cites representative `record_id` values.
- Risks and counter-evidence are included.

## Judgment Rules

- Treat chunks as processing units, not conclusion units.
- Make final claims only from merged row-level labels.
- Prefer direct user evidence over elegant categories.
- Use `needs_review=true` for ambiguous rows.
- Do not infer market size, revenue, or willingness to pay without evidence.
- Avoid jumping from pain point to feature before stating the problem clearly.
