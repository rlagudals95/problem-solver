# Community Painpoint Analysis Skill Design

Date: 2026-06-20
Status: Approved design draft
Owner: hyeongmin

## 1. Purpose

Build a Codex skill named `community-painpoint-analysis` that turns large CSV exports from `community-analyzer` into a traceable problem-definition package.

The skill exists for a full-stack developer who wants to become a business-focused problem solver: someone who can collect messy community data, find real user pain points, define the problem worth solving, and use that definition as the basis for product direction and business goals.

The first version focuses on analysis, not on a web service. It should make Codex reliable for repeated, large-volume qualitative research.

## 2. Input

The first version accepts CSV files produced by `/Users/hyeongmin/Desktop/workspace/community-analyzer`.

Expected source columns include the crawler fields already used by that project:

- `site`
- `post_id`
- `board_code`
- `board_name`
- `category_name`
- `title`
- `author`
- `posted_at`
- `url`
- `view_count`
- `like_count`
- `dislike_count`
- `comment_count`
- `matched_queries`
- `matched_search_urls`
- `search_pages`
- `search_excerpt`
- `body_text`
- `comments_text`
- `comments_json`
- `crawl_status`
- `crawl_error`

The skill may accept one or more CSV files in a single run. Multiple files are merged into one run dataset after schema validation.

## 3. Core Outputs

Each analysis run writes a folder under the user's workspace:

```text
analysis-runs/YYYY-MM-DD-topic/
  source_manifest.json
  codebook.md
  chunks/
  labels/
  labeled_posts.csv
  label_summary.json
  problem-definition.md
  audit-report.md
```

Required outputs:

- `source_manifest.json`: Processing ledger that records source files, row counts, stable IDs, dedupe decisions, chunk membership, inclusion/exclusion status, exclusion reasons, and coverage.
- `codebook.md`: Topic-specific label definitions and decision rules.
- `labeled_posts.csv`: One row per analyzed source record, including per-post labels and evidence.
- `label_summary.json`: Machine-readable aggregate summary used by Codex for final synthesis.
- `problem-definition.md`: Human-readable decision document.
- `audit-report.md`: Coverage, validation, and quality warnings.

## 4. Non-Goals

The first version does not:

- Crawl communities directly.
- Build a dashboard or web service.
- Decide final product features.
- Treat chunk summaries as final conclusions.
- Make unsupported market-size, revenue, or growth claims.
- Hide uncertainty when evidence is weak.

## 5. Recommended Approach

Use a skill plus helper scripts.

Codex should perform judgment-heavy tasks:

- Interpret the user's research topic.
- Calibrate the codebook.
- Label post-level evidence.
- Reconcile taxonomy drift.
- Write the final problem definition.
- Identify risks, counter-evidence, and validation questions.

Scripts should perform deterministic tasks:

- Read and normalize CSV files.
- Generate stable `record_id` values.
- Validate required columns.
- Detect duplicate candidates.
- Split records into chunks.
- Validate label coverage.
- Merge label fragments.
- Produce aggregate counts and evidence indexes.

This split protects against LLM context limits while still using Codex for the parts that require product judgment.

## 6. Reliability Methodology

Large datasets must use a `manifest-first` flow.

1. The preparation script reads all source rows before analysis starts.
2. Every source row receives a stable `record_id`.
3. The manifest records total source rows, excluded rows, exclusion reasons, duplicate candidates, chunk membership, and processing status.
4. Codex labels rows chunk by chunk, but each output row must keep its original `record_id`.
5. Validation scripts compare label outputs against the manifest before any final synthesis.
6. Missing rows, duplicate labels, invalid columns, and empty required labels block final report generation.
7. The final Markdown is created only after `labeled_posts.csv` covers the manifest.

Coverage means every source row must end in exactly one of two states:

- Included in `labeled_posts.csv` with one label row.
- Excluded in `source_manifest.json` with an explicit `exclusion_reason`.

This makes "no missing rows" a checkable property rather than a trust-based instruction.

## 7. Analysis Methodology

The skill uses five passes.

### Pass 1: Dataset Preparation

Run `prepare_dataset.py` to:

- Load one or more CSV files.
- Validate source schema.
- Normalize text fields.
- Create `record_id`.
- Detect exact and near duplicate candidates.
- Mark rows with unusable content or intentional exclusion reasons.
- Create chunk CSV files.
- Write `source_manifest.json`.

Stable `record_id` generation should prefer durable source identifiers. Use `site`, `post_id`, and canonical `url` when available, with source file path and source row index as a fallback to avoid collisions.

Chunk size should be configurable. A default range of 50-150 posts per chunk is appropriate, depending on post length.

### Pass 2: Codebook Calibration

Codex reviews a representative sample, usually 30-50 records, and writes `codebook.md`.

The codebook must define:

- Relevance criteria.
- Irrelevant reasons.
- Journey stages.
- Pain point taxonomy.
- Severity criteria.
- Sentiment criteria.
- Segment candidates.
- Confidence criteria.
- Examples and edge cases from the sample.

The codebook is allowed to evolve during early review, but once full chunk labeling starts it should remain stable unless the user explicitly approves recalibration.

### Pass 3: Chunk Labeling

Codex labels each chunk using the same codebook.

This pass must not produce final conclusions. It only creates row-level labels and evidence.

Required label columns:

- `record_id`
- `is_relevant`
- `irrelevant_reason`
- `user_context`
- `journey_stage`
- `jtbd`
- `primary_pain_point`
- `secondary_pain_point`
- `sentiment`
- `severity`
- `segment_candidate`
- `evidence_quote`
- `confidence`
- `needs_review`

Each labeled chunk is saved in `labels/`.

