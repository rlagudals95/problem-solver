# Pre-PRD PO Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the community pain point analysis skill from `problem-definition.md` to PRD-readiness outputs that support PO decision-making before development starts.

**Architecture:** Keep deterministic renderers in `skills/community-painpoint-analysis/scripts/`. Each renderer reads validated upstream files and writes one Korean Markdown output. Tests run the fixture CSV through the full chain so regressions are caught from source data to PRD-readiness.

**Tech Stack:** Python 3 standard library, CSV/JSON/Markdown files, `unittest`, Codex Skill markdown.

---

## File Structure

- Create: `skills/community-painpoint-analysis/scripts/render_opportunity_brief.py`
- Create: `skills/community-painpoint-analysis/scripts/render_product_direction.py`
- Create: `skills/community-painpoint-analysis/scripts/render_validation_plan.py`
- Create: `skills/community-painpoint-analysis/scripts/render_prd_readiness.py`
- Create: `tests/test_pre_prd_pipeline.py`
- Modify: `skills/community-painpoint-analysis/SKILL.md`
- Modify: `.gitignore` if generated analysis outputs need to remain untracked.

## Task 1: End-To-End Test

- [ ] Write `tests/test_pre_prd_pipeline.py` that runs fixture CSV through prepare, validate, merge, summarize, problem definition, opportunity brief, product direction, validation plan, and PRD readiness.
- [ ] Verify the new test fails because the new renderer scripts do not exist.

## Task 2: Deterministic Renderers

- [ ] Implement `render_opportunity_brief.py` with Korean sections for opportunity summary, target segment, evidence strength, business relevance, and risks.
- [ ] Implement `render_product_direction.py` with Korean sections for strategic direction, solution principles, non-goals, possible solution themes, and product bets.
- [ ] Implement `render_validation_plan.py` with Korean sections for risky assumptions, interview questions, experiments, success criteria, and stop criteria.
- [ ] Implement `render_prd_readiness.py` with Korean sections for readiness decision, required evidence checklist, remaining gaps, and PRD recommendation.

## Task 3: Documentation And Verification

- [ ] Update `SKILL.md` so the workflow ends at PRD-readiness before PRD writing.
- [ ] Run `python3 -m unittest discover -s tests -v`.
- [ ] Run `python3 scripts/install_skill.py`.
- [ ] Commit and push the completed change to `develop`.
