# Labeling Codebook Guide

Use this reference before writing `codebook.md` for an analysis run.

## Required Columns

The label CSV header must match these exact column names and order, with no extra, missing, or duplicate columns.

- `record_id`: Stable row-level ID from chunk CSV.
- `is_relevant`: `true` when the row contains meaningful user evidence for the topic, otherwise `false`.
- `irrelevant_reason`: Required when `is_relevant=false`.
- `user_context`: The concrete situation the user is in.
- `journey_stage`: Exploration, comparison, purchase decision, installation, active use, problem occurrence, cancellation, replacement, review, or a topic-specific equivalent.
- `jtbd`: Use `When ..., I want ..., so I can ...`.
- `primary_pain_point`: Main pain evidenced by the row.
- `secondary_pain_point`: Optional second pain.
- `sentiment`: `부정`, `중립`, `긍정`, or `혼합`.
- `severity`: `낮음`, `중간`, or `높음`.
- `segment_candidate`: Repeated user type suggested by the evidence.
- `evidence_quote`: Short quote or paraphrase grounded in title, body, or comments.
- `confidence`: `낮음`, `중간`, or `높음`.
- `needs_review`: `true` for ambiguous or conflicting rows.

## Irrelevant Reasons

- `promotional_or_deal`: Ad, affiliate link, coupon, or pure deal post.
- `news_or_investor`: News, stock, investor, or market commentary without user pain.
- `generic_chatter`: Casual mention without actionable user need.
- `non_consumer_context`: Vendor, operator, or non-user context.
- `insufficient_signal`: Too little content to interpret safely.

## Severity

- `높음`: Money loss, time loss, repeated stress, contract/cancellation risk, strong distrust, or intense negative emotion.
- `중간`: Meaningful friction that slows a decision or creates uncertainty.
- `낮음`: Mild preference, curiosity, or low-stakes inconvenience.

## Confidence

- `높음`: Direct first-person experience or multiple text fields support the same interpretation.
- `중간`: Evidence is plausible but partially inferred.
- `낮음`: Sparse, ambiguous, or mostly comment-derived evidence.

## Calibration Process

1. Sample 30-50 records across source files and query terms.
2. Draft the initial taxonomy from actual user language.
3. Define inclusion and exclusion rules.
4. Add examples for each major pain point.
5. Freeze the codebook before full chunk labeling unless the user approves recalibration.