### Pass 4: Merge, Validate, And Reconcile

Run validation and merge scripts to:

- Confirm every included `record_id` has exactly one label row.
- Confirm every excluded source row has exactly one explicit exclusion reason.
- Confirm required columns exist.
- Confirm required fields are non-empty where applicable.
- Confirm irrelevant rows include `irrelevant_reason`.
- Confirm relevant rows include pain point, JTBD, evidence, severity, and confidence.
- Merge valid chunks into `labeled_posts.csv`.
- Detect taxonomy drift across chunks.

Taxonomy drift means similar labels appear under different names, such as "가격 부담", "비용 부담", and "요금 부담". Codex should reconcile these labels at the global level before writing the final report.

### Pass 5: Global Synthesis

Codex writes `problem-definition.md` using the merged `labeled_posts.csv` and `label_summary.json`, not using chunk-level summaries as final evidence.

The final synthesis must:

- Rank pain points by frequency, severity, sentiment, confidence, and business relevance.
- Identify target segments with repeated evidence.
- Convert the strongest opportunities into JTBD problem statements.
- Cite representative `record_id` values for key claims.
- Include counter-evidence and weak-evidence warnings.
- Suggest next validation questions and experiments.

## 8. Problem Definition Document

`problem-definition.md` should use this structure:

1. Executive Summary
2. Dataset Coverage
3. Top Pain Points
4. Target Segments
5. JTBD Problem Statements
6. Opportunity Prioritization
7. Recommended Problem Definition
8. Risks And Counter-Evidence
9. Next Validation Questions

Every important claim should include supporting `record_id` references. Strong claims should cite at least 3-5 representative records when enough evidence exists.

## 9. Labeling Codebook Rules

The codebook should prefer evidence over elegance.

Rules:

- Preserve raw user language during post-level labeling when possible.
- Normalize labels during taxonomy reconciliation, not during first reading.
- Use `needs_review=true` instead of forcing ambiguous judgments.
- Mark `confidence=높음` only when the user experience is concrete and directly evidenced.
- Mark `severity=높음` only for clear money loss, time loss, repeated friction, contract risk, cancellation/switching pain, strong distrust, or intense negative emotion.
- Treat promotional posts, news, investor chatter, and generic off-topic discussion as irrelevant.
- Avoid solution jumping in the problem-definition stage.

## 10. Helper Scripts

The skill should include these scripts.

### `prepare_dataset.py`

Inputs:

- Source CSV paths.
- Topic name.
- Output run directory.
- Optional chunk size.

Outputs:

- `source_manifest.json`
- `chunks/chunk-001.csv`, `chunks/chunk-002.csv`, and so on
- Initial `audit-report.md`

Responsibilities:

- Read CSV files.
- Validate schema.
- Generate stable IDs.
- Preserve source row metadata.
- Detect exact duplicate candidates.
- Record inclusion and exclusion status for every source row.
- Split into chunks.

### `validate_labels.py`

Inputs:

- `source_manifest.json`
- One or more label CSV files.

Outputs:

- Validation result to stdout.
- Updated `audit-report.md`.

Responsibilities:

- Check coverage.
- Check duplicates.
- Check required columns.
- Check empty required values.
- Block final synthesis if validation fails.

### `merge_labels.py`

Inputs:

- Validated label CSV files.
- `source_manifest.json`.

Outputs:

- `labeled_posts.csv`

Responsibilities:

- Merge chunks in manifest order.
- Preserve source metadata where useful.
- Fail if validation has not passed.

### `summarize_labels.py`

Inputs:

- `labeled_posts.csv`

Outputs:

- `label_summary.json`

Responsibilities:

- Aggregate pain points, journey stages, segments, sentiment, severity, and confidence.
- Extract top evidence rows per cluster.
- Flag low-confidence clusters.
- Prepare structured inputs for final Codex synthesis.

## 11. Quality Gates

The skill must not write a final problem definition until these gates pass:

- `source_manifest.json` exists.
- `codebook.md` exists.
- Every source `record_id` is accounted for as either labeled or explicitly excluded.
- No duplicate label rows exist for the same `record_id`.
- Required label columns exist.
- Relevant rows contain evidence quotes.
- The final report cites `record_id` values.
- `audit-report.md` records the coverage result.

## 12. Success Criteria

The first version is successful when:

- A user can point Codex at one or more `community-analyzer` CSV files.
- Codex can prepare chunks without losing source rows.
- Codex can produce a complete `labeled_posts.csv`.
- Scripts can prove no rows were missed or duplicated.
- Codex can synthesize a useful `problem-definition.md` from the merged labels.
- The final document is traceable back to concrete community posts.

## 13. Risks

### LLM label inconsistency

Risk: Codex may label similar posts differently across chunks.

Mitigation: Calibrate a codebook first, keep row-level labels, and reconcile taxonomy globally.

### Over-summarization

Risk: Chunk summaries may hide minority but important pain points.

Mitigation: Do not use chunk summaries as final evidence. Synthesize only from merged row-level labels.

### False precision

Risk: The report may sound more certain than the data supports.

Mitigation: Include confidence, `needs_review`, counter-evidence, and weak-evidence warnings.

### CSV scale

Risk: Very large CSV files may be slow to process manually.

Mitigation: Keep deterministic work in scripts and use chunk size controls.

## 14. Future Expansion

After this skill works reliably, the project can expand into:

- A crawler orchestration layer.
- A web-based review UI for `needs_review` rows.
- A reusable analysis database.
- Comparison across multiple markets or time windows.
- Problem-to-strategy generation, including MVP hypotheses, North Star metrics, and business goals.

Those expansions should happen after the CSV-to-problem-definition workflow is proven.
